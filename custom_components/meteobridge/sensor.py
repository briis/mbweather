"""
    Support for the Meteobridge SmartEmbed
    This component will read the local weatherstation data
    and create sensors for each type.

    For a full description, go here: https://github.com/briis/mbweather

    Author: Bjarne Riis
"""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_NAME,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity

from . import MBDATA
from .const import (
    DOMAIN,
    DEFAULT_ATTRIBUTION,
    ENTITY_ID_SENSOR_FORMAT,
    ENTITY_UNIQUE_ID,
    CONF_WIND_UNIT,
    ATTR_UPDATED,
)

_LOGGER = logging.getLogger(__name__)

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
    "forecast": ["Forecast", "", "mdi:text-short", None, None],
    "temp_mmin": [
        "Temp Month Min",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "temp_mmax": [
        "Temp Month Max",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "temp_ymin": [
        "Temp Year Min",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "temp_ymax": [
        "Temp Year Max",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
        TEMP_FAHRENHEIT,
    ],
    "windspeed_mmax": ["Wind Speed Month Max", "m/s", "mdi:weather-windy", None, "mph"],
    "windspeed_ymax": ["Wind Speed Year Max", "m/s", "mdi:weather-windy", None, "mph"],
    "rain_mmax": ["Rain Month Total", "mm", "mdi:weather-rainy", None, "in"],
    "rain_ymax": ["Rain Year Total", "mm", "mdi:weather-rainy", None, "in"],
    "rainrate_mmax": [
        "Rain rate Month Max",
        "mm/h",
        "mdi:weather-pouring",
        None,
        "in/h",
    ],
    "rainrate_ymax": [
        "Rain rate Year Max",
        "mm/h",
        "mdi:weather-pouring",
        None,
        "in/h",
    ],
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> bool:
    """Set up the Meteobridge sensor platform."""
    coordinator = hass.data[MBDATA]["coordinator"]
    if not coordinator.data:
        return

    unit_system = "metric" if hass.config.units.is_metric else "imperial"
    name = slugify(hass.data[CONF_NAME])
    wind_unit = "m/s"

    sensors = []
    for sensor in SENSOR_TYPES:
        sensors.append(
            MeteobridgeSensor(coordinator, sensor, name, unit_system, wind_unit)
        )
        _LOGGER.debug(f"SENSOR ADDED: {sensor}")

    async_add_entities(sensors, True)


class MeteobridgeSensor(Entity):
    """ Implementation of a SmartWeather Weatherflow Current Sensor. """

    def __init__(self, coordinator, sensor, name, unit_system, wind_unit):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._sensor = sensor
        self._unit_system = unit_system
        self._wind_unit = wind_unit
        self._state = None
        self.entity_id = ENTITY_ID_SENSOR_FORMAT.format(self._sensor)
        self._name = SENSOR_TYPES[self._sensor][0]
        self._unique_id = ENTITY_UNIQUE_ID.format(slugify(self._name).replace(" ", "_"))

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
        if self._sensor in self.coordinator.data:
            if not (self.coordinator.data[self._sensor] is None):
                self._state = self.coordinator.data[self._sensor]
                if SENSOR_TYPES[self._sensor][1] == "m/s":
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
            SENSOR_TYPES[self._sensor][4] is None
        ):
            return SENSOR_TYPES[self._sensor][4]
        else:
            if SENSOR_TYPES[self._sensor][1] == "m/s":
                return (
                    "km/h"
                    if self._wind_unit == "kmh"
                    else SENSOR_TYPES[self._sensor][1]
                )
            else:
                return SENSOR_TYPES[self._sensor][1]

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._sensor][2]

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self._sensor][3]

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
