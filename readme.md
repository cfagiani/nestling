Nestling
==========

A simple utility that automatically adjusts the target temperature on a Nest thermostat using readings
from a DHT-11 sensor connected to a Raspberry Pi via its GPIO ports. This script uses a configuration file (config.ini)
to drive its behavior. Prior to first use, you must obtain a key/token from the Nest Developers site since it uses
 the Nest API directly and not a third-party integration like IFTTT.

_Prerequsites_
* Python 3.x
* requests python library
* Raspbery Pi
* DHT-11 temperature/humidity sensor


Setup
* install gpio on raspberry pi (if needed; included in Raspbian distribution)
   - sudo apt-get install python-rpi.gpio
* register for an api account on the Nest website
* enter client id and client secret in the config.ini file
* click auth url, accept the permissions and copy the PIN into the config.ini file as the auth_code
* wire your DHT-11 to the raspberry pi GPIO pins
* enter the data channel number in the config.ini file


NOTE: if you delete the cached token.json file you will need to re-generate a PIN 

**TODO**
* wiring diagram
* tests