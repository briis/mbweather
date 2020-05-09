"""Constants in mbweather component."""
import logging

from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN

DOMAIN = "mbweather"

ENTITY_ID_SENSOR_FORMAT = SENSOR_DOMAIN + ".mbw_{}"
ENTITY_ID_BINARY_SENSOR_FORMAT = BINARY_SENSOR_DOMAIN + ".mbw_{}"
ENTITY_ID_WEATHER_FORMAT = WEATHER_DOMAIN + ".mbw_{}"

DEFAULT_ATTRIBUTION = "Weather data delivered by a Meteobridge powered Weather Station"

LOGGER = logging.getLogger(__package__)
