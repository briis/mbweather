# Meteobridge Weather for Home Assistant
This a *Custom Integration* for [Home Assistant](https://www.home-assistant.io/). It combines real-time weather readings from a Meteobridge Weather Logger and Forecast data from *Dark Sky*.

[*Meteobridge*](https://www.meteobridge.com/wiki/index.php/Home) is a small device that connects your personal weather station to public weather networks like "Weather Underground". This allows you to feed your micro climate data to a weather network in the Internet and to have it there visible from wherever you are. Meteobridge also has many ways of delivering data to your local network, and this furthermore reduces the dependencies for Cloud Services when you need very local Weather Data.<br>
Meteobridge can be delivered as complete HW and SW packages, or there is a SW solution that you then can install yourself on specific HW.<br>
If you have any Davis Weatherstation I would recommend the Meteobridge Nano SD solution or else the Meteobridge PRO solution. 

This Custom Integration consist of 4 parts:
1. The main component which sets up the link to the Meteobridge Data Logger
2. A *Binary Sensor* component, that gives a couple of binary sensors, derived from the data delivered
3. A *Sensor* component delivering realtime data from the Data Logger
4. A Home Assistant *Weather* component, that retrieves Forecast data from *Dark Sky* and then replaces Dark Skys currwent data with the data from the local weatherstation

The `mbweather` component uses a built-in REST API from Meteobridge to retrieve current data for a local WeatherStation, which means that if you don't use the *Weather* component, everything is running inside your local network

## Manual Installation
To add MBWEATHER to your installation, create this folder structure in your /config directory:

“custom_components/mbweather.
Then, drop the following files into that folder:

```yaml
__init__.py
manifest.json
sensor.py
binary_sensor.py
weather.py
```

## HACS Installation
This Integration is not yet part of the default HACS store, but you can add it manually by going to `Settings` in HACS and then add `briis/mbweather` as an `Integration`.

**Page is being updated - Files are comming soon**
