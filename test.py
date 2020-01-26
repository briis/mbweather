import json
import time
from meteobridge import meteobridge

mb = meteobridge("192.168.1.5", "meteobridge", "Ry8jRGMVobk", False, "metric")
sensors = mb.sensors
print(json.dumps(sensors, indent=1))
time.sleep(3)
print("NEW CALL\n")
mb.update()
sensors = mb.sensors
print(json.dumps(sensors, indent=1))
