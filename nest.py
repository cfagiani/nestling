# Nest API client
import requests
import json

API_URL = 'https://developer-api.nest.com'
TOKEN_URL = 'https://api.home.nest.com/oauth2/access_token'

TOKEN_FILE = ".token"


class Nest(object):
    """
    Wrapper class for interacting with the Nest API. You must register a product with Nest and supply a valid
    product id and product secret. Additionally, the first time this is run, you will need to supply a valid unused pin
    code so it can obtain an auth token.
    """

    def __init__(self, client_id, client_secret, auth_code, structure="Home"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.structure = structure
        self.token = self.load_token()
        if self.token is None:
            self.token = self.auth()
        self.data = self.reload_data()

    def execute_call(self, method="get", suffix="", payload=None):
        headers = {'Authorization': 'Bearer {0}'.format(self.token),
                   'Content-Type': 'application/json'}
        if method == "get":
            initial_response = requests.get("{base}{suffix}".format(base=API_URL, suffix=suffix), headers=headers,
                                            allow_redirects=False)
            if initial_response.status_code == 307:
                initial_response = requests.get(initial_response.headers['Location'], headers=headers,
                                                allow_redirects=False)
        else:
            initial_response = requests.put("{base}{suffix}".format(base=API_URL, suffix=suffix),
                                            data=payload,
                                            headers=headers, allow_redirects=False)
        if not initial_response.ok:
            raise Exception("Could not call Nest API. Got status {code}".format(code=initial_response.status_code))
        return initial_response.text

    def set_temp(self, temp, scale="f"):
        """
        Sets the temperature on the thermostat 
        :param temp: temperature to set
        :param scale: temperature scale. (default is f)
        :return: 
        """
        if scale.lower() not in ["f", "c"]:
            raise Exception("Invalid temperature scale")
        payload = {"target_temperature_{scale}".format(scale=scale.lower): temp}
        text = self.execute_call("put", json.dumps(payload),
                                 "/devices/thermostats/{id}".format(id=self.get_thermostat_field("device_id")))
        print text

    def reload_data(self):
        """
        Attempts to read the state information and returns it as a json object.      
        :return: 
        """
        return json.loads(self.execute_call())

    def get_thermostat(self, refresh=False):
        """
        Returns the thermostat information using the cached version (unless refresh is set to true, in which case it 
        will first load the data from the server before returning)
        If no thermostats are found, an exception will be raised. If more than one thermostat is found, this will 
        return the first one that appears in the response data.
        :return: 
        """
        if self.data is None or refresh:
            self.data = self.reload_data()
        devices = self.data.get("devices")
        if devices:
            thermostats = devices.get("thermostats")
            if thermostats:
                return thermostats.values()[0]
        raise Exception("Cannot find thermostat in Nest data. Do you have one?")

    def get_thermostat_field(self, field):
        """
        Helper method to read a specific field from the thermostat data structure
        :param field: 
        :return: 
        """
        therm = self.get_thermostat()
        return therm.get(field)

    def get_current_temp(self):
        """
        Gets the current temperature in fahrenheit from the last loaded thermostat data.
        :return: 
        """
        return self.get_thermostat_field("ambient_temperature_f")

    def is_home(self, refresh=False):
        """
        Returns a boolean value indicating whether someone is at home or not.
        :param refresh: 
        :return: 
        """
        try:
            if self.data is None or refresh:
                self.data = self.reload_data()
            structures = self.data.get("structures")
            if structures:
                for (k, v) in structures.items():
                    if v.get("name") == self.structure:
                        return v.get("away") == "home"
        except:
            return False
        return False

    def load_token(self):
        """
        Loads the cached auth token from the local filesystem.
        :return: 
        """
        with open(TOKEN_FILE) as token_file:
            return token_file.read().strip()

    def auth(self):
        """
        Attempt to obtain an auth token from the token service. This method assumes the user has already generated
        a pin code by clicking on the authorization url in a web browser and accepting the permissions. The auth
        token is written to a file (.token) that will be used for subsequent calls. If that file is deleted, a new 
        pin code must be generated prior to re-running as pin codes are one-time-only.
        :return: 
        """
        payload = "code={auth}&client_id={cid}&client_secret={sec}&grant_type=authorization_code".format(
            cid=self.client_id, sec=self.client_secret, auth=self.auth_code)
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", TOKEN_URL, data=payload, headers=headers)
        if response.ok:
            json_token = json.loads(response.text)
            token = json_token.get("access_token")
            with open(TOKEN_FILE, "w") as token_file:
                token_file.write(token.strip())
            return token
        else:
            print("Error obtaining access token. Check config file for proper clientid, clientsecret, and pincode")
            raise Exception("Authorization Error. Check config file for proper clientid, clientsecret, and pincode.")
