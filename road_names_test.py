from road_names import RoadNames, BBox, View, Tag, _get_osm_file_cached
import unittest
import logging
import shutil
import os


logging.basicConfig(level=logging.DEBUG)

# Define a small area to use for testing
small_area = {
    'lon_min': -123.1565,
    'lon_max': -123.1381,
    'lat_min': 49.2721,
    'lat_max': 49.281,
}


class TestRoadNames(unittest.TestCase):

    def test_get_osm_file_cached(self):

        if os.path.exists('osm'):
            shutil.rmtree('osm')

        # Make BBox
        bbox = BBox(**small_area)

        # Test uncached
        _get_osm_file_cached(bbox=bbox)

        # Test cached
        _get_osm_file_cached(bbox=bbox)

    def test_load_box(self):

        rn = RoadNames()
        rn.load_box(**small_area)

    def test_load_views(self):
        rn = RoadNames()
        tag = Tag(k='surface', v='asphalt')
        view = View(true_tags=[tag])
        rn.load_views(views=[view])

    def test_preprocess(self):
        rn = RoadNames()
        rn.load_box(**small_area)
        tag = Tag(k='highway')
        view = View(true_tags=[tag])
        rn.load_views(views=[view])
        rn._preprocess()
        self.assertGreaterEqual(len(rn.views[0].ways), 10)
        self.assertLessEqual(len(rn.views[0].ways), 1000)