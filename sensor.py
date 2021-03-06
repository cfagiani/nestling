#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import logging

"""
Class used to encapsulate reading data from a DHT-11 temperature/humidity sensor. Users of this class should note that
it is possible that the sensor will not return a valid reading so any calls to get_data should check that the result 
is not (None,None).
"""

__author__ = "Christopher Fagiani"


class TempSensor(object):
    def __init__(self, channel):
        self.channel = channel

    def get_data(self, scale="f"):
        """
        Reads current temperature and humidity data and returns as a pair of (temp, humidity)
        :return: 
        """
        # use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        time.sleep(1)
        self.__send_command()
        # switch to input mode so we can read result
        GPIO.setup(self.channel, GPIO.IN)

        data = []
        j = 0

        while GPIO.input(self.channel) == GPIO.LOW:
            continue

        while GPIO.input(self.channel) == GPIO.HIGH:
            continue

        # read 5 bytes of data
        while j < 40:
            k = 0
            while GPIO.input(self.channel) == GPIO.LOW:
                continue

            while GPIO.input(self.channel) == GPIO.HIGH:
                k += 1
                if k > 100:
                    break

            if k < 8:
                data.append(0)
            else:
                data.append(1)

            j += 1

        GPIO.cleanup()
        humidity_byte = data[0:8]
        humidity_point_byte = data[8:16]
        temperature_byte = data[16:24]
        temperature_point_byte = data[24:32]
        check_byte = data[32:40]

        humidity = 0
        humidity_point = 0
        temperature = 0
        temperature_point = 0
        check = 0

        for i in range(8):
            humidity += humidity_byte[i] * 2 ** (7 - i)
            humidity_point += humidity_point_byte[i] * 2 ** (7 - i)
            temperature += temperature_byte[i] * 2 ** (7 - i)
            temperature_point += temperature_point_byte[i] * 2 ** (7 - i)
            check += check_byte[i] * 2 ** (7 - i)

        tmp = humidity + humidity_point + temperature + temperature_point

        if check == tmp:
            if scale == "f":
                temperature = (temperature * 1.8) + 32
            return temperature, humidity
        else:
            logging.debug("check bit error. read {temp}".format(temp=temperature))
            return None, None

    def __send_command(self):
        """
        Sends a command to the DHT-11 data pin triggering a reading.
        :return: 
        """
        GPIO.setup(self.channel, GPIO.OUT)
        GPIO.output(self.channel, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(self.channel, GPIO.HIGH)


def cleanup():
    GPIO.cleanup()
