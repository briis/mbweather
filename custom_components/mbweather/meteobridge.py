"""Wrapper to retrieve Weather data from a Meteobridge Data Logger
   Specifically developed to wotk with Home Assistant
   Developed by: @briis
   Github: https://github.com/briis/mbweather
   License: MIT
"""

import csv
import requests
from datetime import datetime
class meteobridge:
    """Main class to retrieve the data from the Logger."""

    def __init__(self, Host, User, Pass, ssl, unit_system):
        super().__init__()
        self._host = Host
        self._user = User
        self._pass = Pass
        self._ssl = ssl
        self._unit_system = unit_system
        self.sensor_data = {}

        self.req = requests.session()
        self.update()

    @property
    def sensors(self):
        """Returns a JSON formatted array with all sensor data."""
        return self.sensor_data

    def update(self):
        """Updates the sensor data."""
        self._get_sensor_data()

    def _get_sensor_data(self):
        """Gets the sensor data from the Meteobridge Logger"""

        dataTemplate = "[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:--];[th0hum-act:--];[wind0avgwind-act:--];[wind0dir-avg5.0:--];[rain0total-daysum:--];[rain0rate-act:--];[th0dew-act:--];[wind0chill-act:0];[wind0wind-max1:--];[th0lowbat-act.0:--];[thb0temp-act:--];[thb0hum-act.0:--];[th0temp-dmax:--];[th0temp-dmin:--];[wind0wind-act:--];[th0heatindex-act.1:0];[forecast-text:]"
        preUrl = "https://"
        if self._ssl != True:
            preUrl = "http://"

        reqUrl = preUrl + self._user + ":" + self._pass + "@" + self._host + "/cgi-bin/template.cgi?template=" + dataTemplate

        response = self.req.get(reqUrl)
        if response.status_code == 200:
            decoded_content = response.content.decode("utf-8")
            cr = csv.reader(decoded_content.splitlines(), delimiter=";")
            rows = list(cr)
            cnv = Conversion()

            for values in rows:
                self._timestamp = datetime.strptime(values[0] + " " + values[1], "%d/%m/%Y %H:%M:%S")

                self._outtemp = values[2]
                self._press = cnv.pressure(float(values[3]),self._unit_system)
                self._outhum = values[4]
                self._windspeedavg = cnv.speed(float(values[5]), self._unit_system)
                self._windbearing = int(float(values[6]))
                self._winddir = cnv.wind_direction(float(values[6]))
                self._raintoday = cnv.volume(float(values[7]), self._unit_system)
                self._rainrate = cnv.rate(float(values[8]), self._unit_system)
                self._outdew = values[9]
                self._windchill = values[10]
                self._windgust = cnv.speed(float(values[11]), self._unit_system)
                self._lowbat = values[12]
                self._intemp = values[13]
                self._inhum = values[14]
                self._temphigh = values[15]
                self._templow = values[16]
                self._windspeed = cnv.speed(float(values[17]), self._unit_system)
                self._heatindex = values[18]
                self._feels_like = cnv.feels_like(self._outtemp,self._heatindex, self._windchill)
                self._fc = values[19]

                self._isfreezing = True if float(self._outtemp) < 0 else False
                self._israining = True if float(self._rainrate) > 0 else False
                self._islowbat = True if float(self._lowbat) > 0 else False

                # Data below is comming from Dark Sky, and is updated by external component. Thus we need to check if available
                # and don't overwrite values if present.
                if "condition" in self.sensor_data:
                    if self.sensor_data["condition"] is not None:
                        self._condition = self.sensor_data["condition"]
                    else:
                        self._condition = None
                else:
                    self._condition = None

                if "precip_probability" in self.sensor_data:
                    if self.sensor_data["precip_probability"] is not None:
                        self._precip_probability = self.sensor_data["precip_probability"]
                    else:
                        self._precip_probability = None
                else:
                    self._precip_probability = None

            item = {
                "in_temperature": self._intemp,
                "in_humidity": self._inhum,
                "temperature": self._outtemp,
                "temphigh": self._temphigh,
                "templow": self._templow,
                "humidity": self._outhum,
                "dewpoint": self._outdew,
                "windbearing": self._windbearing,
                "winddirection": self._winddir,
                "windspeedavg": self._windspeedavg,
                "windspeed": self._windspeed,
                "windgust": self._windgust,
                "windchill": self._windchill,
                "heatindex": self._heatindex,
                "feels_like": self._feels_like,
                "pressure": self._press,
                "rainrate": self._rainrate,
                "raintoday": self._raintoday,
                "lowbattery": self._islowbat,
                "raining": self._israining,
                "freezing": self._isfreezing,
                "forecast": self._fc,
                "time": self._timestamp.strftime("%d-%m-%Y %H:%M:%S"),
                "condition": self._condition,
                "precip_probability": self._precip_probability
            }
            self.sensor_data.update(item)

class Conversion:

    """
    Conversion Class to convert between different units.
    WeatherFlow always delivers values in the following formats:
    Temperature: C
    Wind Speed: m/s
    Wind Direction: Degrees
    Pressure: mb
    Distance: km
    """

    def temperature(self, value, unit):
        if unit.lower() == "imperial":
            # Return value F
            return round((value*9/5)+32,1)
        else:
            # Return value C
            return round(value,1)

    def volume(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in
            return round(value * 0.0393700787,2)
        else:
            # Return value mm
            return round(value,1)

    def rate(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in
            return round(value * 0.0393700787,2)
        else:
            # Return value mm
            return round(value,2)

    def pressure(self, value, unit):
        if unit.lower() == "imperial":
            # Return value inHg
            return round(value * 0.0295299801647,3)
        else:
            # Return value mb
            return round(value,1)

    def speed(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in mi/h
            return round(value*2.2369362921,1)
        else:
            # Return value in m/s
            return round(value,1)

    def distance(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in mi
            return round(value*0.621371192,1)
        else:
            # Return value in m/s
            return round(value,0)

    def feels_like(self, temp, heatindex, windchill):
        """ Return Feels Like Temp."""
        if (float(temp) > 26.666666667):
            return float(heatindex)
        elif (float(temp) < 10):
            return float(windchill)
        else:
            return temp

    def wind_direction(self, bearing):
        direction_array = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW","N"]
        direction = direction_array[int((bearing + 11.25) / 22.5)]
        return direction


