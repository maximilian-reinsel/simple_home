from astral import LocationInfo
from dataclasses import dataclass

# Todo - make configurable 
city = LocationInfo("Seattle", "Washington", "Pacific", 47.638029, -122.295042)
print((
    f"Information for {city.name}/{city.region}\n"
    f"Timezone: {city.timezone}\n"
    f"Latitude: {city.latitude:.02f}; Longitude: {city.longitude:.02f}\n"
))
print((
    f'Dawn:    {s["dawn"]}\n'
    f'Sunrise: {s["sunrise"]}\n'
    f'Noon:    {s["noon"]}\n'
    f'Sunset:  {s["sunset"]}\n'
    f'Dusk:    {s["dusk"]}\n'
))

@dataclass
class Location:
    name: str
    region: str
    timezone: str
    latitude: float
    longitude: float

