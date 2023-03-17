from dataclasses import dataclass
from typing import Optional, List
from lxml import etree, builder
import xml.etree.cElementTree
import urllib.request
from tqdm import tqdm
import pandas as pd
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

    url = f'http://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox={url_suffix}]'

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

        # A place to store the way_ids and way_lonlat
        self.way_ids: List[List[int]] = []
        self.way_lonlat: List[pd.DataFrame] = []

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


def _xy_to_svg_d(
        x: np.ndarray,
        y: np.ndarray,
) -> str:
    """
    Convert x, y pixel coordinates to an SVG d string.
    """
    d = f'M {x[0]} {y[0]}'
    for ix, iy in zip(x[1:], y[1:]):
        d += f' L {ix} {iy}'
    return d


class RoadNames:
    def __init__(
            self,
            use_cache: bool = True,
    ):
        """
        RoadNames first takes a region (load_box) and then can plot it (plot).
        """
        self.bbox: Optional[BBox] = None
        self.use_cache = use_cache
        self.osm: Optional[bytes] = None
        self.xml: Optional[lxml.etree.Element] = None
        self.views: List[View] = []
        self.ways: List = []
        self.id_table: Optional[pd.DataFrame] = None
        self.width: Optional[Int] = None
        self.height: Optional[Int] = None
        self.filename: Optional[str] = None

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

        # Load the map data into memory
        self._read_osm()

        # Create a table of ids, lat and lon.
        self._create_id_lat_lon_table()

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
        self.cxml = xml.etree.cElementTree.fromstring(self.osm)

    def _create_id_lat_lon_table(self):
        """
        Each way consists of a list of IDs. These IDs correspond to nodes in the
        XML file. Create a table of IDs, lat, and lon to quickly convert IDs.
        """
        logging.debug('Creating id / lat / lon table.')

        # Walk the tree, and add all relevant id / lat / lon
        id_dict = {
            'id': [],
            'lon': [],
            'lat': [],
        }
        for child in tqdm(self.cxml.iter()):
            if child.tag == 'node':
                id_dict['id'].append(child.get('id'))
                id_dict['lon'].append(child.get('lon'))
                id_dict['lat'].append(child.get('lat'))

        # Make Pandas table
        dtypes = {'id': int, 'lon': float, 'lat': float}
        self.id_table = pd.DataFrame(id_dict)
        self.id_table = self.id_table.astype(dtypes)
        self.id_table.sort_values(by=['id'], inplace=True)
        self.id_table.set_index('id', inplace=True)

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

            # Find the Way elements that are relevant to the View, and add them.
            for way in self.ways:
                view.test_and_add_way(way)

            # Now that all the relevant Ways have been added, extract the IDs
            # of the relevant waypoints into a list of lists.
            for way in view.ways:
                way_ids = []
                for child in way.getchildren():
                    if child.tag == 'nd':
                        way_ids.append(int(child.get('ref')))
                view.way_ids.append(way_ids)

            # Look up these IDs and convert them to lon/lat pairs.
            for id_list in view.way_ids:
                view.way_lonlat.append(self.id_table.loc[id_list])

        # convert the lat, lon to a pixel position. Many of these values will
        # land outside the window range as they are a part of paths that pass
        # through the window.
        for view in self.views:
            for df in view.way_lonlat:
                df['x'] = (df['lon'] - self.bbox.lon_min) / self.bbox.lon_span * self.width
                y = (df['lat'] - self.bbox.lat_min) / self.bbox.lat_span * self.height
                df['y'] = self.height - y

    def _preprocess(
            self,
            width: int = 1000,
    ):
        """
        Once all the data and Views have been added, process the data in
        preparation for plotting.
        """

        # Store parameters
        self.width = width
        self.height = int(self.width * self.bbox.htw_ratio)

        # Select ways from the osm data
        self._select_ways()

        # Process the Views so that they contain the correct Ways
        self._process_views()

    def generate_views(
            self,
            count: int = 10,
    ):
        """
        Generate common views
        """
        highway_types = ['residential', 'tertiary']
        views = []
        for value in highway_types:
            tag = Tag(k='highway', v=value)
            views.append(View(true_tags=[tag]))
        self.load_views(views=views)

    def log_highway_types(self):
        types = {}
        for child in self.cxml.iter():
            if child.tag == 'way':
                for attrib in child.iter():
                    if attrib.tag != 'tag':
                        continue
                    if attrib.get('k') != 'highway':
                        continue
                    value = attrib.get('v')
                    if value in types.keys():
                        types[value] += 1
                    else:
                        types[value] = 1
        df = pd.DataFrame(data={'type': types.keys(), 'count': types.values()})
        df.sort_values(by=['count'], inplace=True, ascending=False)
        logging.debug(df)


    def plot(
            self,
            filename: str = 'default',
            width: int = 1000,
    ):
        """
        Create a plot of the defined BBox.
        """

        # Store attributes, and process data
        self.filename = filename

        # Process the passed data
        self._preprocess(width=width)

        # Generate SVG objects
        elements = builder.ElementMaker()
        svg = elements.svg
        path = elements.path
        rect = elements.rect

        # Create a document with a grey background
        # Create document with white background
        doc = svg(
            xmlns="http://www.w3.org/2000/svg",
            height=str(self.height),
            width=str(self.width),
        )
        doc.append(rect(
            x='0',
            y='0',
            width=str(self.width),
            height=str(self.height),
            fill='#ffffff',
        ))

        # Iterate through the views
        for view in self.views:

            # Iterate through the ways
            for df, way in zip(view.way_lonlat, view.ways):
                d = _xy_to_svg_d(
                    x=df['x'].to_numpy(),
                    y=df['y'].to_numpy(),
                )

                # Make path and append
                p = path(
                    d=d,
                    style='fill:none;stroke-width:1;stroke:rgb(0%,0%,0%);',
                )
                doc.append(p)

        # Save to disk
        if not os.path.exists('svg'):
            os.mkdir('svg')
        with open(f'svg/{self.filename}.svg', 'wb') as f:
            f.write(etree.tostring(doc, pretty_print=True))


if __name__ == '__main__':
    pass
