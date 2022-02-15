import datetime
import time

import attr
import pytz

from .serialplugin import Serial
from main import Measurement

def now():
	return pytz.UTC.localize(datetime.datetime.utcnow())

class Multical66(Serial):
	pluginName = "multical66"

	def init(self):
		self.openPort()
	
	def __readFromPort(self):
		# https://wiki.volkszaehler.org/hardware/channels/meters/warming/kamstrup_multical_401
		# https://github.com/RuntimeError123/hass-mc66c/
		self.log.debug('Requesting register 1')
		self.serial.baudrate = 300
		self.serial.write(b'/#1')
		self.serial.flush()
		self.log.debug('Waiting for answer')
		time.sleep(1)
		self.serial.baudrate = 1200
		self.serial.flushInput()
		datagram = self.serial.read(87)
		self.serial.baudrate = 300
		return datagram
	
	def __processDatagram(self, datagram):
		data = datagram.decode('ascii').split(' ')
		if len(data) < 10:
			self.log.warn(f'Corrupt reply, less than 10 fields returned')
			return None
		for d in data[:10]:
			if len(d) != 7:
				self.log.warn(f'Corrupt reply, field {d} has invalid length')
				return None
		try:
			fields = {
				'energy': float(data[0]) * 1.0e7,
				'volume': float(data[1]) * 1.0e1,
				't_in': float(data[3])/100,
				't_out': float(data[4])/100,
			}
		except ValueError:
			return None
		return Measurement(self.name, now(), fields)

	def getMeasurement(self):
		self.last = time.time()
		d = self.__readFromPort()
		self.log.debug(f'Datagram: {d}')
		m = self.__processDatagram(d)
		return m
	
	def wait(self):
		nap = 1800 - (time.time() - self.last)
		self.log.debug(f'Sleeping for {nap:.1f} seconds')
		time.sleep(nap)
