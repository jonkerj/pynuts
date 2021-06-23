import logging
import attr
import config

@attr.s
class Measurement:
	name = attr.ib()
	timestamp = attr.ib()
	fields = attr.ib()

@attr.s
class PyNuts:
	cfg = attr.ib()
	log = attr.ib(init=False)
	input = attr.ib(init=False)
	output = attr.ib(init=False)

	def init(self):
		ch = logging.StreamHandler()
		ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)8s:%(name)s: %(message)s"))
		self.log = logging.getLogger('pynuts')
		self.log.addHandler(ch)
		self.log.setLevel(self.cfg.loglevel)
		
		self.input = self.cfg.input_cls(self.cfg.input_name, self.log, self.cfg)
		self.output = self.cfg.output_cls(self.cfg.output_name, self.log, self.cfg)

		self.log.info("Initialized")

	def run(self):
		while True:
			m = self.input.read()
			self.output.write(m)
			self.input.wait()

if __name__ == '__main__':
	p = PyNuts(config.PyNuts.from_environ())
	p.init()
	p.run()
