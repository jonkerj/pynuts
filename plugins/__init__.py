import attr

@attr.s
class Base:
	name = attr.ib()
	parentLog = attr.ib()
	cfg = attr.ib()
	pluginName = "UNDEFINED"

	def __attrs_post_init__(self):
		self.log = self.parentLog.getChild(self.name)
		self.init()
		self.log.info("Initialized")
	
	def init(self):
		pass

from . import input
from . import output
