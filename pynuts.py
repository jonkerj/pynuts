#!/usr/bin/env python3

import asyncio
import logging
import sys
import datetime
import iec62056
import influxdb
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

def now():
	zone = datetime.datetime.now(datetime.timezone.utc).astimezone()
	return datetime.datetime.now().replace(tzinfo=zone.tzinfo)

class Measurement(object):
	def __init__(self, name, timestamp, fields):
		self.name = name
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
	async def request(self):
		if 'request' in self.config:
			command = self.config["request"]["command"].encode('ascii')
			self.logger.debug(f'Requesting telegram by saying {command}')
			if 'delay' in self.config['request']:
				self.logger.debug(f'Delaying {self.config["request"]["delay"]}s')
				await asyncio.sleep(self.config["request"]["delay"])
	
	async def process_telegram(self, telegram):
		fields = {}
		t =  now()
		units = {
			None: lambda x: x,
			'kWh': lambda x: x * 3.6e6,
			'A': lambda x: x,
			'V': lambda x: x,
			'kW': lambda x: x * 1e3,
			'm3': lambda x: x * 1e3,
			'W': lambda x: x,
			's': lambda x: x,
		}
		for k in telegram.keys():
			v = telegram[k]
			if isinstance(v, iec62056.objects.Register):
				if type(v.value) in [int, float]:
					if v.unit not in units:
						raise NotImplementedError(f'No transformation function for unit {v.unit} yet')
					transformed = units[v.unit](v.value)

					if v.timestamp is None:
						fields[k] = transformed
					else:
						sub = Measurement(self.config['name'], v.timestamp, {k: transformed})
						self.logger.debug('Queueing sub-measurement (gas?)')
						await self.q.put(sub)
				if type(v.value) in [datetime.datetime]:
					t = v.value
		self.logger.debug('Queueing measurement')
		await self.q.put(Measurement(self.config['name'], t, fields))
		
	async def run(self) -> None:
		port = self.config['port']
		self.logger.debug(f'Creating serial reader/writer for {port} (115200 7n1)')
		reader, _ = await serial_asyncio.open_serial_connection(url=port, baudrate=115200, bytesize=7, parity='N', stopbits=1)
		iec_parser = iec62056.parser.Parser()
		buf = bytes()
		await self.request()
		while True:
			t0 = now()
			line = await reader.read(2048)
			t1 = now()

			# if receiving the line took more than 1 second, it is the start of a new telegram
			if (t1 - t0).total_seconds() > 1:
				if len(buf) > 0:
					self.logger.debug('Assembling telegram')
					try:
						telegram = iec_parser.parse(buf.decode('ascii'))
					except Exception: # TODO catch more specific exceptions
						pass
					else:
						await self.process_telegram(telegram)
				buf = line
				await self.request()
			else:
				buf += line

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
		interval = int(self.config['interval'])
		self.logger.info(f'Polling in {interval}s intervals')
		while True:
			t =  now()
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
			try:
				fields = {
					'energy': float(data[0]) * 1.0e7,
					'volume': float(data[1]) * 1.0e1,
					't_in': float(data[3])/100,
					't_out': float(data[4])/100,
				}
			except ValueError:
				continue
			else:
				self.logger.debug('Queueing measurement')
				await self.q.put(Measurement(self.config['name'], now(), fields))
			duration = (now() - t).total_seconds()
			self.logger.debug(f'Fetching took {duration:.3}s, sleeping {interval - duration:.5}s')
			await asyncio.sleep(interval - duration)

class GPIOCounter(MeasurementProducer):
	async def run(self) -> None:
		gpio = self.config['gpio']
		with open(f'/sys/class/gpio/gpio{gpio}/value', 'rb') as f:
			last = None
			count = 0.0
			increment = self.config['increment']
			while True:
				v = int(f.read())
				f.seek(0)

				if last is not None and v != last:
					self.logger.debug(f'GPIO changed from {last} to {v}')
					count += increment
					await self.q.put(Measurement(self.config['name'], now(), {self.config['key']: count}))
				last = v
				await asyncio.sleep(self.config['resolution'])

class InfluxDBSubmitter(MeasurementConsumer):
	async def run(self) -> None:
		self.logger.debug('Initializing InfluxDB client')
		idb = influxdb.InfluxDBClient(**self.config['connection'])
		self.logger.info(f'Connected to InfluxDB version {idb.ping()}')
		while True:
			m = await self.q.get()
			self.logger.debug(f'Submitting measurement from {m.name}')
			# TODO make influxdb aio too
			idb.write_points(tags=self.config['tags'], points=[{
				'measurement': m.name,
				'time': m.timestamp,
				'fields': m.fields,
			}])
			self.q.task_done()

systems = {
	'serial_iec': Serial62056Receiver,
	'multical66': Multical66Receiver,
	'influxdb': InfluxDBSubmitter,
	'gpiocounter': GPIOCounter,
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
