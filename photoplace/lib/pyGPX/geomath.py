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
# Thanks to:
#   * Oliver White and Graham Jones from wherewasi.project at
#     http://code.google.com/p/wherewasi/ for Geographic calculations.
#   * Steven Dutch, Natural and Applied Sciences, University of Wisconsin
#     for some formulas at http://www.uwgb.edu/dutchs/usefuldata/UTMFormulas.HTM
#   * Nick Granado for bearing calculations at
#     http://www.heatxsink.com/entry/manipulating-geo-coordinates-in-python-and-foursquare-cheating
#   * Andrew Hedges at http://andrew.hedges.name/experiments/
#     for some useful widgets.
"""
Some useful geographic formulas to do caculations with coordinates, points,
distances, bearing, etc ...

More information, see test code.
"""
__package_name__ = "gpx"
__package_revision__ = '0'
__package_version__ = '0.1.1'
__package_released__ = "Dec 2014"
__package_author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__package_license__ = "Apache 2.0"
__package_copyright__ ="(c) Jose Riguera"


import math


EarthsRadius     = 6378137.0    # Earth's radius =~ 6371km
MaxDistanceEarth = 22000000.0   # Max distance between two points


def NtoD (n):
   """
   Get degrees from a decimal number.
   """
   return int(n)


def NtoM (n):
    """
    Get minutes from a decimal number.
    """
    minutes = float(n) * 60.0 - NtoD(n) * 60.0
    return int(minutes)


def NtoS (n):
    """
    Get seconds from a decimal number.
    """
    seconds = float(n) * 3600.0 - NtoD(n) * 3600.0 - NtoM(n) * 60.0
    seconds = round(seconds, 2)
    return seconds


def NtoDMS (coordinate):
    """
    Get degrees, minutes and seconds from a decimal number.
    """
    (m, s) = divmod(coordinate * 3600, 60)
    (d, m) = divmod(m, 60)
    return (d, m, s)


def DMStoN (degrees, minutes, seconds):
    """
    Get a decimal number from degrees, minutes and seconds.
    """
    decimal = degrees + float(minutes) / 60.0 + float(seconds) / 3600.0
    return decimal


def distanceCoord (lat0, lon0, lat1, lon1):
    """
    Distance between two points in meters.
    """
    dLat = math.radians(lat1 - lat0)
    dLon = math.radians(lon1 - lon0)
    a = math.sin(dLat/2.0) * math.sin(dLat/2.0) + math.cos(math.radians(lat0)) * \
        math.cos(math.radians(lat1)) * math.sin(dLon/2.0) * math.sin(dLon/2.0)
    if a > 1.0: 
        # error correction for rounding errors.
        a = 1.0 
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return (EarthsRadius * c)


def moveCoord (latitude, longitude, distance, bearing):
    """
    Calculate next point at distance with bearing.
    """
    bearing = math.radians(bearing)
    lat = math.radians(latitude)
    lon = math.radians(longitude)
    d = float(distance) / float(EarthsRadius)
    y = math.asin(math.sin(lat) * math.cos(d) + \
        math.cos(lat) * math.sin(d) * math.cos(bearing))
    x = lon + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(lat), \
        math.cos(d) - math.sin(lat) * math.sin(y))
    return (math.degrees(y), math.degrees(x))


def bearingCoord (lat0, lon0, lat1, lon1):
    """
    Bearing from one point to another in degrees (0-360).
    """
    dLat = lat1 - lat0
    dLon = lon1 - lon0
    y = math.sin(math.radians(dLon)) * math.cos(math.radians(lat1))
    x = math.cos(math.radians(lat0)) * math.sin(math.radians(lat1)) - \
        math.sin(math.radians(lat0)) * math.cos(math.radians(lat1)) * \
        math.cos(math.radians(dLon))
    bearing = math.degrees(math.atan2(y, x))
    if(bearing < 0.0):
        bearing = bearing + 360.0
    return bearing


