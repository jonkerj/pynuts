import asyncio
import serial_asyncio
import iec62056
import datetime

async def telegrams(port):
	reader, _ = await serial_asyncio.open_serial_connection(url=port, baudrate=115200, bytesize=7, parity='N', stopbits=1)
	iec_parser = iec62056.parser.Parser()
	buf = bytes()
	while True:
		t0 = datetime.datetime.now()
		line = await reader.read(2048)
		t1 = datetime.datetime.now()

		# if receiving the line took more than 1 second, it is the start of a new telegram
		if (t1 - t0).total_seconds() > 1:
			print('last part received, assembling telegram')
			if len(buf) > 0:
				telegram = iec_parser.parse(buf.decode('ascii'))
				yield telegram
			else:
				print('it was empty, discarding')
			buf = line
		else:
			print('received a part')
			buf += line

async def main():
	async for telegram in telegrams('/dev/kaifa'):
		print(telegram)

if __name__ == '__main__':
	asyncio.run(main())
