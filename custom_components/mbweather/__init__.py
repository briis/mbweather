"""Meteobridge Weather Integration for Home Assistant"""
import xml.etree.ElementTree
import logging
import requests
import csv
from datetime import timedelta, datetime
import voluptuous as vol

from homeassistant.const import (TEMP_CELSIUS, CONF_NAME, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL, PRECISION_TENTHS, PRECISION_WHOLE)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from . import meteobridge as mb

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
ATTR_WEATHER_PRECIP_PPROBABILIY = "precip_probability"

DOMAIN = 'mbweather'
MBDATA = DOMAIN
CONF_USE_SLL = 'use_ssl'

DEFAULT_ATTRIBUTION = "Weather data delivered by a Meteobridge powered Weather Station"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
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
    scan_interval = conf[CONF_SCAN_INTERVAL]

    hass.data[MBDATA] = mb.meteobridge(host, username, password, ssl, unit_system)
    hass.data[CONF_NAME] = name

    async def _async_systems_update(now):
        """Refresh internal state for all systems."""
        hass.data[MBDATA].update()

        async_dispatcher_send(hass, DOMAIN)

    async_track_time_interval(hass, _async_systems_update, scan_interval)

    return True


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
    def precip_probability(self):
        """Return the Precipitation Probability."""
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

        precip_probability = self.precip_probability
        if precip_probability is not None:
            data[ATTR_WEATHER_PRECIP_PPROBABILIY] = precip_probability

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
