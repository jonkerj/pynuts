import time

import influxdb

from . import Base

class InfluxDB(Base):
	pluginName = "influxdb"

	def init(self):
		self.log.debug(f'Connection parameters: {self.cfg.influxdb}')
		self.client = influxdb.InfluxDBClient(
			host=self.cfg.influxdb.host,
			port=self.cfg.influxdb.port,
			ssl=self.cfg.influxdb.ssl,
			verify_ssl=self.cfg.influxdb.verify_ssl,
			database=self.cfg.influxdb.database,
			username=self.cfg.influxdb.username,
			password=self.cfg.influxdb.password,
		)
		version = self.client.ping()
		self.log.info(f'Initialized InfluxDB connection to {self.cfg.influxdb.host}:{self.cfg.influxdb.port}, version {version}')

	def submitMeasurement(self, measurement):
		res = self.client.write_points(tags=self.cfg.influxdb.tags, points=[{
			'measurement': measurement.name,
			'time': measurement.timestamp,
			'fields': measurement.fields,
		}])
		if not res:
			raise RuntimeError('Write to InfluxDB returned False')
