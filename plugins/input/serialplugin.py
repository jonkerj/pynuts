import serial
import serial.tools.list_ports

from . import Base

class Serial(Base):
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
						self.log.debug(f'{port.device} has no {cfgKey} property. Skipping')
						match = False
						continue
					
					cfgVal = cfgTrans(cfgVal)
					devVal = devTrans(devVal)

					if cfgVal != devVal:
						self.log.debug(f'{cfgKey} mismatch ({cfgVal}!={devVal}) for {port.device}')
						match = False

			if match:
				self.log.info(f'{port.device} was selected')
				return port.device
		raise RuntimeError('Could not find a proper port')
	
	def openPort(self):
		self.log.debug(f"Opening serial port with settings {self.cfg.serial}")
		port = self.__findPort()
		self.serial = serial.Serial(
			port=port,
			baudrate=self.cfg.serial.baudrate,
			bytesize=self.cfg.serial.bytesize,
			parity=self.cfg.serial.parity,
			stopbits=self.cfg.serial.stopbits,
			timeout=self.cfg.serial.timeout,
		)
