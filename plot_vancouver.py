"""
Plot roads of Vancouver, BC, colored by road suffix.
Fraser Parlane 20230504
"""
from road_names import RoadNames


def run():
    """Plot road names."""

    # Define a small area to use for testing
    small_area = {
        'lon_min': -123.1565,
        'lon_max': -123.1381,
        'lat_min': 49.2721,
        'lat_max': 49.281,
    }

    sm_area = {
        'lon_min': -123.1565,
        'lon_max': -123.1381,
        'lat_min': 49.25,
        'lat_max': 49.281,
    }

    med_area = {
        'lon_min': -123.27,
        'lon_max': -123.13,
        'lat_min': 49.23,
        'lat_max': 49.28,
    }

    large_area = {
        'lon_min': -123.2901,
        'lon_max': -123.0007,
        'lat_min': 49.2296,
        'lat_max': 49.3692,
    }

    rn = RoadNames()
    rn.load_box(**small_area)
    # rn.load_box(**sm_area)
    # rn.load_box(**med_area)
    # rn.load_box(**large_area)
    rn.generate_views()
    rn.plot(
        filename='vancouver',
    )


if __name__ == '__main__':
    run()
