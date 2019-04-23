import asyncio
import logging
import serial_asyncio

async def main():
	print('Creating reader/writer')
	reader, writer = await serial_asyncio.open_serial_connection(url='/dev/kamstrup', baudrate=300, bytesize=7, parity='E', stopbits=2)
	data = await kamstrup66c(reader, writer)
	print(data)

# the correct formula is:
# 0) set settings to 300 7e2
# 1) send /#1\r\n
# 2) wait 1s (while flushing buffer?)
# 3) set speed to 1200 baud
# 4) receive up to 87 characters
# thanks you, https://github.com/RuntimeError123/hass-mc66c/

async def kamstrup66c(reader, writer):
	print('Requesting register 1')
	writer.write(b'/#1\r\n')
	print('Waiting')
	await asyncio.sleep(1)
	print('Setting baud to 1200')
	writer.transport.serial.baudrate = 1200
	print('Waiting')
	await asyncio.sleep(9)
	data = await reader.read(87)
	print('Setting baud to 300')
	writer.transport.serial.baudrate = 300
	data = data[5:].decode('ascii').split(' ')
	return {
		'energy': float(data[0])/100,  #GJ
		'volume': float(data[1])/100,  #m3
		'hours': int(data[2]),         #h
		't_in': float(data[3])/100,    #C
		't_out': float(data[4])/100,   #C
	}

if __name__ == '__main__':
	asyncio.run(main())
