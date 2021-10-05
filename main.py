import logging
import sys
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
	log = attr.ib()
	input = attr.ib(init=False)
	output = attr.ib(init=False)

	def init(self):
		self.input = self.cfg.input_cls(self.cfg.input_name, self.log, self.cfg)
		self.output = self.cfg.output_cls(self.cfg.output_name, self.log, self.cfg)

		self.log.info("Initialized")

	def run(self):
		while True:
			m = self.input.read()
			if m:
				self.output.write(m)
			self.input.wait()

if __name__ == '__main__':
	cfg = config.PyNuts.from_environ()

	ch = logging.StreamHandler(sys.stderr)
	ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)8s:%(name)s: %(message)s"))
	log = logging.getLogger('pynuts')
	log.addHandler(ch)
	log.setLevel(cfg.loglevel)
		
	p = PyNuts(cfg, log)
	p.init()
	p.run()
