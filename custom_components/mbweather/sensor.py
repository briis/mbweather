"""
    Support for the Meteobridge SmartEmbed
    This component will read the local weatherstation data
    and create sensors for each type.

    For a full description, go here: https://github.com/briis/mbweather

    Author: Bjarne Riis
"""
import logging
import voluptuous as vol
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_FRIENDLY_NAME,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from . import MBDATA, DOMAIN, DEFAULT_ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["mbweather"]

SCAN_INTERVAL = timedelta(seconds=5)

CONF_WIND_UNIT = "wind_unit"

ATTR_UPDATED = "updated"

SENSOR_TYPES = {
    "temperature": [
        "Temperature",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "temphigh": [
        "Temp High Today",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "templow": [
        "Temp Low Today",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "in_temperature": [
        "Indoor Temp",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "dewpoint": [
        "Dewpoint",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "windchill": [
        "Wind Chill",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "heatindex": [
        "Heatindex",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "feels_like": [
        "Feels Like",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "windspeedavg": ["Wind Speed Avg", "m/s", "mdi:weather-windy", None, "mph"],
    "windspeed": ["Wind Speed", "m/s", "mdi:weather-windy", None, "mph"],
    "windbearing": ["Wind Bearing", "°", "mdi:compass-outline", None, None],
    "winddirection": ["Wind Direction", "", "mdi:compass-outline", None, None],
    "windgust": ["Wind Gust", "m/s", "mdi:weather-windy", None, "mph"],
    "raintoday": ["Rain today", "mm", "mdi:weather-rainy", None, "in"],
    "rainrate": ["Rain rate", "mm/h", "mdi:weather-pouring", None, "in/h"],
    "humidity": ["Humidity", "%", "mdi:water-percent", DEVICE_CLASS_HUMIDITY, None],
    "in_humidity": [
        "Indoor Hum",
        "%",
        "mdi:water-percent",
        DEVICE_CLASS_HUMIDITY,
        None,
    ],
    "pressure": ["Pressure", "hPa", "mdi:gauge", DEVICE_CLASS_PRESSURE, "inHg"],
    "uvindex": ["UV Index", "UVI", "mdi:weather-sunny-alert", None, "UVI"],
    "solarrad": ["Solar Radiation", "W/m2", "mdi:weather-sunny", None, "W/m2"],
    "condition": ["Condition", "", "mdi:text-short", None, None],
    "precip_probability": ["Precip Probability", "%", "mdi:water-percent", None, None],
    "forecast": ["Forecast", "", "mdi:text-short", None, None],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
        vol.Optional(CONF_WIND_UNIT, default="ms"): cv.string,
        vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    """Set up the Meteobridge sensor platform."""
    coordinator = hass.data[MBDATA]["coordinator"]
    if not coordinator.data:
        return

    unit_system = "metric" if hass.config.units.is_metric else "imperial"
    name = config.get(CONF_NAME)
    wind_unit = config.get(CONF_WIND_UNIT)

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(
            MBWeatherSensor(coordinator, variable, name, unit_system, wind_unit)
        )

    async_add_entities(sensors, True)


class MBWeatherSensor(Entity):
    """ Implementation of a SmartWeather Weatherflow Current Sensor. """

    def __init__(self, coordinator, condition, name, unit_system, wind_unit):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._condition = condition
        self._unit_system = unit_system
        self._wind_unit = wind_unit
        self._state = None
        self._name = f"mbw_{SENSOR_TYPES[self._condition][0]}"
        self._unique_id = f"mbw_{self._name.lower().replace(' ', '_')}"
        # _LOGGER.debug(f"SENSOR: {self._condition} added")

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._condition in self.coordinator.data:
            if not (self.coordinator.data[self._condition] is None):
                self._state = self.coordinator.data[self._condition]
                # _LOGGER.debug(
                #     f"SENSOR: {SENSOR_TYPES[self._condition][0]} with Value: {self._state}"
                # )
                if SENSOR_TYPES[self._condition][1] == "m/s":
                    return (
                        round(self._state * 3.6, 1)
                        if self._wind_unit == "kmh"
                        else self._state
                    )
                else:
                    return self._state
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._unit_system == "imperial" and not (
            SENSOR_TYPES[self._condition][4] is None
        ):
            return SENSOR_TYPES[self._condition][4]
        else:
            if SENSOR_TYPES[self._condition][1] == "m/s":
                return (
                    "km/h"
                    if self._wind_unit == "kmh"
                    else SENSOR_TYPES[self._condition][1]
                )
            else:
                return SENSOR_TYPES[self._condition][1]

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._condition][2]

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self._condition][3]

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr[ATTR_ATTRIBUTION] = DEFAULT_ATTRIBUTION
        attr[ATTR_UPDATED] = self.coordinator.data["time"]

        return attr

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)
