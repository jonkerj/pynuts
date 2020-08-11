# GPIO Water meter

My water meter (Sensus 620) contains a little red/metal wheel that rotates every
liter consumed. Using a IR reflection meter TCRT5000 module from eBay (sold as
"obstacle avoidance module") I am able to keep track of this wheel.

## Mechanics

JHeyman has created an excellent
[3D printable model](https://github.com/jheyman/wirelesswatermeter), which fits
an eBay TCRT5000 module to a Sensus 620.

## Electronics

Since the TRCT5000 module operated on both 3.3V and 5V, it was just a matter of
connecting the module to the expansion header of my SBC (Orange Pi, but any will
do) by connecting VCC to 3.3V, GND to GND and DO to a GPIO pin.

## Settings
You will need to setup the GPIO pin outside of Nuts at this moment. I have
provided `setup_gpio_nuts.sh` as an example for this:
```bash
jorik@boron:~/nuts$ sudo sh ./setup_gpio_nuts.sh 6
```

The following code sets up Nuts to count edges (both directions) and increment a
counter with each half liter consumed:
```INI
[subsystem:water]
class = GPIOCounter
gpio = 6
keys = total
increment = 0.5
```
