# SRTM

SRTM.py is a python parser for the Shuttle Radar Topography Mission elevation data.

See: http://www2.jpl.nasa.gov/srtm/.

## claim

This project is a portal project of https://github.com/tkrajina/srtm.py. This project
provide less functions than srtm.py, but it can use mmap to accelerate fetching data. And 
we assume you have srtm data already, not on network.

## Usage:
```python
from srtm import GeoElevation

filepath = '/filepath/'
elevation_data = GeoElevation(filepath, pre_load=True)

print('CGN Airport elevation (meters):',
    elevation_data.get_elevation(50.8682, 7.1377))

```

