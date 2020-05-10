"""Constants in mbweather component."""
import logging

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN

DOMAIN = "meteobridge"

ENTITY_ID_SENSOR_FORMAT = SENSOR_DOMAIN + ".mb_{}"
ENTITY_ID_BINARY_SENSOR_FORMAT = BINARY_SENSOR_DOMAIN + ".mb_{}"
ENTITY_UNIQUE_ID = "mb_{}"

METEOBRIDGE_PLATFORMS = [
    "binary_sensor",
    "sensor",
]

CONF_WIND_UNIT = "wind_unit"

ATTR_UPDATED = "updated"

DEFAULT_ATTRIBUTION = "Data delivered by a Meteobridge powered Weather Station"
DEFAULT_USERNAME = "meteobridge"

LOGGER = logging.getLogger(__package__)
