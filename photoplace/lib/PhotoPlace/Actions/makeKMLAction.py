#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       makeKMLAction.py
#
#       Copyright 2010 Jose Riguera Lopez <jriguera@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
"""
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import threading
import datetime

import pyGPX

import Interface
from PhotoPlace.definitions import *



class MakeKML(Interface.Action, threading.Thread):

    def __init__(self, state, rootdata={}):
        Interface.Action.__init__(self, state,
            [state.lock_geophotos, state.lock_gpxdata, state.lock_kmldata])
        threading.Thread.__init__(self)
        self.photouri = state['photouri']
        self.jpgsize = state['jpgsize']
        self.quality = state.quality['img']
        self.jpgzoom = state['jpgzoom']
        self.outputdir = state.outputdir
        utczoneminutes = state['utczoneminutes']
        self.time_zone = datetime.timedelta(minutes=utczoneminutes)
        self.str_tzdiff = '-'
        if utczoneminutes < 0:
            utczoneminutes = -utczoneminutes
            self.str_tzdiff = '+'
        hours, remainder = divmod(utczoneminutes, 60)
        minutes, seconds = divmod(remainder, 60)
        self.str_tzdiff = self.str_tzdiff + "%.2d:%.2d" % (hours, minutes)
        self.uri_mode = 0
        self.rootdata = dict(rootdata)


    def _set_value(self, key, value):
        if self.rootdata.has_key(key):
            current = self.rootdata[key].strip()
            try:
                val = float(current)
            except:
                self.rootdata[key] = value
        else:
            self.rootdata[key] = value


    def ini(self, *args, **kwargs):
        min_time = datetime.datetime.utcnow()
        max_time = datetime.datetime(1980, 6, 2)
        total_length = 0.0
        num_tracks = 0
        num_points = 0
        max_lat = -90.0
        min_lat = 90.0
        max_lon = -180.0
        min_lon = 180.0
        if self.state.gpxdata:
            for track in self.state.gpxdata.tracks:
                if not track.status:
                    continue
                try:
                    (tmin, tmax, duration) = track.timeMinMaxDuration()
                    if tmin < min_time:
                        min_time = tmin
                    if tmax > max_time:
                        max_time = tmax
                    (lmin, lmax, length) = track.lengthMinMaxTotal()
                    total_length += length
                    points = track.listpoints()
                    for point in points:
                        num_points += 1
                        if max_lat < point.lat:
                            max_lat = point.lat
                        if min_lat > point.lat:
                            min_lat = point.lat
                        if max_lon < point.lon:
                            max_lon = point.lon
                        if min_lon > point.lon:
                            min_lon = point.lon
                    points = None
                    num_tracks += 1
                except Exception as e:
                    self.dgettext['error'] = str(e)
                    self.dgettext['path'] = track.name #.encode(PLATFORMENCODING)
                    msg = _("Cannot process '%(path)s': %(error)s.") % self.dgettext
                    self.logger.error(msg)
            min_time = min_time + self.time_zone
            max_time = max_time + self.time_zone
        else:
            num_tracks = 1
            prev_lat = 0.0
            prev_lon = 0.0
            for geophoto in self.state.geophotos:
                if geophoto.status > 0 and geophoto.isGeoLocated():
                    if num_points == 0:
                        min_time = geophoto.time
                    else:
                        total_length += pyGPX.distanceCoord(
                            prev_lat, prev_lon, 
                            geophoto.lat, geophoto.lon)
                    max_time = geophoto.time
                    if max_lat < geophoto.lat:
                        max_lat = geophoto.lat
                    if min_lat > geophoto.lat:
                        min_lat = geophoto.lat
                    if max_lon < geophoto.lon:
                        max_lon = geophoto.lon
                    if min_lon > geophoto.lon:
                        min_lon = geophoto.lon
                    prev_lat = geophoto.lat
                    prev_lon = geophoto.lon
                    num_points += 1
        diff_time = abs(max_time - min_time)
        self.rootdata[PhotoPlace_NumPOINTS] = num_points
        self.rootdata[PhotoPlace_NumTRACKS] = num_tracks
        str_time = min_time.strftime("%Y-%m-%dT%H:%M:%S")
        self.rootdata[PhotoPlace_MinTime] = str_time + self.str_tzdiff
        str_time = max_time.strftime("%Y-%m-%dT%H:%M:%S")
        self.rootdata[PhotoPlace_MaxTime] = str_time + self.str_tzdiff
        self.rootdata[PhotoPlace_DiffTime] = str(diff_time)
        self.rootdata[PhotoPlace_MinLAT] = min_lat
        self.rootdata[PhotoPlace_MaxLAT] = max_lat
        self.rootdata[PhotoPlace_MinLON] = min_lon
        self.rootdata[PhotoPlace_MaxLON] = max_lon
        # Calculate the best values:
        max_distance = pyGPX.distanceCoord(min_lat, min_lon, max_lat, max_lon)
        altitude = max_distance * 2
        self._set_value(PhotoPlace_IniALT, altitude)
        self._set_value(PhotoPlace_IniRANGE, PhotoPlace_Cfg_default_inirange)
        self._set_value(PhotoPlace_IniTILT, PhotoPlace_Cfg_default_initilt)
        self._set_value(PhotoPlace_IniHEADING, PhotoPlace_Cfg_default_heading)
        center_lat = (max_lat + min_lat)/2.0
        self._set_value(PhotoPlace_MidLAT, center_lat)
        center_lon = (max_lon + min_lon)/2.0
        self._set_value(PhotoPlace_MidLON, center_lon)
        self.rootdata[PhotoPlace_ResourceURI] = self.photouri  #.encode(PLATFORMENCODING)
        self._notify_ini(self.rootdata)
        self.dgettext['jpgsize'] = self.jpgsize
        self.dgettext['jpgzoom'] = self.jpgzoom
        self.dgettext['quality'] = self.quality
        self.dgettext['photouri'] = self.photouri  #.encode(PLATFORMENCODING)
        self.dgettext['exifmode'] = self.state['exifmode']
        self.dgettext['outputdir'] = self.outputdir.encode(PLATFORMENCODING)
        # Photo URI
        if '%(' in self.photouri:
            self.uri_mode = 1
        elif '%s' in self.photouri:
            self.uri_mode = 2
        else:
            self.uri_mode = 0
        self.logger.info(_("Generating KML from photos' geodata ..."))
        msg = _("Generating KML from photos with options: <%s>.") % self.dgettext
        self.logger.debug(msg)
        self.num_photos = 0


    def go(self, rini):
        photodata = dict()
        for photo in self.state.geophotos:
            self._notify_run(photo, 0)
            if photo.status < self.state.status:
                continue
            photodata.clear()
            self.dgettext['photo'] = photo.name.encode(PLATFORMENCODING)
            self.dgettext['photo_lon'] = photo.lon
            self.dgettext['photo_lat'] = photo.lat
            self.dgettext['photo_ele'] = photo.ele
            self.dgettext['photo_time'] = photo.time
            if photo.isGeoLocated():
                photodata.update(photo.attr)
                photodata[PhotoPlace_PhotoLAT] = photo.lat
                photodata[PhotoPlace_PhotoLON] = photo.lon
                photodata[PhotoPlace_PhotoELE] = photo.ele
                photodata[PhotoPlace_PhotoNAME] = photo.name.encode(PLATFORMENCODING)
                photodata[PhotoPlace_PhotoDATE] = photo.time
                photodata[PhotoPlace_PhotoPTIME] = photo.ptime
                photodata[PhotoPlace_PhotoWIDTH] = self.jpgsize[0]
                photodata[PhotoPlace_PhotoHEIGHT] = self.jpgsize[1]
                photodata[PhotoPlace_PhotoZOOM] = self.jpgzoom
                photodata[PhotoPlace_ResourceURI] = self.photouri  #.encode(PLATFORMENCODING)
                str_utctime = photo.time.strftime("%Y-%m-%dT%H:%M:%S")
                photodata[PhotoPlace_PhotoUTCDATE] = str_utctime + self.str_tzdiff
                for k in photo.exif.exif_keys:
                    try:
                        photodata[k] = str(photo.exif[k].value)
                    except:
                        pass
                if self.uri_mode == 1:
                    photodata[PhotoPlace_PhotoURI] = self.photouri % photodata
                elif self.uri_mode == 2:
                    photodata[PhotoPlace_PhotoURI] = \
                        self.photouri % photo.name.encode(PLATFORMENCODING)
                else:
                    photodata[PhotoPlace_PhotoURI] = \
                        self.photouri + photo.name.encode(PLATFORMENCODING)
                # data to template.
                self.state.kmldata.setData(photodata)
                self._notify_run(photo, 1)
                msg = _("Photo '%(photo)s' was processed for KML data")
                self.logger.debug(msg % self.dgettext)
                self.num_photos += 1
            else:
                msg = _("Ignoring not geolocated photo '%(photo)s' (%(photo_time)s).")
                self.logger.warning(msg % self.dgettext)
                self._notify_run(photo, -1)
        return self.state.kmldata


    def end(self, rgo):
        self.state.kmldata.close(self.rootdata)
        self.rootdata = None
        self._notify_end(self.num_photos)
        self.dgettext['num_photos'] = self.num_photos
        msg = _("%(num_photos)s photos have been processed for KML data.")
        self.logger.info(msg % self.dgettext)
        return self.num_photos


# EOF
