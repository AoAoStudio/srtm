# -*- coding: utf-8 -*-

import unittest
from srtm import GeoElevation


class SRTMTests(unittest.TestCase):

    def setUp(self) -> None:
        self.srtm = GeoElevation('test_files', pre_load=True)

    def test_dead_sea(self):
        self.assertEqual(759, self.srtm.get_elevation(44.1, -71.1))

    def test_point_with_invalid_elevation(self):
        self.assertEqual(None, self.srtm.get_elevation(47.0, 13.07))

    def test_invalit_coordinates_for_file(self):

        try:
            self.assertFalse(self.srtm.get_elevation(1, 1))
        except Exception as e:
            message = str(e)
            self.assertEqual('Invalid latitude 1 for file N47E013.hgt', message)

        try:
            self.assertFalse(self.srtm.get_elevation(47, 1))
        except Exception as e:
            message = str(e)
            self.assertEqual('Invalid longitude 1 for file N47E013.hgt', message)

    def test_invalid_file(self):
        geo_file = self.srtm.get_elevation_file(44.1, 191.1)
        self.assertEqual(None, geo_file)

    def test_coordinates_in_file(self):
        geo_file = self.srtm.get_elevation_file(44.1, -71.1)

        self.assertEqual(geo_file.get_elevation(44.1, -71.1),
                         geo_file.get_elevation(44.1, -71.1))

    def test_without_approximation(self):
        self.assertEqual(self.srtm.get_elevation(44.1, -71.1, approximate=False),
                         self.srtm.get_elevation(44.1, -71.1))

        # SRTM elevations are always integers:
        elevation = self.srtm.get_elevation(44.1, -71.1)
        self.assertTrue(int(elevation) == elevation)

    def test_with_approximation(self):
        self.assertNotEqual(self.srtm.get_elevation(44.1, -71.1, approximate=True),
                            self.srtm.get_elevation(44.1, -71.1))

        # When approximating a random point, it probably won't be a integer:
        elevation = self.srtm.get_elevation(44.1, -71.1, approximate=True)
        self.assertTrue(int(elevation) != elevation)

    def test_approximation(self):
        # TODO(TK) Better tests for approximation here:
        elevation_without_approximation = self.srtm.get_elevation(44.1, -71.1)
        elevation_with_approximation = self.srtm.get_elevation(44.1, -71.1, approximate=True)

        self.assertNotEqual(elevation_with_approximation, elevation_without_approximation)
        self.assertTrue(abs(elevation_with_approximation - elevation_without_approximation) < 30)


if __name__ == '__main__':
    unittest.main()
