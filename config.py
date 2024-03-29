# stdlib
import datetime
import inspect
import logging
import sys

# upstream
import environ
import pytz

# own
import plugins

def convLoglevel(s):
	levels = ['CRITICAL', 'FATAL', 'ERROR', 'WARNING', 'WARN', 'INFO', 'DEBUG']
	if not s in levels:
		raise ValueError(f'{s} is not a valid log level. Valid are {"".join(choices)}')
	return s

def convTags(s):
	tags = {}
	for ts in s.split(','):
		if ts != '':
			kv = ts.split('=', 1)
			if not len(kv)==2:
				raise ValueError(f'Supplied tags {s} are not in the format tag1=val1,tag2=val2')
			tags[kv[0]] = kv[1]
	return tags

def convPlugin(s, m):
	assert m in ['plugins.input', 'plugins.output']
	mod = sys.modules[m]
	classes = [clsObj for clsName, clsObj in inspect.getmembers(mod, predicate=inspect.isclass) if clsObj.pluginName == s]
	if len(classes) == 1:
		return classes[0]
	elif len(classes) > 1:
		raise ValueError(f'More than one class with name {s} found in {m}')
	else:
		raise ValueError(f'No class with name {s} found in {m}')

def convInputPlugin(s):
	return convPlugin(s, 'plugins.input')

def convOutputPlugin(s):
	return convPlugin(s, 'plugins.output')

@environ.config(prefix='PYNUTS')
class PyNuts:
	input_cls = environ.var("serialiec62056", converter=convInputPlugin)
	input_name = environ.var("power")
	input_tz = environ.var("Europe/Amsterdam", converter=pytz.timezone)
	output_cls = environ.var("influxdb", converter=convOutputPlugin)
	output_name = environ.var("influxdb")
	loglevel = environ.var("INFO", converter=convLoglevel)
	influxdb_bucket = environ.var('pynuts', name='INFLUXDB_V2_BUCKET')  # bit awkward, but if we put it under sub-config-class we cannot get this nice envvar

	@environ.config
	class Serial:
		port = environ.var('')
		baudrate = environ.var(115200, converter=int)
		bytesize = environ.var(7, converter=int)
		parity = environ.var('N')
		stopbits = environ.var(1, converter=int)
		timeout = environ.var(2, converter=float)
		vid = environ.var('')
		pid = environ.var('')
		serial = environ.var('')
	
	serial = environ.group(Serial)

	@environ.config
	class Counter:
		filename = environ.var('/sys/class/gpio/gpio71/value') # On Pine A64 this is PC7 / pin 11 on Pi2 header
		increase = environ.var(0.5, converter=float)
		key = environ.var('volume')
		interval = environ.var(0.1)
	
	counter = environ.group(Counter)
	