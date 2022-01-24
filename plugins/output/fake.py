from . import Base

class Fake(Base):
	pluginName = "fake"

	def init(self):
		pass

	def submitMeasurement(self, measurement):
		pass
