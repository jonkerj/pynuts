#!/usr/bin/env python3

import asyncio
import logging
import sys
import datetime
import iec62056
import yaml
import serial_asyncio

logging.basicConfig(
	format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
	level=logging.DEBUG,
	datefmt="%H:%M:%S",
	stream=sys.stderr,
)
logger = logging.getLogger("pynuts")
#logging.getLogger("chardet.charsetprober").disabled = True

class Measurement(object):
	def __init__(self, timestamp, fields):
		self.timestamp = timestamp
		self.fields = fields

class QueueManipulator(object):
	def __init__(self, q : asyncio.Queue, config : dict) -> None:
		self.q = q
		self.config = config
		self.logger = logging.getLogger(f'pynuts.{self.config["name"]}')
		self.logger.info(f'Initialized as a {self.__class__.__name__}')
	
class MeasurementProducer(QueueManipulator):
	pass

class MeasurementConsumer(QueueManipulator):
	pass

class Serial62056Receiver(MeasurementProducer):
	async def run(self) -> None:
		iec_parser = iec62056.parser.Parser()
		while True:
			if 'request' in self.config:
				command = self.config["request"]["command"].encode('ascii')
				self.logger.debug(f'Requesting telegram by saying {command}')
				if 'delay' in self.config['request']:
					self.logger.debug(f'Delaying {self.config["request"]["delay"]}s')
					await asyncio.sleep(self.config["request"]["delay"])
			# mock Kaifa MA-105
			telegram = iec_parser.parse(iec62056.samples.KAIFA_MA105.decode('ascii'))
			fields = {}
			t =  datetime.datetime.now()
			for k in telegram.keys():
				v = telegram[k]
				if isinstance(v, iec62056.objects.Register):
					if type(v.value) in [int, float]:
						if v.timestamp is None:
							fields[k] = v.value
						else:
							sub = Measurement(v.timestamp, {k: v.value})
							self.logger.debug('Queueing sub-measurement (gas?)')
							await self.q.put(sub)
					if type(v.value) in [datetime.datetime]:
						t = v.value
			self.logger.debug('Queueing measurement')
			await self.q.put(Measurement(t, fields))
			self.logger.debug('Sleeping 5 seconds')
			await asyncio.sleep(5)

class Multical66Receiver(MeasurementProducer):
	# the correct formula is:
	# 0) set settings to 300 7e2
	# 1) send /#1\r\n
	# 2) wait 1s (while flushing buffer?)
	# 3) set speed to 1200 baud
	# 4) receive up to 87 characters
	# thank you, https://github.com/RuntimeError123/hass-mc66c/
	async def run(self) -> None:
		port = self.config['port']
		self.logger.debug(f'Creating serial reader/writer for {port} (300 7e2)')
		reader, writer = await serial_asyncio.open_serial_connection(url=port, baudrate=300, bytesize=7, parity='E', stopbits=2)
		while True:
			t =  datetime.datetime.now()
			self.logger.debug('Requesting register 1')
			# baudrate is not exposed in serial_async, but can be accessed through (only) the writer
			writer.transport.serial.baudrate = 300
			writer.write(b'/#1\r\n')
			await asyncio.sleep(1)
			self.logger.debug('Waiting for answer')
			writer.transport.serial.baudrate = 1200
			await asyncio.sleep(9)
			raw = await reader.read(87)
			writer.transport.serial.baudrate = 300
			data = raw[5:].decode('ascii').split(' ')
			fields = {
				'energy': float(data[0])/100,  #GJ
				'volume': float(data[1])/100,  #m3
				't_in': float(data[3])/100,    #C
				't_out': float(data[4])/100,   #C
			}
			self.logger.debug('Queueing measurement')
			await self.q.put(Measurement(t, fields))
			duration = (datetime.datetime.now() - t).total_seconds()
			self.logger.debug(f'Fetching took {duration}s, sleeping {60 - duration}s')
			await asyncio.sleep(60 - duration)

class InfluxDBSubmitter(MeasurementConsumer):
	async def run(self) -> None:
		while True:
			m = await self.q.get()
			self.logger.debug(f'Received measurement from queue (t={m.timestamp.strftime("%c")}, {len(m.fields.keys())} keys). Submitting')
			await asyncio.sleep(0.5)
			self.q.task_done()

systems = {
	'serial_iec': Serial62056Receiver,
	'multical66': Multical66Receiver,
	'influxdb': InfluxDBSubmitter,
}

async def main(config: dict) -> None:
	q = asyncio.Queue()
	subsystems = []
	assert 'subsystems' in config, 'Config should contain "subsystems" key'
	assert isinstance(config['subsystems'], list), 'subsystems should be a list'
	for subsys in config['subsystems']:
		if subsys['system'] not in systems:
			raise NotImplementedError(f'Subsystem {subsys["name"]} is not implemented')
		klass = systems[subsys['system']]
		subsystems.append(klass(q, subsys))
	tasks = map(asyncio.create_task, [s.run() for s in subsystems])
	await asyncio.gather(*tasks)
	await q.join()

if __name__ == '__main__':
	assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
	with open('config.yaml', 'r') as fh:
		config = yaml.load(fh, Loader=yaml.SafeLoader)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main(config))
	loop.close()
