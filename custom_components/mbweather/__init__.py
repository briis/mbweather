"""Meteobridge Weather Integration for Home Assistant"""
import xml.etree.ElementTree
import logging
import requests
import csv
from datetime import timedelta, datetime

import voluptuous as vol

from homeassistant.const import (TEMP_CELSIUS, CONF_NAME, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, PRECISION_TENTHS, PRECISION_WHOLE)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ATTR_CONDITION_CLASS = "condition_class"
ATTR_FORECAST = "forecast"
ATTR_FORECAST_CONDITION = "condition"
ATTR_FORECAST_PRECIPITATION = "precipitation"
ATTR_FORECAST_TEMP = "temperature"
ATTR_FORECAST_TEMP_LOW = "templow"
ATTR_FORECAST_TIME = "datetime"
ATTR_FORECAST_WIND_BEARING = "wind_bearing"
ATTR_FORECAST_WIND_SPEED = "wind_speed"
ATTR_WEATHER_ATTRIBUTION = "attribution"
ATTR_WEATHER_HUMIDITY = "humidity"
ATTR_WEATHER_OZONE = "ozone"
ATTR_WEATHER_PRESSURE = "pressure"
ATTR_WEATHER_TEMPERATURE = "temperature"
ATTR_WEATHER_VISIBILITY = "visibility"
ATTR_WEATHER_WIND_BEARING = "wind_bearing"
ATTR_WEATHER_WIND_SPEED = "wind_speed"
ATTR_WEATHER_RAINTODAY = "rain_today"
ATTR_WEATHER_RAINRATE = "rain_rate"

DOMAIN = 'mbweather'
ATTRIBUTION = "Weather data delivered by a Meteobridge powered Weather Station"
MBDATA = 'mbdata'
CONF_USE_SLL = 'use_ssl'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_USE_SLL, default=False): cv.string,
        vol.Optional(CONF_NAME, default=DOMAIN): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up the MBWeather platform."""

    conf = config[DOMAIN]
    host = conf[CONF_HOST]
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    name = conf[CONF_NAME]
    ssl = conf[CONF_USE_SLL]
    unit_system = 'metric' if hass.config.units.is_metric else 'imperial'

    mbw = getWeatherData(host, username, password, ssl, unit_system)
    mbw.update()
    _LOGGER.debug("Data Returned: %s ", mbw.data)

    if mbw.data['time'] is None:
        return False

    hass.data[MBDATA] = mbw
    hass.data[CONF_NAME] = name

    return True

class getWeatherData:

    def __init__(self, Host, User, Pass, ssl, unit_system):
        self._host = Host
        self._user = User
        self._pass = Pass
        self._ssl = ssl
        self._unit_system = unit_system
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from the Weatherstation."""
        mbdata = mbweatherData(self._host, self._user, self._pass, self._ssl, self._unit_system)
        self.data = mbdata

class mbweatherData:

    def __init__(self):
        self._host = None
        self._user = None
        self._pass = None
        self._ssl = None
        self._unit_system = None
        self.data = None
   
    def __new__(self, Host, User, Pass, ssl, unit_system):
        self._host = Host
        self._user = User
        self._pass = Pass
        self._ssl = ssl
        self._unit_system = unit_system
        self._winddir = ''
        self._windbearing = 0
        self._windgust = 0
        self._windspeedavg = 0
        self._windspeed = 0
        self._lowbat = False
        self._windchill = 0
        self._heatindex = 0
        self._feels_like = 0
        self._intemp = 0
        self._inhum = 0
        self._press = 0
        self._fc = ''
        self._outtemp = 0
        self._temphigh = 0
        self._templow = 0
        self._outhum = 0
        self._outdew = 0
        self._rainrate = 0
        self._raintoday = 0
        self._israining = False
        self._isfreezing = False
        self._islowbat = False
        self._timestamp = None

        self._getData(self)

        retval = {
            'in_temperature': self._intemp,
            'in_humidity': self._inhum,
            'temperature': self._outtemp,
            'temphigh': self._temphigh,
            'templow': self._templow,
            'humidity': self._outhum,
            'dewpoint': self._outdew,
            'windbearing': self._windbearing,
            'winddirection': self._winddir,
            'windspeedavg': self._windspeedavg,
            'windspeed': self._windspeed,
            'windgust': self._windgust,
            'windchill': self._windchill,
            'heatindex': self._heatindex,
            'feels_like': self._feels_like,
            'pressure': self._press,
            'rainrate': self._rainrate,
            'raintoday': self._raintoday,
            'lowbattery': self._islowbat,
            'raining': self._israining,
            'freezing': self._isfreezing,
            'forecast': self._fc,
            'time': self._timestamp
            }
        
        return retval

    def _getData(self):
        dataRequest = '[DD]/[MM]/[YYYY];[hh]:[mm]:[ss];[th0temp-act:0];[thb0seapress-act:--];[th0hum-act:--];[wind0avgwind-act:--];[wind0dir-avg5.0:--];[rain0total-daysum:--];[rain0rate-act:--];[th0dew-act:--];[wind0chill-act:0];[wind0wind-max1:--];[th0lowbat-act.0:--];[thb0temp-act:--];[thb0hum-act.0:--];[th0temp-dmax:--];[th0temp-dmin:--];[wind0wind-act:--];[th0heatindex-act.1:0];[forecast-text:]'
        preUrl = 'https://'
        if self._ssl.lower() != 'true':
            preUrl = 'http://'

        reqUrl = preUrl + self._user + ':' + self._pass + '@' + self._host + '/cgi-bin/template.cgi?template=' + dataRequest
        # reqUrl = 'http://docker.for.mac.localhost/mbhaweather.txt'

        with requests.Session() as s:
            response = s.get(reqUrl)
            if response.status_code != 200:
                _LOGGER.debug("Invalid response from API")
            else:
                decoded_content = response.content.decode('utf-8')
                _LOGGER.debug("Raw: " + decoded_content)
                cr = csv.reader(decoded_content.splitlines(), delimiter=';')
                rows = list(cr)
                cnv = Conversion()

                for values in rows:
                    self._timestamp = datetime.strptime(values[0] + ' ' + values[1], '%d/%m/%Y %H:%M:%S')

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

                    if float(self._outtemp) < 0:
                        self._isfreezing = True
                    else:
                        self._isfreezing = False

                    if float(self._rainrate) > 0:
                        self._israining = True
                    else:
                        self._israining = False

                    if float(self._lowbat) > 0:
                        self._islowbat = True
                    else:
                        self._islowbat = False

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
        if unit.lower() == 'imperial':
            # Return value F
            return round((value*9/5)+32,1)
        else:
            # Return value C
            return round(value,1)

    def volume(self, value, unit):
        if unit.lower() == 'imperial':
            # Return value in
            return round(value * 0.0393700787,2)
        else:
            # Return value mm
            return round(value,1)

    def rate(self, value, unit):
        if unit.lower() == 'imperial':
            # Return value in
            return round(value * 0.0393700787,2)
        else:
            # Return value mm
            return round(value,2)

    def pressure(self, value, unit):
        if unit.lower() == 'imperial':
            # Return value inHg
            return round(value * 0.0295299801647,3)
        else:
            # Return value mb
            return round(value,1)

    def speed(self, value, unit):
        if unit.lower() == 'imperial':
            # Return value in mi/h
            return round(value*2.2369362921,1)
        else:
            # Return value in m/s
            return round(value,1)

    def distance(self, value, unit):
        if unit.lower() == 'imperial':
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
        direction_array = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']
        direction = direction_array[int((bearing + 11.25) / 22.5)]
        return direction