def bestViewAltitude(max_lat, max_lon, min_lat, min_lon, scale_range=1.5, aspect_ratio=1.5):
    """
    Calculate the best altitude to see the points.
    http://stackoverflow.com/questions/5491315/calculate-range-and-altitude-of-the-google-earth-kml-lookat-element-to-fit-all-f
    http://code.google.com/p/earth-api-utility-library/source/browse/trunk/extensions/src/view/boundsview.js
    """
    center_lon = (max_lon + min_lon) / 2.0
    center_lat = (max_lat + min_lat) / 2.0
    
    EW_distance = distanceCoord(center_lat, max_lon, center_lat, min_lon)
    NS_distance = distanceCoord(min_lat, center_lon, max_lat, center_lon)
    aspect_ratio = min(max(aspect_ratio, EW_distance / NS_distance), 1.0)
    
    # using the experimentally derived distance formula.
    alpha = math.radians(45.0 / (aspect_ratio + 0.4) - 2.0)
    expand_distance = max(NS_distance, EW_distance)
    beta = min(math.radians(90.0), alpha + expand_distance / (2.0 * float(EarthsRadius)))
    altitude = scale_range * float(EarthsRadius) * \
               (math.sin(beta) * math.sqrt(1.0 + ( 1.0 / math.pow(math.tan(alpha), 2))) - 1)
    return altitude


def simplDouglasPeucker(points, epsilon):
    """
    The Ramer–Douglas–Peucker algorithm (RDP) is an algorithm for reducing the 
    number of points in a curve that is approximated by a series of points.
    """
    # epsilon depth in meters is the maximum allowed distance between the poin,
    # and the paht. It is the height of the triangle abc where a-b and b-c are 
    # two consecutive line segments 
    len_points = len(points)
    # indexes of points to include in the simplification
    index = []
    # if one or two points ...
    if len_points < 3:
        return points
    band_sqr = epsilon * 360.0 / (2.0 * math.pi * EarthsRadius)
    band_sqr = band_sqr * band_sqr
    F = math.pi / 360.0
    stack = [(0, len_points-1)]
    while stack:
        start, end = stack.pop()
        if (end - start) > 1:
            # intermediate points, find most distant intermediate point
            # with the line from start to end points 
            x12 = (points[end].lon - points[start].lon)
            y12 = (points[end].lat - points[start].lat)
            if math.fabs(x12) > 180.0:
                x12 = 360.0 - math.fabs(x12)
            x12 *= math.cos(F * (points[end].lat + points[start].lat))
            d12 = (x12*x12) + (y12*y12)

            sig = start
            max_dev_sqr = -1.0
            for i in xrange(start + 1, end):
                x13 = (points[i].lon - points[start].lon)
                y13 = (points[i].lat - points[start].lat)
                if math.fabs(x13) > 180.0:
                    x13 = 360.0 - math.fabs(x13)
                x13 *= math.cos(F * (points[i].lat + points[start].lat))
                d13 = (x13*x13) + (y13*y13)
                x23 = (points[i].lon - points[end].lon)
                y23 = (points[i].lat - points[end].lat)
                if math.fabs(x23) > 180.0:
                    x23 = 360.0 - math.fabs(x23)
                x23 *= math.cos(F * (points[i].lat + points[end].lat))
                d23 = (x23*x23) + (y23*y23)
                if d13 >= (d12 + d23):
                    dev_sqr = d23
                elif d23 >= (d12 + d13):
                    dev_sqr = d13
                else:
                    # solve triangle
                    dev_sqr = (x13 * y12 - y13 * x12) * (x13 * y12 - y13 * x12) / d12
                if dev_sqr > max_dev_sqr:
                    sig = i;
                    max_dev_sqr = dev_sqr;
            if max_dev_sqr < band_sqr:
                # no sig. intermediate point, transfer current start point 
                index.append(start)
            else:
                stack.append((sig, end))
                stack.append((start, sig))
        else:
            index.append(start)
    # last point
    index.append(len_points-1)
    return [points[i] for i in index]


# EOF

