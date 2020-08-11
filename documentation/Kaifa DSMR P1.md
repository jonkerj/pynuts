# Kaifa DSMR

This file describes how I got to read out my Kaifa MA 105 electricity/gas meter
using Nuts.

## Hardware

In essence, I crimped a cable, which had a six pin 0.1" female header ("FTDI")
on one side, and a RJ11 (technically 6P4C) connector on the other side. The
pinout:

FTDI   | RJ11
-------|------
1 GND  | 3 GND
2 CTS# |
3 VCC  | 2 RTS
4 TXD  |
5 RXD  | 5 TXD 
6 RTS# |

The other three pins of the DSMR P1 port (1, 4 and 6) are unconnnected, since
they are documented as `NC`. The `RTS` pin is tied to VCC, since we are always
ready to receive data, if connected.

## Settings

I chose to use a FTDI, because the RTS signal needs to be inverted. FTDI's (even
my $3 eBay clone) are able to do this in hardware, but you'll need to configure
them to do so. I did so using [this tool](http://rtr.ca/ft232r/). NB: I could
not get [ftx-prog](https://github.com/richardeoin/ftx-prog) to work.

```bash
 jorik@boron:~$ ./ft232r_prog --old-serial-number 42 --invert_rxd
```

Furthermore, you'll need to set the following parameters:
```INI
[subsystem:power]
class = SerialIECInterface
port = /dev/kaifa
baud = 115200
bits = 7
parity = N
stop = 1
timeout = 4
keys = energy_consumed_t1, energy_consumed_t2
```
Of course, you are free to use other keys as well (`energy_produced_*`, if you
have PV on your roof).

## External Links
* [DSMR P1 Companion Standard](http://www.netbeheernederland.nl/themas/hotspot/hotspot-documenten/?dossierid=11010056&title=Slimme%20meter&onderdeel=Documenten)
* [P1 Poort slimme meter hardware (Dutch)](http://domoticx.com/p1-poort-slimme-meter-hardware/)
