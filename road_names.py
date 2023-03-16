from dataclasses import dataclass
from typing import Optional
from lxml import etree
import urllib.request
from tqdm import tqdm
import numpy as np
import logging
import os


@dataclass
class BBox:
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    def __post_init__(self):
        self.lon_min_str = f'{self.lon_min:.4f}'
        self.lon_max_str = f'{self.lon_max:.4f}'
        self.lat_min_str = f'{self.lat_min:.4f}'
        self.lat_max_str = f'{self.lat_max:.4f}'
        self.id = f'{self.lon_min_str}_{self.lon_max_str}_{self.lat_min_str}_{self.lat_max_str}'

        # Calculate map scaling values
        self.lon_mid = (self.lon_min + self.lon_max) / 2
        self.lat_mid = (self.lat_min + self.lat_max) / 2
        self.lon_span = self.lon_max - self.lon_min
        self.lat_span = self.lat_max - self.lat_min
        self.lon_scale = np.cos(self.lat_mid * np.pi / 180)
        self.htw_ratio = self.lat_span / (self.lon_span * self.lon_scale)


def _get_osm_file_cached(
        bbox: BBox,
        use_cache: bool = True,
) -> bytes:
    """
    Get an OSM file from OpenStreetMaps for the given bounding box. If already
    downloaded, return cached file.
    """

    # Check if file already exists
    filename = f'{bbox.id}.osm'
    filepath = f'osm/{filename}'
    cache_available = True
    if use_cache:
        logging.debug('Cached being used.')
        if os.path.isfile(filepath):
            logging.debug(f'Cached file exists: {filepath}')
        else:
            logging.debug(f'Cached file {filepath} does not exist.')
            cache_available = False
    else:
        cache_available = False

    if not cache_available:
        _get_osm_file(bbox=bbox)

    # Load and return
    with open(filepath, 'rb') as f:
        file = f.read()
    return file


def _get_osm_file(
        bbox: BBox,
) -> None:
    """
    Download an OSM file from OpenStreetMaps for the given bounding box.
    """

    # Create osm folder
    if not os.path.exists('osm'):
        os.makedirs('osm')

    # Download data
    url_suffix = f'{bbox.lon_min_str},{bbox.lat_min_str},{bbox.lon_max_str},{bbox.lat_max_str}'
    url = f'https://api.openstreetmap.org/api/0.6/map?bbox={url_suffix}'
    filepath = f'osm/{bbox.id}.osm'
    logging.debug(f'Downloading {url}')
    urllib.request.urlretrieve(url, filepath)


class RoadNames:
    def __init__(
            self,
            use_cache: bool = True
    ):
        self.bbox: Optional[BBox] = None
        self.use_cache = use_cache
        self.osm: Optional[bytes] = None
        self.xml: Optional[lxml.etree._Element] = None

    def load_box(
            self,
            lon_min: float,
            lon_max: float,
            lat_min: float,
            lat_max: float,
    ) -> None:
        """
        Define the plotting area with a bounding box of lon, lat.
        """
        self.bbox = BBox(
            lon_min=lon_min,
            lon_max=lon_max,
            lat_min=lat_min,
            lat_max=lat_max,
        )

    def _read_osm(self):
        """
        Load the OSM file into memory.
        """
        # Load OSM
        self.osm = _get_osm_file_cached(bbox=self.bbox)

        # Convert to XML
        logging.debug('Converting OSM to XML.')
        self.xml = etree.fromstring(self.osm)

    def plot(
            self,
            filename: str = 'default',
    ):

        # Load the data
        self._read_osm()


if __name__ == '__main__':
    pass
