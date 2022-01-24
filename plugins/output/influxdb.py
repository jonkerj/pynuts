import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from . import Base

class InfluxDB(Base):
	pluginName = "influxdb"

	def init(self):
		self.client = InfluxDBClient.from_env_properties()
		self.bucket = self.cfg.influxdb_bucket
		self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
		health = self.client.health()

		assert health.status == 'pass'
		self.log.info(f'Initialized InfluxDB connection to {self.client.url}, bucket {self.bucket} version {health.version}')

	def submitMeasurement(self, measurement):
		p = Point(measurement.name).time(measurement.timestamp)
		for k, v in measurement.fields.items():
			p = p.field(k, v)
		
		self.write_api.write(self.bucket, record=p)
