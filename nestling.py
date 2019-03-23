#!/usr/bin/env python3

import configparser
import logging
import sys
import time

from prometheus_client import start_http_server, Gauge

import nest
import sensor

"""
nestling.py is a simple utility that automatically adjusts the target temperature on a Nest thermostat using readings
from a DHT-11 sensor connected to a Raspberry Pi via its GPIO ports. This script uses a configuration file (config.ini)
to drive its behavior. Prior to first use, you must obtain a key/token from the Nest Developers site.
"""
__author__ = "Christopher Fagiani"

CONF_FILE = "config.ini"
INTERVAL_SEC = 60
NEST_REFRESH_ITER = 5  # only refresh the nest api every 5 minutes
MAX_ALLOWED_DELTA = 3  # don't change things by more than 3 degrees


def validate_config(config):
    """
    Validates that the config object located contains all the required values.
    :param config: 
    :return: 
    """
    if config is None:
        raise Exception("config.ini must be supplied")
    required_keys = [("nestapi", "clientid"), ("nestapi", "clientsecret"), ("nestapi", "pincode"),
                     ("wiring", "datachannel")]
    for key in required_keys:
        val = config.get(key[0], key[1])
        if val is None or len(val.strip()) == 0:
            raise Exception("Missing value for '{k}' in section '{s}'".format(k=key[1], s=key[0]))


def run_monitor(config):
    """
    This function initializes the temperature sensor and the Nest client then will execute the main logic loop until a 
    keyboard interrupt is detected.
    :param config: 
    :return: 
    """
    try:
        scale = config.get("temperature", "scale")
        thermometer = sensor.TempSensor(config.getint("wiring", "datachannel"))
        nest_api = nest.Nest(config.get("nestapi", "clientid"), config.get("nestapi", "clientsecret"),
                             config.get("nestapi", "pincode"))
        start_http_server(config.getint("prometheus", "prometheus_port"))
        temp_gauge = Gauge('temperature', "Temperature in {scale}".format(scale=scale), ['loc'])
        humid_gauge = Gauge('humidity', 'Humidity', ['loc'])
        count = 0
        while True:
            sensor_temp, sensor_humid = read_temp_and_humidity(thermometer, scale)
            temp_gauge.labels('remote').set(sensor_temp)
            humid_gauge.labels('remote').set(sensor_humid)

            if count % NEST_REFRESH_ITER == 0:
                count = 0
                nest_api.reload_data()
                temp_gauge.labels('thermostat').set(nest_api.get_current_temp())
                humid_gauge.labels('thermostat').set(nest_api.get_thermostat_field('humidity'))

                if config.getboolean("nestling", "adjust_temp"):
                    adjust_temp_if_needed(nest_api, sensor_temp, config.getint('temperature', 'target_heat'),
                                          config.getint('temperature', 'target_cool'))
            count += 1
            time.sleep(INTERVAL_SEC)
    except KeyboardInterrupt:
        print("Shutting down.")
        sensor.cleanup()


def read_temp_and_humidity(sensor, scale="f"):
    """
    Reads the current temperature and humidity.
    :param sensor:
    :param scale: default is f (fahrenheit)
    :return:
    """
    (temperature, humidity) = sensor.get_data(scale)
    while temperature is None or temperature <= 32:
        (temperature, humidity) = sensor.get_data()
        time.sleep(.5)
    return temperature, humidity


def adjust_temp_if_needed(nest_api, sensor_temp, target_heat, target_cool):
    """
    Checks to see if we need to adjust the temperature on the thermostat based on the following rules:
    - nest thinks someone is home
    - the nest isn't running
    :param nest_api: 
    :param sensor_temp:
    :param target_heat
    :param target_cool
    :return: 
    """
    desired_temp_delta = None
    target_temp = None
    if sensor_temp > target_cool:
        desired_temp_delta = sensor_temp - target_cool
        target_temp = target_cool
    elif sensor_temp < target_heat:
        desired_temp_delta = target_heat - sensor_temp
        target_temp = target_heat
    if desired_temp_delta is None:
        logging.debug("No adjustment needed")
        return
    # only care if someone is home
    if nest_api.is_home():
        cur_thermostat_temp = nest_api.get_current_temp()
        # only make changes if hvac is not already running
        if nest_api.get_thermostat_field("hvac_state") == "off":
            logging.debug("target: {tgt}, remote: {rem}, therm: {therm}".format(tgt=sensor_temp + desired_temp_delta,
                                                                                rem=sensor_temp,
                                                                                therm=cur_thermostat_temp))
            # sanity check to ensure we don't do something crazy
            # need to ensure we are allowed to heat/cool
            if validate_temperature_delta(nest_api.get_thermostat_field("hvac_mode"), desired_temp_delta):
                # apply the change
                nest_api.set_temp(target_temp + desired_temp_delta)
                logging.info("Changed the temp to {val}".format(val=(target_temp + desired_temp_delta)))


def validate_temperature_delta(mode, delta):
    """
    Checks if the delta can be applied by ensuring the mode passed in supports applying the temperature delta (i.e. if 
    we want to turn down the temp, must be in either cool or heat-cool mode) and that we are not trying to adjust things
    by too much.
    :param mode: 
    :param delta: 
    :return: 
    """
    # sanity check to ensure we don't do something crazy
    if abs(delta) > MAX_ALLOWED_DELTA:
        logging.warning("Delta {delta} too high. Not adjusting temperature".format(delta=MAX_ALLOWED_DELTA))
        return False
    elif abs(delta) < 1:
        logging.debug("Delta is less than one degree. Not adjusting temperature.")
    if delta <= 0:
        return mode.lower().strip() in ["cool", "heat-cool"]
    else:
        return mode.lower().strip() in ["heat", "heat-cool"]


def main():
    config = configparser.ConfigParser()
    config.read(CONF_FILE)
    try:
        validate_config(config)
    except Exception as e:
        logging.error("{file} failed validation. {msg}".format(file=CONF_FILE, msg=e.message))
        sys.exit(1)
    logging.info("Running Nestling. Press control+c to terminate.")
    run_monitor(config)


if __name__ == "__main__":
    main()
