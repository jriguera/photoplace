#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright © 2010 Jose Riguera Lopez <jriguera@gmail.com>
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


# EOF

