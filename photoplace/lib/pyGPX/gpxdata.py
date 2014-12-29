#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright 2010-2015 Jose Riguera Lopez <jriguera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
Main implementation for GPX package.
"""
__package_name__ = "gpx"
__package_revision__ = '0'
__package_version__ = '0.1.1'
__package_released__ = "Dec 2014"
__package_author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__package_license__ = "Apache 2.0"
__package_copyright__ ="(c) Jose Riguera"


import time
import datetime

__GPX_version__ = "1.1"
__GPX_creator__ = "GPX4PhotoPlace"


import os.path
import gettext
import locale

__GETTEXT_DOMAIN__ = "pygpx"
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)


import exceptions
import geomath



# #############################
# GPX point Type implementation
# #############################

class GPXItem(object):
    """
    Base class for GPX components

    """

    def __cmp__(self, wpt):
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass



# #############################
# GPX point Type implementation
# #############################

class GPXPoint(GPXItem):
    """
    Base class for GPX points

    """
    def __init__(self, lat, lon, ele=0.0, time=datetime.datetime.utcnow(), attr={}):
        """
        GPX Point (trackpoint/waypoint) class constructor

        :Parameters:
            -`lat`: The latitude of the point. Decimal degrees, WGS84 datum.
            -`lon`: The longitude of the point. Decimal degrees, WGS84 datum.
            -`ele`: Elevation of the point. Meters.
            -`time`: Time (UTC data).
            -`attr`: Dictionary type with other data
        """
        if lat < -90.0 or lat > 90.0:
            raise ValueError(_("latitude = '%d', not in [-90.0..90.0] range") % (lat))
        if lon < -180.0 or lon > 180.0:
            raise ValueError(_("longitude = '%d', not in [-180.0..180.0] range") % (lon))
        if not isinstance(time, datetime.datetime):
            dgettext = dict()
            dgettext['type_expected'] = datetime.datetime.__name__
            dgettext['type_got'] = time.__class__.__name__
            msg = _("Time type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        self.time = time
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.attr = attr
        self.status = 1


    def __cmp__(self, wpt):
        return self.equals(wpt, True, False)


    def __repr__(self):
        return "<(%.8f, %.8f, %.8f, %s) %s>" % \
        (self.lat, self.lon, self.ele, self.time, self.attr)


    def __str__(self):
        return "GPXPoint lat=%.8f, lon=%.8f, ele=%.8f, time=%s \n\tattr=%s" % \
        (self.lat, self.lon, self.ele, self.time, self.attr)


    def equals(self, wpt, samele=True, ontime=False):
        same_time = same_ele = True
        if self.lat == wpt.lat:
            if self.lon == wpt.lon:
                if samele:
                    if self.ele != wpt.ele:
                        same_ele = False
                if ontime:
                    if not self.time == wpt.time:
                        same_time = False
                return same_time & same_ele
        return False


    def distance(self, argv1, argv2=''):
        if isinstance(argv1, GPXPoint):
            lat = argv1.lat
            lon = argv1.lon
        else:
            if not isinstance(argv1, float):
                dgettext = {'type_expected': float.__name__, 'type_got': argv1.__class__.__name__}
                msg = _("Latitude type excepted '%(type_expected)s', got '%(type_got)s' instead")
                raise TypeError(msg % dgettext)
            if not isinstance(argv2, float):
                dgettext = {'type_expected': float.__name__, 'type_got': argv2.__class__.__name__}
                msg = _("Longitude type excepted '%(type_expected)s', got '%(type_got)s' instead")
                raise TypeError(msg % dgettext)
            if argv1 < -90.0 or argv1 > 90.0:
                raise ValueError(_("latitude = '%d', not in [-90.0..90.0] range") % (argv1))
            if argv2 < -180.0 or argv2 > 180.0:
                raise ValueError(_("longitude = '%d', not in [-180.0..180.0] range") % (argv2))
            lat = argv1
            lon = argv2
        return geomath.distanceCoord(self.lat, self.lon, lat, lon)


    def bearing(self, argv1, argv2=''):
        if isinstance(argv1, GPXPoint):
            lat = argv1.lat
            lon = argv1.lon
        else:
            if not isinstance(argv1, float):
                dgettext = {'type_expected': float.__name__, 'type_got': argv1.__class__.__name__}
                msg = _("Latitude type excepted '%(type_expected)s', got '%(type_got)s' instead")
                raise TypeError(msg % dgettext)
            if not isinstance(argv2, float):
                dgettext = {'type_expected': float.__name__, 'type_got': argv2.__class__.__name__}
                msg = _("Longitude type excepted '%(type_expected)s', got '%(type_got)s' instead")
                raise TypeError(msg % dgettext)
            if argv1 < -90.0 or argv1 > 90.0:
                raise ValueError(_("latitude = '%d', not in [-90.0..90.0] range") % (argv1))
            if argv2 < -180.0 or argv2 > 180.0:
                raise ValueError(_("longitude = '%d', not in [-180.0..180.0] range") % (argv2))
            lat = argv1
            lon = argv2
        return geomath.bearingCoord(self.lat, self.lon, lat, lon)


# ###############################
# GPX Segment Type implementation
# ###############################

class GPXSegment(GPXItem):
    """
    Base class for GPX track segments
    """
    def __init__(self, name, attr={}, lwpts=[]):
        """GPX Track Seg class constructor

        :Parameters:
            -`name`: identifier for this track segment.
            -`attr`: Dictionary type with other data.
            -`lwpts`: List of points.
        """
        self.name = name
        self.attr = attr
        self.lwpts = []
        for wpt in lwpts:
            self.addPoint(wpt)


    def __repr__(self):
        return "[%s attr=%s: %s]" % (self.name, self.attr, self.lwpts)


    def __str__(self):
        return "GPXSegment name=%s, attr=%s :\n\t%s" % (self.name, self.attr, self.lwpts)


    def addPoint(self, wpt):
        if not isinstance(wpt, GPXPoint):
            dgettext = {'type_expected': GPXPoint.__name__, 'type_got': wpt.__class__.__name__}
            msg = _("Point type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        pos = 0
        num_points = len(self.lwpts)
        if num_points < 1:
            self.lwpts.append(wpt)
        else:
            if wpt.time > self.lwpts[num_points - 1].time:
                self.lwpts.append(wpt)
                pos = num_points
            else:
                for pos in xrange(0, num_points):
                    if wpt.time < self.lwpts[pos].time:
                        self.lwpts.insert(pos, wpt)
                        break
        return pos


    def delPoint(self, pos):
        if pos >= 0 and pos < len(self.lwpts):
            del self.lwpts[pos]
        else:
            raise exceptions.GPXErrorSegment(_("Cannot delete point at pos %s!") % pos)


    def position(self, wpt):
        if not isinstance(wpt, GPXPoint):
            dgettext = {'type_expected': GPXPoint.__name__, 'type_got': wpt.__class__.__name__}
            msg = _("Point type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        num_points = len(self.lwpts)
        for pos in xrange(0, num_points - 1):
            point = self.lwpts[pos]
            if wpt == point:
                return pos
        return -1


    # Perfecto!, funciona por diferencias!!
    def closest(self, time):
        if time < self.lwpts[0].time:
            return self.lwpts[0]
        last = len(self.lwpts) - 1
        if time > self.lwpts[last].time:
            return self.lwpts[last]
        pdiff = datetime.timedelta.max
        for pos in xrange(0, last):
            point = self.lwpts[pos]
            diff = abs(point.time - time)
            if diff > pdiff:
                return self.lwpts[pos - 1]
            pdiff = diff
        # with only one point
        return self.lwpts[0]


    def nearestPointDistance(self, lat, lon):
        min_distance = geomath.MaxDistanceEarth
        nearest = None
        for point in self.lwpts:
            distance = point.distance(lat, lon)
            if distance < min_distance :
                min_distance = distance
                nearest = point
        return (nearest, min_distance)


    def length(self):
        total_distance = 0
        num_points = len(self.lwpts)
        if num_points > 1:
            pos = 1
            while pos <= num_points - 1 :
                point = self.lwpts[pos]
                prev_point = self.lwpts[pos - 1]
                total_distance += point.distance(prev_point)
                pos = pos + 1
        return total_distance


    def coordMinMax(self):
        max_lat = -90.0
        min_lat = 90.0
        max_lon = -180.0
        min_lon = 180.0
        if len(self.lwpts) > 0:
            for point in self.lwpts:
                if point.lat > max_lat:
                    max_lat = point.lat
                if point.lat < min_lat:
                    min_lat = point.lat
                if point.lon > max_lon:
                    max_lon = point.lon
                if point.lon < min_lon:
                    min_lon = point.lon
        return ((min_lat, min_lon), (max_lat, max_lon))


    def elevationMinMax(self):
        max_ele = -12000.0
        min_ele = 9000.0
        if len(self.lwpts) > 0:
            for point in self.lwpts:
                if point.ele > max_ele:
                    max_ele = point.ele
                if point.ele < min_ele:
                    min_ele = point.ele
        return (min_ele, max_ele)


    def timeMinMax(self):
        num_points = len(self.lwpts)
        min_date = datetime.datetime.max
        max_date = datetime.datetime.min
        if num_points > 0:
            min_date = self.lwpts[0].time
            max_date = self.lwpts[num_points - 1].time
        return (min_date, max_date)


    def speedMinAvgMax(self):
        total_distance = 0.0
        min_speed = 0.0
        max_speed = 0.0
        avg_speed = 0.0
        num_points = len(self.lwpts)
        if num_points > 1:
            pos = 1
            while pos <= num_points - 1:
                point = self.lwpts[pos]
                prev_point = self.lwpts[pos - 1]
                distance = point.distance(prev_point)
                total_distance = total_distance + distance
                diff_time = point.time - prev_point.time
                t = diff_time.seconds * 1000000 + diff_time.microseconds
                speed = (float(distance) / float(t)) * 1000000
                if pos == 1:
                    min_speed = speed
                    max_speed = speed
                if speed > max_speed:
                    max_speed = speed
                if speed < min_speed:
                    min_speed = speed
                pos = pos + 1
            min_date = self.lwpts[0].time
            max_date = self.lwpts[num_points - 1].time
            diff_time = max_date - min_date
            t = diff_time.seconds * 1000000 + diff_time.microseconds
            avg_speed = (float(total_distance) / float(t)) * 1000000
        return (min_speed, avg_speed, max_speed)


# #############################
# GPX Track Type implementation
# #############################

class GPXTrack(GPXItem):
    """
    Base class for GPX Traks
    """

    def __init__(self, name, desc='', attr={}):
        """
        GPX Trk (Track) class constructor

        :Parameters:
            -`name`: Name for the point
            -`desc`: Description.
            -`attr`: Dictionary type with other data
        """
        self.name = name
        self.desc = desc
        self.attr = attr
        self.ltrkseg = []
        self.status = 1


    def __repr__(self):
        return "(Track=%s, desc=%s, atrr=%s TrackSegs=%s)" % \
        (self.name, self.desc, self.attr, self.ltrkseg)


    def __str__(self):
        return "Track name=%s, desc=%s, attr=%s \n\tTrackSegs=%s" % \
        (self.name, self.desc, self.attr, self.ltrkseg)


    def addSegment(self, trkseg):
        if not isinstance(trkseg, GPXSegment):
            dgettext = {'type_expected': GPXSegment.__name__, 'type_got': trkseg.__class__.__name__}
            msg = _("Segment type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        if len(trkseg.lwpts) < 1:
            raise exceptions.GPXErrorTrack(_("Segment empty!"))
        num_seg = len(self.ltrkseg)
        pos = 0
        if num_seg < 1:
            self.ltrkseg.append(trkseg)
        else:
            datein = trkseg.lwpts[0].time
            # in > last -> append
            if datein > self.ltrkseg[num_seg - 1].lwpts[0].time:
                self.ltrkseg.append(trkseg)
                pos = num_seg
            # find correct position
            else:
                for pos in xrange(0, num_seg):
                    if datein < self.ltrkseg[pos].lwpts[0].time:
                        self.ltrkseg.insert(pos, trkseg)
                        break
        return pos


    def delSegment(self, pos):
        if pos >= 0 and pos < len(self.ltrkseg):
            del self.ltrkseg[pos]
        else:
            raise exceptions.GPXErrorTrack(_("Cannot delete segment at pos %s!") % pos)


    def position(self, trkseg):
        if not isinstance(trkseg, GPXSegment):
            dgettext = {'type_expected': GPXSegment.__name__, 'type_got': trkseg.__class__.__name__}
            msg = _("Segment type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        num_seg = len(self.ltrkseg)
        for pos in xrange(0, num_seg - 1):
            if trkseg.name == self.ltrkseg[pos].name:
                return pos
        return -1


    def listpoints(self):
        list_points = []
        for trkseg in self.ltrkseg:
            list_points = list_points + trkseg.lwpts
        return list_points


    def listPath(self, first_lat, first_lon, last_lat, last_lon):
        list_points = []
        found_first = False
        found_last = False
        track_pos = 0
        for trkseg in self.ltrkseg:
            point_pos = 0
            for point in trkseg.lwpts:
                if found_first:
                    list_points.append(point)
                    if point.lat == last_lat and point.lon == last_lon:
                        found_last = True
                        break
                else:
                    if point.lat == first_lat and point.lon == first_lon:
                        found_first = True
                        list_points.append(point)
                    elif point.lat == last_lat and point.lon == last_lon:
                        pos = 0
                        while pos < track_pos:
                            list_points = list_points + self.ltrkseg[pos].lwpts
                            pos = pos + 1
                        list_points = list_points + trkseg.lwpts[:point_pos + 1]
                        found_last = True
                        break
                point_pos += 1
            if found_last:
                break
            track_pos += 1
        return list_points


    def closest(self, time, tdelta):
        closed_trackseg = []
        for trkseg in self.ltrkseg :
            min_time = trkseg.lwpts[0].time - tdelta
            max_time = trkseg.lwpts[-1].time + tdelta
            if time > min_time and time < max_time:
                closed_trackseg.append(trkseg)
        return closed_trackseg


    def nearestSegmentPointDistance(self, lat, lon):
        min_distance = geomath.MaxDistanceEarth
        seg_nearest = None
        point_nearest = None
        for trkseg in self.ltrkseg :
            (point, distance) = trkseg.nearestPointDistance(lat, lon)
            if distance < min_distance :
                min_distance = distance
                seg_nearest = trkseg
                point_nearest = point
        return (seg_nearest, point_nearest, min_distance)


    def lengthMinMaxTotal(self):
        total_distance = 0.0
        max_long = 0.0
        min_long = geomath.MaxDistanceEarth
        for trkseg in self.ltrkseg :
            longitude = trkseg.length()
            if longitude < min_long:
                min_long = longitude
            if longitude > max_long:
                max_long = longitude
            total_distance = total_distance + longitude
        return (min_long, max_long, total_distance)


    def timeMinMaxDuration(self):
        min_time = datetime.datetime.max
        max_time = datetime.datetime.min
        diff_time = datetime.timedelta()
        for trkseg in self.ltrkseg :
            (tmin, tmax) = trkseg.timeMinMax()
            tdiff = tmax - tmin
            if tmin < min_time:
                min_time = tmin
            if tmax > max_time:
                max_time = tmax
            diff_time = diff_time + tdiff
        return (min_time, max_time, diff_time)


    def speedMinAvgMax(self):
        total_distance = 0.0
        min_speed = 0.0
        max_speed = 0.0
        avg_speed = 0.0
        l_avg_speed = []
        counter = 0
        for trkseg in self.ltrkseg :
            (smin, savg, smax) = trkseg.speedMinAvgMax()
            if counter == 0:
                min_speed = smin
                max_speed = smax
            if smin < min_speed:
                min_speed = smin
            if smax > max_speed:
                max_speed = smax
            l_avg_speed.append(savg)
            counter = counter + 1
        if len(l_avg_speed) > 0:
            avg_speed = float(sum(l_avg_speed)) / len(l_avg_speed)
        return (min_speed, avg_speed, max_speed)


# ######################
# GPX gpx implementation
# ######################

class GPX(object):
    """
    Base class for GPX data.
    It represents data that can be found into a GPX file.
    """

    def __init__(self, name, time, metadata={}):
        """
        GPX class constructor

        :Parameters:
            -`name`: Name GPX metadata.
            -`time`: Time, class 'datetime'
            -`metadata`: Metadata dictionary from GPX
        """
        if not isinstance(time, datetime.datetime):
            dgettext = {'type_expected': datetime.datetime.__name__, 'type_got': time.__class__.__name__}
            msg = _("Time type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        self.version = __GPX_version__
        self.creator = __GPX_creator__
        self.metadata = metadata
        self.metadata.setdefault('name', name)
        self.metadata.setdefault('time', time)
        self.waypoints = []
        self.tracks = []
        self.routes = []


    def __repr__(self):
        return "(GPX=%sv, creator=%s, metadata=%s Waypoints=%s Tracks=%s Routes=%s)" % \
        (self.version, self.creator, self.metadata, self.waypoints, self.tracks, self.routes)

    def __str__(self):
        return "GPX %sv, creator=%s, %s \n\tWaypoints: %s\n\tTracks: %s\n\tRoutes: %s" % \
        (self.version, self.creator, self.metadata, self.waypoints, self.tracks, self.routes)


# EOF

