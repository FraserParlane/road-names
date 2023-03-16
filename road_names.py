from dataclasses import dataclass
from typing import Optional, List
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
        """
        Defines a bounding box to plot. Math is performed on these bounds for
        plotting purposes.
        """

        # Create standardized strings of lat, lon
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
    filename = f'map_{bbox.id}.osm'
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
    filepath = f'osm/map_{bbox.id}.osm'
    logging.debug(f'Downloading {url}')
    urllib.request.urlretrieve(url, filepath)


@dataclass
class Tag:
    """
    A Tag describes a way of selecting objects from the OSM XML file. Tags are
    used to create Views.
    """
    k: str
    v: Optional[str] = None


def _way_has_tag(
        way,
        tag: Tag,
) -> bool:
    """
    Check if a Way element has a Tag
    """

    # Check for tag in each child
    for child in way.getchildren():
        if child.tag != 'tag':
            continue
        if child.get('k') != tag.k:
            continue
        if tag.v is not None and child.get('v') != tag.v:
            continue
        return True

    # If not found, return False
    return False


def _way_has_tags(
        way,
        tags: List[Tag],
) -> bool:
    """
    Check if a Way element has a Tag
    """
    for tag in tags:
        if not _way_has_tag(way, tag):
            return False
    return True


def _way_not_has_tags(
        way,
        tags: List[Tag],
) -> bool:
    """
    Check if a Way element has none of the listed tags
    :param way: The Way to check for a Tag
    :param tags: The Tags to look for
    :return: bool
    """
    for tag in tags:
        if _way_has_tag(way, tag):
            return False
    return True


@dataclass
class View:
    """
    A View is used to select objects from the OSM XML file. A View is defined by
    a series of Tags that must be True or False.
    """
    true_tags: Optional[List[Tag]] = None
    false_tags: Optional[List[Tag]] = None

    def __post_init__(self):
        # These ways are valid for this View
        self.ways = []
        if self.true_tags is None:
            self.true_tags = []
        if self.false_tags is None:
            self.false_tags = []

    def test_and_add_way(
            self,
            way,
    ) -> None:
        """
        Test if a Way meets the criteria for this View. If so, add it.
        """
        if not _way_has_tags(way, self.true_tags):
            return None
        if not _way_not_has_tags(way, self.false_tags):
            return None
        self.ways.append(way)


class RoadNames:
    def __init__(
            self,
            use_cache: bool = True
    ):
        """
        RoadNames first takes a region (load_box) and then can plot it (plot).
        """
        self.bbox: Optional[BBox] = None
        self.use_cache = use_cache
        self.osm: Optional[bytes] = None
        self.xml: Optional[lxml.etree._Element] = None
        self.views: List[View] = []
        self.ways: List = []

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

    def load_views(
            self,
            views: List[View]
    ):
        """
        Provide a list of views to visualize.
        """
        self.views += list(views)

    def _read_osm(self):
        """
        Load the OSM file into memory. Convert into an XML for parsing.
        """
        # Load OSM
        self.osm = _get_osm_file_cached(bbox=self.bbox)

        # Convert to XML
        logging.debug('Converting OSM to XML.')
        self.xml = etree.fromstring(self.osm)

    def _select_ways(self):
        """
        the OSM tree contains several object types. We are only interested in
        the objects labelled way. Isolate these for easy iteration.
        """
        logging.debug('Selecting way objects from XML.')
        for child in self.xml.getchildren():
            if child.tag == 'way':
                self.ways.append(child)

    def _process_views(self):
        """
        For each of the views, add the relevant Ways.
        """

        logging.debug('Processing views.')
        for view in tqdm(self.views):
            for way in self.ways:
                view.test_and_add_way(way)

    def _preprocess(self):
        """
        Once all the data and Views have been added, process the data in
        preparation for plotting.
        """

        # Load the map data into memory
        self._read_osm()

        # Select ways from the osm data
        self._select_ways()

        # Process the Views so that they contain the correct Ways
        self._process_views()

    def plot(
            self,
            filename: str = 'default',
    ):
        """
        Create a plot of the defined BBox.
        """
        self._preprocess()


if __name__ == '__main__':
    pass
