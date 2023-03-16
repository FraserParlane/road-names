from road_names import RoadNames, _get_osm_file_cached
import unittest
import logging
import shutil
import os


logging.basicConfig(level=logging.DEBUG)


class TestRoadNames(unittest.TestCase):

    def test_get_osm_file_cached(self):

        if os.path.exists('osm'):
            shutil.rmtree('osm')

        # Test uncached
        _get_osm_file_cached(
            min_lon=-123.1565,
            max_lon=-123.1381,
            min_lat=49.2721,
            max_lat=49.281,
        )

        # Test cached
        _get_osm_file_cached(
            min_lon=-123.1565,
            max_lon=-123.1381,
            min_lat=49.2721,
            max_lat=49.281,
        )