class WeatherEntityExt(Entity):
    """ABC for weather data. Extended with extra Attributes"""

    @property
    def temperature(self):
        """Return the platform temperature."""
        raise NotImplementedError()

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        raise NotImplementedError()

    @property
    def pressure(self):
        """Return the pressure."""
        return None

    @property
    def humidity(self):
        """Return the humidity."""
        raise NotImplementedError()

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return None

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return None

    @property
    def ozone(self):
        """Return the ozone level."""
        return None

    @property
    def attribution(self):
        """Return the attribution."""
        return None

    @property
    def visibility(self):
        """Return the visibility."""
        return None

    @property
    def rain_today(self):
        """Return the Precipitation for the day."""
        return None

    @property
    def rain_rate(self):
        """Return the current Precipitation rate."""
        return None

    @property
    def forecast(self):
        """Return the forecast."""
        return None

    @property
    def precision(self):
        """Return the forecast."""
        return (
            PRECISION_TENTHS
            if self.temperature_unit == TEMP_CELSIUS
            else PRECISION_WHOLE
        )

    @property
    def state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self.temperature is not None:
            data[ATTR_WEATHER_TEMPERATURE] = show_temp(
                self.hass, self.temperature, self.temperature_unit, self.precision
            )

        humidity = self.humidity
        if humidity is not None:
            data[ATTR_WEATHER_HUMIDITY] = round(humidity)

        ozone = self.ozone
        if ozone is not None:
            data[ATTR_WEATHER_OZONE] = ozone

        pressure = self.pressure
        if pressure is not None:
            data[ATTR_WEATHER_PRESSURE] = pressure

        wind_bearing = self.wind_bearing
        if wind_bearing is not None:
            data[ATTR_WEATHER_WIND_BEARING] = wind_bearing

        wind_speed = self.wind_speed
        if wind_speed is not None:
            data[ATTR_WEATHER_WIND_SPEED] = wind_speed

        visibility = self.visibility
        if visibility is not None:
            data[ATTR_WEATHER_VISIBILITY] = visibility

        rain_today = self.rain_today
        if rain_today is not None:
            data[ATTR_WEATHER_RAINTODAY] = rain_today

        rain_rate = self.rain_rate
        if rain_rate is not None:
            data[ATTR_WEATHER_RAINRATE] = rain_rate

        attribution = self.attribution
        if attribution is not None:
            data[ATTR_WEATHER_ATTRIBUTION] = attribution

        if self.forecast is not None:
            forecast = []
            for forecast_entry in self.forecast:
                forecast_entry = dict(forecast_entry)
                forecast_entry[ATTR_FORECAST_TEMP] = show_temp(
                    self.hass,
                    forecast_entry[ATTR_FORECAST_TEMP],
                    self.temperature_unit,
                    self.precision,
                )
                if ATTR_FORECAST_TEMP_LOW in forecast_entry:
                    forecast_entry[ATTR_FORECAST_TEMP_LOW] = show_temp(
                        self.hass,
                        forecast_entry[ATTR_FORECAST_TEMP_LOW],
                        self.temperature_unit,
                        self.precision,
                    )
                forecast.append(forecast_entry)

            data[ATTR_FORECAST] = forecast

        return data

    @property
    def state(self):
        """Return the current state."""
        return self.condition

    @property
    def condition(self):
        """Return the current condition."""
        raise NotImplementedError()
