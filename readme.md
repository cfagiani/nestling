Nestling
==========

This is a simple Python application that can serve as a remote temperature sensor for a Nest thermostat. 

_Prerequsites_
* Python 2.7.x
* requests python library
* Raspbery Pi with GPIO installed


Setup
* install gpio on raspberry pi (if needed; included in Raspbian distribution)
   - sudo apt-get install python-rpi.gpio
* register for an api account on the Nest website
* enter client id and client secret in the config.ini file
* click auth url, accept the permissions and copy the PIN into the config.ini file as the auth_code
* wire your thermistor to the raspberry pi GPIO pins
* enter the data channel number in the config.ini file


NOTE: if you delete the cached token.json file you will need to re-generate a PIN 

**TODO**
* replace print calls with logging
* cleanup sensor module
* wiring diagram
