import asyncio
import logging
import serial_asyncio

async def main():
	print('Creating reader/writer')
	reader, writer = await serial_asyncio.open_serial_connection(url='/dev/kamstrup', baudrate=300, bytesize=7, parity='E', stopbits=2, timeout=8)
	print(dir(reader))
	await asyncio.gather(request(reader, writer))
	
async def request(reader, writer):
	print('Requesting telegram')
	writer.write(b'/?!\r\n')
	print('Waiting 8 seconds')
	await asyncio.sleep(8)
	part = await reader.read(2048)
	print(f'Got a part: {part}')

if __name__ == '__main__':
	asyncio.run(main())
