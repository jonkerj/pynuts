import datetime
import time

import attr
import pytz

from . import Base
from main import Measurement

def now():
	return pytz.UTC.localize(datetime.datetime.utcnow())

def readfile(fn):
	with open(fn, 'rb') as f:
		v = f.read().strip()
	return v

class Counter(Base):
	pluginName = "counter"

	def init(self):
		self.count = 0
		self.last = readfile(self.cfg.counter.filename)
		self.log.info(f'Watching file {self.cfg.counter.filename} for changes')

	def getMeasurement(self):
		v = readfile(self.cfg.counter.filename)
		if self.last is None or v != self.last:
			self.log.debug(f'File changed from {self.last} to {v}')
			self.last = v
			self.count += self.cfg.counter.increase

			return Measurement(self.name, now(), {self.cfg.counter.key: self.count})

	def wait(self):
		time.sleep(self.cfg.counter.interval)
