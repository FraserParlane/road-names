import urllib.request
from tqdm import tqdm
import logging
import os


def _get_osm_file_cached(
        min_lon: float,
        max_lon: float,
        min_lat: float,
        max_lat: float,
) -> bytes:
    """
    Get an OSM file from OpenStreetMaps for the given bounding box. If already
    downloaded, return cached file.
    """

    # Convert the floats to standardized strings
    min_lon_str = f'{min_lon:.4f}'
    max_lon_str = f'{max_lon:.4f}'
    min_lat_str = f'{min_lat:.4f}'
    max_lat_str = f'{max_lat:.4f}'

    # Check if file already exists
    filename = f'{min_lon_str}_{max_lon_str}_{min_lat_str}_{max_lat_str}.osm'
    filepath = f'osm/{filename}'
    if os.path.isfile(filepath):
        logging.debug(f'Cached file exists: {filepath}')
    else:
        logging.debug(f'Cached file {filepath} does not exist.')
        _get_osm_file(
            min_lon_str=min_lon_str,
            max_lon_str=max_lon_str,
            min_lat_str=min_lat_str,
            max_lat_str=max_lat_str,
            filepath=filepath,
        )

    # Load and return
    with open(filepath, 'rb') as f:
        file = f.read()
    return file


def _get_osm_file(
        min_lon_str: str,
        max_lon_str: str,
        min_lat_str: str,
        max_lat_str: str,
        filepath: str,
) -> None:
    """
    Download an OSM file from OpenStreetMaps for the given bounding box.
    """

    # Create osm folder
    if not os.path.exists('osm'):
        os.makedirs('osm')

    # Download data
    url_suffix = f'{min_lon_str},{min_lat_str},{max_lon_str},{max_lat_str}'
    url = f'https://api.openstreetmap.org/api/0.6/map?bbox={url_suffix}'
    logging.debug(f'Downloading {url}')
    urllib.request.urlretrieve(url, filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
