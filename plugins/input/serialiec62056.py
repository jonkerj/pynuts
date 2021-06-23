import datetime
import time

import attr
import serial
import serial.tools.list_ports
import iec62056

from . import Base
from main import Measurement

def now():
	zone = datetime.datetime.now(datetime.timezone.utc).astimezone()
	return datetime.datetime.now().replace(tzinfo=zone.tzinfo)

class SerialIEC62056(Base):
	pluginName = "serialiec62056"

	def __findPort(self):
		if self.cfg.serial.port and self.cfg.serial.port != '':
			return self.cfg.serial.port
		
		# OK, no port specified, return the first port that passes all tests
		# if you don't filter based on VID/PID/serial, all ports will match
		filtermap = [
			('vid', lambda x: int(x, 16), 'vid', int),
			('pid', lambda x: int(x, 16), 'pid', int),
			('serial', lambda x: x.lower(), 'serial_number', lambda x: x.lower()),
		]
		for port in serial.tools.list_ports.comports():
			self.log.debug(f'Considering {port.device}')
			match = True # is matches until we show otherwise
			for cfgKey, cfgTrans, devKey, devTrans in filtermap:
				cfgVal = getattr(self.cfg.serial, cfgKey)
				devVal = getattr(port, devKey)
				self.log.debug(f'Looking for match {cfgKey}={cfgVal}')
				if cfgVal != '':
					if devVal is None:
						self.log.debug('{port.device} has no {cfgKey}')
						match = False
					
					cfgVal = cfgTrans(cfgVal)
					devVal = devTrans(devVal)

					if cfgVal != devVal:
						self.log.debug(f'{cfgKey} mismatch ({cfgVal}!={devVal}) for {port.device}')
						match = False

			if match:
				self.log.info(f'{port.device} was selected')
				return port.device
		raise RuntimeError('Could not find a proper port')
				

	def init(self):
		self.parser = iec62056.parser.Parser()
		self.log.debug(f"Opening serial port with settings {self.cfg.serial}")
		self.serial = serial.Serial(
			port=self.__findPort(),
			baudrate=self.cfg.serial.baudrate,
			bytesize=self.cfg.serial.bytesize,
			parity=self.cfg.serial.parity,
			stopbits=self.cfg.serial.stopbits,
			timeout=self.cfg.serial.timeout,
		)
	
	def __readFromPort(self):
		while self.serial.in_waiting == 0:
			# to soften the busy wait, doze a little off
			time.sleep(0.1)
		msg = b''
		while True:
			b = self.serial.read(1)
			if len(b) > 0:
				msg += b
			else:
				break
		return msg
	
	def __readFake(self):
		time.sleep(2)
		return iec62056.samples.KAIFA_MA105
	
	def __processDatagram(self, datagram):
		telegram = self.parser.parse(datagram.decode('ascii'))
		fields = {}
		t =  now()
		units = {
			None: lambda x: x,
			'kWh': lambda x: x * 3.6e6,
			'A': lambda x: x,
			'V': lambda x: x,
			'kW': lambda x: x * 1e3,
			'm3': lambda x: x * 1e3,
			'W': lambda x: x,
			's': lambda x: x,
		}
		for k in telegram.keys():
			v = telegram[k]
			if isinstance(v, iec62056.objects.Register):
				if isinstance(v.value, (int, float)):
					if v.unit not in units:
						raise NotImplementedError(f'No transformation function for unit {v.unit} yet')
					transformed = units[v.unit](v.value)

					if v.timestamp is None:
						fields[k] = transformed
					else:
						self.log.debug('Found a sub-measurement. This is not supported yet')
				if isinstance(v.value, datetime.datetime):
					t = v.value
		return Measurement(self.name, t, fields)

	def getMeasurement(self):
		while True:
			datagram = self.__readFromPort()
			measurement = self.__processDatagram(datagram)
			return measurement
