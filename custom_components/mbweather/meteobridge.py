"""Wrapper to retrieve Weather data from a Meteobridge Data Logger
   Specifically developed to wotk with Home Assistant
   Developed by: @briis
   Github: https://github.com/briis/mbweather
   License: MIT
"""

import csv
import aiohttp
import logging
from datetime import datetime


class UnexpectedError(Exception):
    """Other error."""

    pass


_LOGGER = logging.getLogger(__name__)


class Meteobridge:
    """Main class to retrieve the data from the Logger."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        Host: str,
        User: str,
        Pass: str,
        unit_system: str,
        ssl: bool = False,
    ):
        self._host = Host
        self._user = User
        self._pass = Pass
        self._ssl = ssl
        self._unit_system = unit_system
        self.sensor_data = {}

        self.req = session

    async def update(self) -> dict:
        """Updates the sensor data."""
        await self._get_sensor_data()
        return self.sensor_data

    async def _get_sensor_data(self) -> None:
        """Gets the sensor data from the Meteobridge Logger"""

        dataTemplate = "[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:0];[th0hum-act:0];[wind0avgwind-act:0];[wind0dir-avg5.0:0];[rain0total-daysum:0];[rain0rate-act:0];[th0dew-act:0];[wind0chill-act:0];[wind0wind-max1:0];[th0lowbat-act.0:0];[thb0temp-act:0];[thb0hum-act.0:0];[th0temp-dmax:0];[th0temp-dmin:0];[wind0wind-act:0];[th0heatindex-act.1:0];[uv0index-act:0];[sol0rad-act:0];[th0temp-mmin.1:0];[th0temp-mmax.1:0];[th0temp-ymin.1:0];[th0temp-ymax.1:0];[wind0wind-mmax.1:0];[wind0wind-ymax.1:0];[rain0total-mmax.1:0];[rain0total-ymax.1:0];[rain0rate-mmax.1:0];[rain0rate-ymax.1:0];[forecast-text:]"
        preUrl = "https://"
        if self._ssl != True:
            preUrl = "http://"

        reqUrl = (
            preUrl
            + self._user
            + ":"
            + self._pass
            + "@"
            + self._host
            + "/cgi-bin/template.cgi?template="
            + dataTemplate
        )

        async with self.req.get(reqUrl,) as response:
            if response.status == 200:
                content = await response.read()
                decoded_content = content.decode("utf-8")

                cr = csv.reader(decoded_content.splitlines(), delimiter=";")
                rows = list(cr)
                cnv = Conversion()

                for values in rows:
                    self._timestamp = datetime.strptime(
                        values[0] + " " + values[1], "%d/%m/%Y %H:%M:%S"
                    )

                    self._outtemp = cnv.temperature(float(values[2]), self._unit_system)
                    self._press = cnv.pressure(float(values[3]), self._unit_system)
                    self._outhum = values[4]
                    self._windspeedavg = cnv.speed(float(values[5]), self._unit_system)
                    self._windbearing = int(float(values[6]))
                    self._winddir = cnv.wind_direction(float(values[6]))
                    self._raintoday = cnv.volume(float(values[7]), self._unit_system)
                    self._rainrate = cnv.rate(float(values[8]), self._unit_system)
                    self._outdew = cnv.temperature(float(values[9]), self._unit_system)
                    self._windchill = cnv.temperature(
                        float(values[10]), self._unit_system
                    )
                    self._windgust = cnv.speed(float(values[11]), self._unit_system)
                    self._lowbat = values[12]
                    self._intemp = cnv.temperature(float(values[13]), self._unit_system)
                    self._inhum = values[14]
                    self._temphigh = cnv.temperature(
                        float(values[15]), self._unit_system
                    )
                    self._templow = cnv.temperature(
                        float(values[16]), self._unit_system
                    )
                    self._windspeed = cnv.speed(float(values[17]), self._unit_system)
                    self._heatindex = cnv.temperature(
                        float(values[18]), self._unit_system
                    )
                    self._uvindex = float(values[19])
                    self._solarrad = float(values[20])
                    self._feels_like = cnv.feels_like(
                        self._outtemp,
                        self._heatindex,
                        self._windchill,
                        self._unit_system,
                    )
                    self._tempmmin = cnv.temperature(
                        float(values[21]), self._unit_system
                    )
                    self._tempmmax = cnv.temperature(
                        float(values[22]), self._unit_system
                    )
                    self._tempymin = cnv.temperature(
                        float(values[23]), self._unit_system
                    )
                    self._tempymax = cnv.temperature(
                        float(values[24]), self._unit_system
                    )
                    self._windmmax = cnv.speed(float(values[25]), self._unit_system)
                    self._windymax = cnv.speed(float(values[26]), self._unit_system)
                    self._rainmmax = cnv.volume(float(values[27]), self._unit_system)
                    self._rainymax = cnv.volume(float(values[28]), self._unit_system)
                    self._rainratemmax = cnv.volume(
                        float(values[29]), self._unit_system
                    )
                    self._rainrateymax = cnv.volume(
                        float(values[30]), self._unit_system
                    )
                    self._fc = values[31]

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
                            self._precip_probability = self.sensor_data[
                                "precip_probability"
                            ]
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
                    "uvindex": self._uvindex,
                    "solarrad": self._solarrad,
                    "lowbattery": self._islowbat,
                    "raining": self._israining,
                    "freezing": self._isfreezing,
                    "forecast": self._fc,
                    "time": self._timestamp.strftime("%d-%m-%Y %H:%M:%S"),
                    "condition": self._condition,
                    "precip_probability": self._precip_probability,
                    "temp_mmin": self._tempmmin,
                    "temp_mmax": self._tempmmax,
                    "temp_ymin": self._tempymin,
                    "temp_ymax": self._tempymax,
                    "windspeed_mmax": self._windmmax,
                    "windspeed_ymax": self._windymax,
                    "rain_mmax": self._rainmmax,
                    "rain_ymax": self._rainymax,
                    "rainrate_mmax": self._rainratemmax,
                    "rainrate_ymax": self._rainrateymax,
                }
                self.sensor_data.update(item)
            else:
                raise UnexpectedError(
                    f"Fetching Meteobridge data failed: {response.status} - Reason: {response.reason}"
                )


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
            return round((value * 9 / 5) + 32, 1)
        else:
            # Return value C
            return round(value, 1)

    def volume(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 1)

    def rate(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in
            return round(value * 0.0393700787, 2)
        else:
            # Return value mm
            return round(value, 2)

    def pressure(self, value, unit):
        if unit.lower() == "imperial":
            # Return value inHg
            return round(value * 0.0295299801647, 3)
        else:
            # Return value mb
            return round(value, 1)

    def speed(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in mi/h
            return round(value * 2.2369362921, 1)
        else:
            # Return value in m/s
            return round(value, 1)

    def distance(self, value, unit):
        if unit.lower() == "imperial":
            # Return value in mi
            return round(value * 0.621371192, 1)
        else:
            # Return value in km
            return round(value, 0)

    def feels_like(self, temp, heatindex, windchill, unit):
        """ Return Feels Like Temp."""
        if unit.lower() == "imperial":
            high_temp = 80
            low_temp = 50
        else:
            high_temp = 26.666666667
            low_temp = 10

        if float(temp) > high_temp:
            return float(heatindex)
        elif float(temp) < low_temp:
            return float(windchill)
        else:
            return temp

    def wind_direction(self, bearing):
        direction_array = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N",
        ]
        direction = direction_array[int((bearing + 11.25) / 22.5)]
        return direction
