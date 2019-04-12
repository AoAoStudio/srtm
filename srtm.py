# -*- coding: utf-8 -*-

"""
SRTM.py is a python parser for the Shuttle Radar Topography Mission elevation data.

See: http://www2.jpl.nasa.gov/srtm/.

"""
import math
import mmap
import os
import re
import struct

ONE_DEGREE = 1000. * 10000.8 / 90.


def distance(latitude_1, longitude_1, latitude_2, longitude_2):
    """
    Distance between two points.
    """

    coef = math.cos(latitude_1 / 180. * math.pi)
    x = latitude_1 - latitude_2
    y = (longitude_1 - longitude_2) * coef

    return math.sqrt(x * x + y * y) * ONE_DEGREE


def get_color_between(color1, color2, i):
    """ i is a number between 0 and 1, if 0 then color1, if 1 color2, ... """
    if i <= 0:
        return color1
    if i >= 1:
        return color2
    return (int(color1[0] + (color2[0] - color1[0]) * i),
            int(color1[1] + (color2[1] - color1[1]) * i),
            int(color1[2] + (color2[2] - color1[2]) * i))


class GeoElevation(object):
    srtm_mmap = dict()

    def __init__(self, filepath, pre_load=False):
        """
        :param filepath: hgt file path
        :param pre_load: True to load hgt file when init , False to load hgt when used
        """
        if not os.path.exists(filepath):
            raise Exception('filepath not exist')

        self.pre_load = pre_load
        self.filepath = filepath

        if self.pre_load:
            for root, dirs, files in os.walk(filepath):
                for f in files:
                    file_path = os.path.join(root, f)
                    if os.path.exists(file_path):
                        m = mmap.mmap(os.open(file_path, os.O_RDWR), 0)
                        self.srtm_mmap[f] = m

    def get_elevation(self, latitude, longitude, approximate=None):
        """
        get elevation data from (latitude, longitude)
        :param latitude:
        :param longitude:
        :param approximate:
        :return:
        """
        geo_elevation_file = self.get_elevation_file(float(latitude), float(longitude))

        if not geo_elevation_file and self.pre_load:
            return None
        elif not self.pre_load:
            file_name = self.get_file_name(latitude, longitude)
            filepath = os.path.join(self.filepath, file_name)
            if os.path.exists(filepath):
                m = mmap.mmap(os.open(filepath, os.O_RDWR), 0)
                self.srtm_mmap[file_name] = m
                # in preload mode load srtm file data
                geo_elevation_file = self.get_elevation_file(float(latitude), float(longitude))
            else:
                return None

        return geo_elevation_file.get_elevation(
            float(latitude),
            float(longitude),
            approximate)

    def get_elevation_file(self, latitude, longitude):
        """
        get GeoElevationFile
        """
        file_name = self.get_file_name(latitude, longitude)

        if not file_name:
            return None

        data = self.srtm_mmap.get(file_name, None)
        if not data:
            return None

        result = GeoElevationFile(file_name, data, self)
        return result

    def get_file_name(self, latitude, longitude):
        """
        lon/lat -> srtm filename
        """
        if latitude >= 0:
            north_south = 'N'
        else:
            north_south = 'S'

        if longitude >= 0:
            east_west = 'E'
        else:
            east_west = 'W'

        file_name = '%s%s%s%s.hgt' % (north_south, str(int(abs(math.floor(latitude)))).zfill(2),
                                      east_west, str(int(abs(math.floor(longitude)))).zfill(3))
        if file_name not in self.srtm_mmap.keys():
            return None

        return file_name


