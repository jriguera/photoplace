#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       makeKMLAction.py
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
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.3"
__date__ = "Apr 2020"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


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
        self.tzdiff = state.tzdiff
        self.stzdiff = state.stzdiff
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
                min_time = min_time #- self.tzdiff
                max_time = max_time #- self.tzdiff
        else:
            num_tracks = 1
            prev_lat = 0.0
            prev_lon = 0.0
            for geophoto in self.state.geophotos:
                if geophoto.status >= self.state.status and geophoto.isGeoLocated():
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
            min_time = min_time - self.tzdiff
            max_time = max_time - self.tzdiff
        smax_time = max_time.strftime("%Y-%m-%dT%H:%M:%S") + self.stzdiff
        smin_time = min_time.strftime("%Y-%m-%dT%H:%M:%S") + self.stzdiff
        diff_time = abs(max_time - min_time)
        self.rootdata[PhotoPlace_NumPOINTS] = num_points
        self.rootdata[PhotoPlace_NumTRACKS] = num_tracks
        self.rootdata[PhotoPlace_MinTime] = smin_time
        self.rootdata[PhotoPlace_MaxTime] = smax_time
        self.rootdata[PhotoPlace_DiffTime] = str(diff_time)
        self.rootdata[PhotoPlace_MinLAT] = min_lat
        self.rootdata[PhotoPlace_MaxLAT] = max_lat
        self.rootdata[PhotoPlace_MinLON] = min_lon
        self.rootdata[PhotoPlace_MaxLON] = max_lon
        self._set_value(PhotoPlace_IniALT, PhotoPlace_Cfg_default_inialt)
        self._set_value(PhotoPlace_IniRANGE, PhotoPlace_Cfg_default_inirange)
        if self.rootdata[PhotoPlace_IniRANGE] < 1:
            if num_points > 1:
                altitude = pyGPX.bestViewAltitude(max_lat, max_lon, min_lat, min_lon)
            else:
                altitude = PhotoPlace_Cfg_default_inialt
            self.rootdata[PhotoPlace_IniRANGE] = altitude
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
        if self.outputdir != None:
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
                photo_tutc = photo.time - self.tzdiff
                photodata[PhotoPlace_PhotoUTCDATE] = photo_tutc.strftime("%Y-%m-%dT%H:%M:%S") + self.stzdiff
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
                tmptemplates = None
                if photo.path in self.state.geophotostyle:
                    tmptemplates = self.state.geophotostyle[photo.path]
                # data to template.
                self.state.kmldata.setData(photodata, tmptemplates)
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
