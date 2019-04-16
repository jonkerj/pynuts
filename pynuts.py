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
			telegram = self.iec_parser.parse(iec62056.samples.KAIFA_MA105.decode('ascii'))
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
