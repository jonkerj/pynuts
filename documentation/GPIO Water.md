# GPIO Water meter

**This plugin is currently not working**

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
