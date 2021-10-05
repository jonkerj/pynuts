from .. import Base as Plugin

class Base(Plugin):
	def read(self):
		m = self.getMeasurement()
		if m:
			self.log.debug(f"Read measurement: {m}")
		return m

	def getMeasurement(self):
		raise NotImplementedError
	
	def wait(self):
		pass

from .serialiec62056 import SerialIEC62056
from .kamstrup import Multical66
from .counter import Counter

__all__ = [
	Base,
	SerialIEC62056,
	Multical66,
	Counter,
]
