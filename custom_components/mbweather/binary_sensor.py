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
from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from homeassistant.const import ATTR_ATTRIBUTION, CONF_MONITORED_CONDITIONS, CONF_NAME
from homeassistant.helpers.entity import generate_entity_id
from . import DEFAULT_ATTRIBUTION, MBDATA, DOMAIN

DEPENDENCIES = ["mbweather"]

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "raining": ["Raining", None, "mdi:water", "mdi:water-off"],
    "lowbattery": ["Battery Status", None, "mdi:battery-10", "mdi:battery"],
    "freezing": ["Freezing", None, "mdi:thermometer-minus", "mdi:thermometer-plus"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
        vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    """Set up the MBWeather binary sensor platform."""
    coordinator = hass.data[MBDATA]["coordinator"]
    if not coordinator.data:
        return

    name = config.get(CONF_NAME)

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(MBweatherBinarySensor(coordinator, variable, name))
        _LOGGER.debug("Binary ensor added: %s", variable)

    async_add_entities(sensors, True)


class MBweatherBinarySensor(BinarySensorEntity):
    """ Implementation of a MBWeather Binary Sensor. """

    def __init__(self, coordinator, condition, name):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._condition = condition
        self._device_class = SENSOR_TYPES[self._condition][1]
        self._name = SENSOR_TYPES[self._condition][0]
        self._unique_id = f"mbw_{self._name.lower().replace(' ', '_')}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._condition] is True

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return (
            SENSOR_TYPES[self._condition][2]
            if self.coordinator.data[self._condition]
            else SENSOR_TYPES[self._condition][3]
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self._condition][1]

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr[ATTR_ATTRIBUTION] = DEFAULT_ATTRIBUTION
        return attr

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)
