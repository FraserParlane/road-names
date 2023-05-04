"""
Plot roads of Vancouver, BC, colored by road suffix.
Fraser Parlane 20230504
"""
from road_names import RoadNames
import logging

# Set log level
logging.basicConfig(level=logging.DEBUG)


def run():
    """Plot road names."""

    logging.debug('\n\nVancouver, BC')
    rn = RoadNames()
    # rn.load_box(lon_min=-123.16, lon_max=-123.14, lat_min=49.27, lat_max=49.28)  # Small
    rn.load_box(lon_min=-123.29, lon_max=-123.00, lat_min=49.23, lat_max=49.37)
    rn.plot(filename='vancouver', legend_x=0.05, legend_y=0.3)

    logging.debug('\n\nKelowna, BC')
    rn = RoadNames()
    rn.load_box(lon_min=-119.65, lon_max=-119.34, lat_min=49.77, lat_max=49.98)
    rn.plot(filename='kelowna', legend_x=0.05, legend_y=0.05)

    logging.debug('\n\nLexington, Kentucky')
    rn = RoadNames()
    rn.load_box(lon_min=-84.65, lon_max=-84.35, lat_min=37.93, lat_max=38.13)
    rn.plot(filename='lexington', legend_x=0.05, legend_y=0.05)

    logging.debug('\n\nSan Francisco, California')
    rn = RoadNames()
    rn.load_box(lon_min=-122.63, lon_max=-122.24, lat_min=37.56, lat_max=37.91)
    rn.plot(filename='sanfrancisco', legend_x=0.05, legend_y=0.05)

    logging.debug('\n\nNew York, New York')
    rn = RoadNames()
    rn.load_box(lon_min=-74.04, lon_max=-73.82, lat_min=40.68, lat_max=40.87)
    rn.plot(filename='newyork', legend_x=0.05, legend_y=0.05)


if __name__ == '__main__':
    run()
