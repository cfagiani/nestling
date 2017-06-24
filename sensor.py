#!/usr/bin/python

import RPi.GPIO as GPIO
import time


class TempSensor(object):
    def __init__(self, channel):
        self.channel = channel

    def get_data(self, scale="f"):
        """
        Reads current temperature and humidity data and returns as a pair of (temp, humidity)
        :return: 
        """
        GPIO.setmode(GPIO.BCM)
        time.sleep(1)
        GPIO.setup(self.channel, GPIO.OUT)
        GPIO.output(self.channel, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(self.channel, GPIO.HIGH)

        GPIO.setup(self.channel, GPIO.IN)

        data = []
        j = 0

        while GPIO.input(self.channel) == GPIO.LOW:
            continue

        while GPIO.input(self.channel) == GPIO.HIGH:
            continue

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
        humidity_bit = data[0:8]
        humidity_point_bit = data[8:16]
        temperature_bit = data[16:24]
        temperature_point_bit = data[24:32]
        check_bit = data[32:40]

        humidity = 0
        humidity_point = 0
        temperature = 0
        temperature_point = 0
        check = 0

        for i in range(8):
            humidity += humidity_bit[i] * 2 ** (7 - i)
            humidity_point += humidity_point_bit[i] * 2 ** (7 - i)
            temperature += temperature_bit[i] * 2 ** (7 - i)
            temperature_point += temperature_point_bit[i] * 2 ** (7 - i)
            check += check_bit[i] * 2 ** (7 - i)

        tmp = humidity + humidity_point + temperature + temperature_point

        if check == tmp:
            if scale == "f":
                temperature = (temperature * 1.8) + 32
            return temperature, humidity
        else:
            print "check bit error. read {temp}".format(temp=temperature)
            return None, None


def cleanup():
    GPIO.cleanup()
