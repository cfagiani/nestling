import sys
import time
import ConfigParser  # note if using python3, rename to configparser
import sensor
import nest

CONF_FILE = "config.ini"
INTERVAL_SEC = 60 * 5  # sample every 5 minutes
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
        thermometer = sensor.TempSensor(config.getint("wiring", "datachannel"))
        nest_api = nest.Nest(config.get("nestapi", "clientid"), config.get("nestapi", "clientsecret"),
                             config.get("nestapi", "pincode"))
        while True:
            adjustment = get_desired_temp_adjustment(thermometer)
            adjust_temp_if_needed(nest_api, adjustment)
            time.sleep(INTERVAL_SEC)
    except KeyboardInterrupt:
        print("Shutting down.")
        sensor.cleanup()


def get_desired_temp_adjustment(thermometer):
    """
    Obtains a reading from the temperature sensor and returns a pair consisting of the target temperature and the 
    current temperature.  
    :param thermometer: 
    :return: 
    """
    (temperature, humidity) = thermometer.get_data(scale="f")
    while temperature is None or temperature <= 32:
        (temperature, humidity) = thermometer.get_data()
        time.sleep(.5)
    print ("got reading of {temp}".format(temp=temperature))
    if temperature < config.getint("temperature", "targetheat"):
        return config.getint("temperature", "targetheat"), temperature
    elif temperature > config.getint("temperature", "targetcool"):
        return config.getint("temperature", "targetcool"), temperature
    else:
        return None


def adjust_temp_if_needed(nest_api, adjustment):
    """
    Checks to see if we need to adjust the temperature on the thermostat based on the following rules:
    - adjustment is not None
    - nest thinks someone is home
    - the nest isn't running
    :param nest_api: 
    :param adjustment: 
    :return: 
    """
    if adjustment is None:
        print ("No adjustment needed")
        return
    # only care if someone is home
    if nest_api.is_home(refresh=True):
        # only make changes if hvac is not already running
        if nest_api.get_thermostat_field("hvac_state") == "off":
            cur_thermostat_temp = nest_api.get_current_temp()
            target_temp = adjustment[0]
            cur_remote_temp = adjustment[1]
            desired_temp_delta = target_temp - cur_remote_temp
            print ("target: {tgt}, remote: {rem}, therm: {therm}".format(tgt=target_temp, rem=cur_remote_temp,
                                                                         therm=cur_thermostat_temp))
            # sanity check to ensure we don't do something crazy
            # need to ensure we are allowed to heat/cool
            if validate_temperature_delta(nest_api.get_thermostat_field("hvac_mode"), desired_temp_delta):
                # apply the change
                nest_api.set_temp(target_temp + desired_temp_delta)
                print ("Changed the temp to {val}".format(val=(target_temp + desired_temp_delta)))



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
        print("Delta {delta} too high. Not adjusting temp".format(delta=MAX_ALLOWED_DELTA))
        return False
    if delta <= 0:
        return mode.lower().strip() in ["cool", "heat-cool"]
    else:
        return mode.lower().strip() in ["heat", "heat-cool"]


if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.read(CONF_FILE)
    try:
        validate_config(config)
    except Exception as e:
        print("{file} failed validation. {msg}".format(file=CONF_FILE, msg=e.message))
        sys.exit(1)
    print("Running Nestling. Press control+c to terminate.")
    run_monitor(config)
