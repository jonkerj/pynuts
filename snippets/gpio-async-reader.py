#!/usr/bin/env python3

import asyncio

# I would love to do this using select.epoll(), but I do not know of a way to
# combine this in a readable way with asyncio. So we poll 'speed' x per second

async def main(gpio, speed):
	with open(f'/sys/class/gpio/gpio{gpio}/value', 'rb') as f:
		last = None
		while True:
			v = f.read()
			f.seek(0)

			if last is not None and v != last:
				print(f'GPIO changed from {last} to {v}')
			last = v
			await asyncio.sleep(1.0/speed)

if __name__ == '__main__':
	asyncio.run(main(6, 4))
