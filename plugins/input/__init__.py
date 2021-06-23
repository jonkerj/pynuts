from .. import Base as Plugin

class Base(Plugin):
	def read(self):
		self.log.debug("read()")
		m = self.getMeasurement()
		self.log.debug(f"Read measurement: {m}")
		return m

	def getMeasurement(self):
		raise NotImplementedError

from .serialiec62056 import SerialIEC62056

__all__ = [
	Base,
	SerialIEC62056,
]