class GeoElevationFile:
    """
    Contains data from a single Shuttle elevation file.

    This class should not be instantiated without its GeoElevationData because
    it may need elevations from nearby files.
    """

    file_name = None
    url = None

    latitude = None
    longitude = None

    data = None

    def __init__(self, file_name, data, geo_elevation_data):
        """ Data is a raw file contents of the file. """

        self.geo_elevation_data = geo_elevation_data
        self.file_name = file_name

        self.parse_file_name_starting_position()
        self.data = data

        square_side = math.sqrt(len(self.data) / 2.)
        assert square_side == int(square_side), 'Invalid file size: {0} for file {1}'.format(len(self.data),
                                                                                             self.file_name)

        self.square_side = int(square_side)

    def get_row_and_column(self, latitude, longitude):
        return math.floor((self.latitude + 1 - latitude) * float(self.square_side - 1)), \
               math.floor((longitude - self.longitude) * float(self.square_side - 1))

    def get_elevation(self, latitude, longitude, approximate=None):
        """
        If approximate is True then only the points from SRTM grid will be
        used, otherwise a basic aproximation of nearby points will be calculated.
        """
        if not (self.latitude <= latitude < self.latitude + 1):
            raise Exception('Invalid latitude %s for file %s' % (latitude, self.file_name))
        if not (self.longitude <= longitude < self.longitude + 1):
            raise Exception('Invalid longitude %s for file %s' % (longitude, self.file_name))

        row, column = self.get_row_and_column(latitude, longitude)

        if approximate:
            return self.approximation(latitude, longitude)
        else:
            return self.get_elevation_from_row_and_column(int(row), int(column))

    def approximation(self, latitude, longitude):
        """
        Dummy approximation with nearest points. The nearest the neighbour the
        more important will be its elevation.
        """
        d = 1. / self.square_side
        d_meters = d * ONE_DEGREE

        # Since the less the distance => the more important should be the
        # distance of the point, we'll use d-distance as importance coef
        # here:
        importance_1 = d_meters - distance(latitude + d, longitude, latitude, longitude)
        elevation_1 = self.geo_elevation_data.get_elevation(latitude + d, longitude, approximate=False)

        importance_2 = d_meters - distance(latitude - d, longitude, latitude, longitude)
        elevation_2 = self.geo_elevation_data.get_elevation(latitude - d, longitude, approximate=False)

        importance_3 = d_meters - distance(latitude, longitude + d, latitude, longitude)
        elevation_3 = self.geo_elevation_data.get_elevation(latitude, longitude + d, approximate=False)

        importance_4 = d_meters - distance(latitude, longitude - d, latitude, longitude)
        elevation_4 = self.geo_elevation_data.get_elevation(latitude, longitude - d, approximate=False)
        # TODO(TK) Check if coordinates inside the same file, and only the decide if to xall
        # self.geo_elevation_data.get_elevation or just self.get_elevation

        if elevation_1 == None or elevation_2 == None or elevation_3 == None or elevation_4 == None:
            elevation = self.get_elevation(latitude, longitude, approximate=False)
            if not elevation:
                return None
            elevation_1 = elevation_1 or elevation
            elevation_2 = elevation_2 or elevation
            elevation_3 = elevation_3 or elevation
            elevation_4 = elevation_4 or elevation

        # Normalize importance:
        sum_importances = float(importance_1 + importance_2 + importance_3 + importance_4)

        # Check normallization:
        assert abs(importance_1 / sum_importances + \
                   importance_2 / sum_importances + \
                   importance_3 / sum_importances + \
                   importance_4 / sum_importances - 1) < 0.000001

        result = importance_1 / sum_importances * elevation_1 + \
                 importance_2 / sum_importances * elevation_2 + \
                 importance_3 / sum_importances * elevation_3 + \
                 importance_4 / sum_importances * elevation_4

        return result

    def get_elevation_from_row_and_column(self, row, column):
        i = row * (self.square_side) + column
        assert i < len(self.data) - 1

        # mod_logging.debug('{0}, {1} -> {2}'.format(row, column, i))

        unpacked = struct.unpack(">h", self.data[i * 2: i * 2 + 2])
        result = None
        if unpacked and len(unpacked) == 1:
            result = unpacked[0]

        if (result is None) or result > 10000 or result < -1000:
            return None

        return result

    def parse_file_name_starting_position(self):
        """ Returns (latitude, longitude) of lower left point of the file """
        groups = re.findall('([NS])(\d+)([EW])(\d+)\.hgt', self.file_name)

        assert groups and len(groups) == 1 and len(groups[0]) == 4, 'Invalid file name {0}'.format(self.file_name)

        groups = groups[0]

        if groups[0] == 'N':
            latitude = float(groups[1])
        else:
            latitude = - float(groups[1])

        if groups[2] == 'E':
            longitude = float(groups[3])
        else:
            longitude = - float(groups[3])

        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return '[{0}:{1}]'.format(self.__class__, self.file_name)
