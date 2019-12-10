"""
    Support for Meteobridge SmartEmbed
    This component will read the local weatherstation data
    and create Binary sensors for each type defined below.

    For a full description, go here: https://github.com/briis/hass-mbweather

    Author: Bjarne Riis
"""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import (ENTITY_ID_FORMAT,
                                                    PLATFORM_SCHEMA,
                                                    BinarySensorDevice)
from homeassistant.const import (ATTR_ATTRIBUTION, CONF_ENTITY_NAMESPACE,
                                 CONF_MONITORED_CONDITIONS, CONF_NAME)
from homeassistant.helpers.entity import Entity, generate_entity_id
from . import ATTRIBUTION, MBDATA

DEPENDENCIES = ['mbweather']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mbweather'

SENSOR_TYPES = {
    'raining': ['Raining', None, 'mdi:water', 'mdi:water-off'],
    'lowbattery': ['Battery Status', None, 'mdi:battery-10', 'mdi:battery'],
    'freezing': ['Freezing', None, 'mdi:thermometer-minus', 'mdi:thermometer-plus']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DOMAIN): cv.string
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MBWeather binary sensor platform."""

    name = config.get(CONF_NAME)
    data = hass.data[MBDATA]

    if data.data['time'] is None:
        return

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(MBweatherBinarySensor(hass, data, variable, name))
        _LOGGER.debug("Binary ensor added: %s", variable)

    add_entities(sensors, True)

class MBweatherBinarySensor(BinarySensorDevice):
    """ Implementation of a MBWeather Binary Sensor. """

    def __init__(self, hass, data, condition, name):
        """Initialize the sensor."""
        self._condition = condition
        self.data = data
        self._device_class = SENSOR_TYPES[self._condition][1]
        self._name = SENSOR_TYPES[self._condition][0]
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, '{} {}'.format('mbw', SENSOR_TYPES[self._condition][0]), hass=hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        if self._condition in self.data.data:
            variable = self.data.data[self._condition]
            if not (variable is None):
                return variable
        return None

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._condition][2] if self.data.data[self._condition] \
            else SENSOR_TYPES[self._condition][3]

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self._condition][1]

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attr

    def update(self):
        """Update current conditions."""
        self.data.update()
