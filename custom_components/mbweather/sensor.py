"""
    Support for the Meteobridge SmartEmbed
    This component will read the local weatherstation data
    and create sensors for each type.

    For a full description, go here: https://github.com/briis/mbweather

    Author: Bjarne Riis
"""
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA
from homeassistant.const import (ATTR_ATTRIBUTION, CONF_MONITORED_CONDITIONS,
                                 CONF_NAME, DEVICE_CLASS_HUMIDITY,
                                 DEVICE_CLASS_ILLUMINANCE,
                                 DEVICE_CLASS_PRESSURE,
                                 DEVICE_CLASS_TEMPERATURE, LENGTH_METERS,
                                 TEMP_CELSIUS, UNIT_UV_INDEX)
from homeassistant.helpers.entity import Entity, generate_entity_id

from . import ATTRIBUTION, MBDATA

DEPENDENCIES = ['mbweather']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mbweather'
CONF_WIND_UNIT = 'wind_unit'

ATTR_UPDATED = 'updated'

SENSOR_TYPES = {
    'temperature': ['Temperature', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'temphigh': ['Temp High Today', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'templow': ['Temp Low Today', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'in_temperature': ['Indoor Temp', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'dewpoint': ['Dewpoint', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'windchill': ['Wind Chill', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'heatindex': ['Heatindex', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'feels_like': ['Feels Like', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE, None],
    'windspeedavg': ['Wind Speed Avg', 'm/s', 'mdi:weather-windy', None, 'mph'],
    'windspeed': ['Wind Speed', 'm/s', 'mdi:weather-windy', None, 'mph'],
    'windbearing': ['Wind Bearing', '°', 'mdi:compass-outline', None, None],
    'winddirection': ['Wind Direction', '', 'mdi:compass-outline', None, None],
    'windgust': ['Wind Gust', 'm/s', 'mdi:weather-windy', None, 'mph'],
    'raintoday': ['Rain today', 'mm', 'mdi:weather-rainy', None, 'in'],
    'rainrate': ['Rain rate', 'mm/h', 'mdi:weather-pouring', None, 'in/h'],
    'humidity': ['Humidity', '%', 'mdi:water-percent', DEVICE_CLASS_HUMIDITY, None],
    'in_humidity': ['Indoor Hum', '%', 'mdi:water-percent', DEVICE_CLASS_HUMIDITY, None],
    'pressure': ['Pressure', 'hPa', 'mdi:gauge', DEVICE_CLASS_PRESSURE, 'inHg'],
    'condition': ['Condition', '', 'mdi:text-short', None, None],
    'forecast': ['Forecast', '', 'mdi:text-short', None, None]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_WIND_UNIT, default='ms'): cv.string,
    vol.Optional(CONF_NAME, default=DOMAIN): cv.string
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the SmartWeather sensor platform."""
    unit_system = 'metric' if hass.config.units.is_metric else 'imperial'

    name = config.get(CONF_NAME)
    data = hass.data[MBDATA]
    wind_unit = config.get(CONF_WIND_UNIT)

    if data.data['time'] is None:
        return

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(MBWeatherSensor(hass, data, variable, name, unit_system, wind_unit))

    add_entities(sensors, True)

class MBWeatherSensor(Entity):
    """ Implementation of a SmartWeather Weatherflow Current Sensor. """

    def __init__(self, hass, data, condition, name, unit_system, wind_unit):
        """Initialize the sensor."""
        self._condition = condition
        self._unit_system = unit_system
        self._wind_unit = wind_unit
        self.data = data
        self._name = SENSOR_TYPES[self._condition][0]
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, '{} {}'.format('mbw', SENSOR_TYPES[self._condition][0]), hass=hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug("Sensor: %s",self._condition)
        if self._condition == 'condition':
            if (not 'condition' in self.data.data):
                return 'Requires Weather Component'

        if self._condition in self.data.data:
            variable = self.data.data[self._condition]

            if not (variable is None):
                if SENSOR_TYPES[self._condition][1] == 'm/s':
                    return round(variable*3.6,1) \
                        if self._wind_unit == 'kmh' \
                        else variable
                else:
                    return variable
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._unit_system == 'imperial' and not (SENSOR_TYPES[self._condition][4] is None):
            return SENSOR_TYPES[self._condition][4]
        else:
            if SENSOR_TYPES[self._condition][1] == 'm/s':
                return 'km/h' \
                    if self._wind_unit == 'kmh' \
                    else SENSOR_TYPES[self._condition][1]
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
        attr[ATTR_ATTRIBUTION] = ATTRIBUTION
        attr[ATTR_UPDATED] = self.data.data['time']

        return attr

    def update(self):
        """Update current conditions."""
        self.data.update()
