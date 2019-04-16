#!/usr/bin/env python3

import asyncio
import logging
import sys
import datetime
import iec62056

logging.basicConfig(
	format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
	level=logging.DEBUG,
	datefmt="%H:%M:%S",
	stream=sys.stderr,
)
#logger = logging.getLogger("pynuts")
#logging.getLogger("chardet.charsetprober").disabled = True

class Measurement(object):
	def __init__(self, timestamp, fields):
		self.timestamp = timestamp
		self.fields = fields

class QueueManipulator(object):
	def __init__(self, q : asyncio.Queue) -> None:
		self.q = q
		self.logger = logging.getLogger(self.__class__.__name__)

class MeasurementProducer(QueueManipulator):
	pass

class MeasurementConsumer(QueueManipulator):
	pass

class Serial62056Receiver(MeasurementProducer):
	def __init__(self, q : asyncio.Queue) -> None:
		super().__init__(q)
		self.iec_parser = iec62056.parser.Parser()

	async def run(self) -> None:
		while True:
			# mock Kaifa MA-105
			dummy = (
				b'/KFM5KAIFA-METER\r\n\r\n'
				b'1-3:0.2.8(42)\r\n'
				b'0-0:1.0.0(161113205757W)\r\n'
				b'0-0:96.1.1(3960221976967177082151037881335713)\r\n'
				b'1-0:1.8.1(001581.123*kWh)\r\n'
				b'1-0:1.8.2(001435.706*kWh)\r\n'
				b'1-0:2.8.1(000000.000*kWh)\r\n'
				b'1-0:2.8.2(000000.000*kWh)\r\n'
				b'0-0:96.14.0(0002)\r\n'
				b'1-0:1.7.0(02.027*kW)\r\n'
				b'1-0:2.7.0(00.000*kW)\r\n'
				b'0-0:96.7.21(00015)\r\n'
				b'0-0:96.7.9(00007)\r\n'
				b'1-0:99.97.0(3)(0-0:96.7.19)(000104180320W)(0000237126*s)(000101000001W)(2147583646*s)(000102000003W)(2317482647*s)\r\n'
				b'1-0:32.32.0(00000)\r\n'
				b'1-0:52.32.0(00000)\r\n'
				b'1-0:72.32.0(00000)\r\n'
				b'1-0:32.36.0(00000)\r\n'
				b'1-0:52.36.0(00000)\r\n'
				b'1-0:72.36.0(00000)\r\n'
				b'0-0:96.13.1()\r\n'
				b'0-0:96.13.0()\r\n'
				b'1-0:31.7.0(000*A)\r\n'
				b'1-0:51.7.0(006*A)\r\n'
				b'1-0:71.7.0(002*A)\r\n'
				b'1-0:21.7.0(00.170*kW)\r\n'
				b'1-0:22.7.0(00.000*kW)\r\n'
				b'1-0:41.7.0(01.247*kW)\r\n'
				b'1-0:42.7.0(00.000*kW)\r\n'
				b'1-0:61.7.0(00.209*kW)\r\n'
				b'1-0:62.7.0(00.000*kW)\r\n'
				b'0-1:24.1.0(003)\r\n'
				b'0-1:96.1.0(4819243993373755377509728609491464)\r\n'
				b'0-1:24.2.1(161129200000W)(00981.443*m3)\r\n'
				b'!6796\r\n'
			)
			telegram = self.iec_parser.parse(dummy.decode('ascii'))
			fields = {}
			t =  datetime.datetime.now()
			for k in telegram.keys():
				v = telegram[k]
				if isinstance(v, iec62056.objects.Register):
					if type(v.value) in [int, float]:
						fields[k] = v.value
					if type(v.value) in [datetime.datetime]:
						t = v.value
			self.logger.debug('Queueing measurement')
			await self.q.put(Measurement(t, fields))
			self.logger.debug('Sleeping 5 seconds')
			await asyncio.sleep(5)

class InfluxDBSubmitter(MeasurementConsumer):
	async def run(self) -> None:
		while True:
			m = await self.q.get()
			self.logger.debug(f'Received measurement from queue (t={m.timestamp.strftime("%c")}, {len(m.fields.keys())} keys). Submitting')
			await asyncio.sleep(0.5)
			self.q.task_done()

async def main() -> None:
	q = asyncio.Queue()
	subsystems = [Serial62056Receiver(q), InfluxDBSubmitter(q)]
	tasks = map(asyncio.create_task, [s.run() for s in subsystems])
	await asyncio.gather(*tasks)
	await q.join()

if __name__ == '__main__':
	assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
	loop.close()
