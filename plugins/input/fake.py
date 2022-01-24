import datetime
import time

import pytz

from . import Base
from main import Measurement

def now():
	return pytz.UTC.localize(datetime.datetime.utcnow())

class Fake(Base):
	pluginName = "fake"

	def init(self):
		self.count = 0

	def getMeasurement(self):
		self.count += 1

		return Measurement(self.name, now(), {"fake": self.count})

	def wait(self):
		time.sleep(1)
