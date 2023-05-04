This package colorizes roads based on their suffix. (e.g., road, street, avenue, etc.) The map data is automatically downloaded from OpenStreetMap based on the provided coordinates. Below is a minimal example.
```python
    # Vancouver, BC
    rn = RoadNames()
    rn.load_box(lon_min=-123.29, lon_max=-123.00, lat_min=49.23, lat_max=49.37)
    rn.plot(filename='vancouver')
```

Vancouver, BC, Canada
![](png/vancouver.png)

San Francisco, California
![](png/sanfrancisco.png)

Kelowna, BC, Canada
![](png/kelowna.png)

Lexington, Kentucky
![](png/lexington.png)