from .. import Base as Plugin

class Base(Plugin):
	def write(self, measurement):
		self.log.debug("write()")
		self.submitMeasurement(measurement)
	
	def submitMeasurement(self, measurement):
		raise NotImplementedError

from .influxdb import InfluxDB

__all__ = [
	Base,
	InfluxDB,
]
