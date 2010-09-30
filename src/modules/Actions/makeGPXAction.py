#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       makeGPXAction.py
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

import gpx

import Actions.Interface
from definitions import *



class MakeGPX(Actions.Interface.Action, threading.Thread):

    def __init__(self, state, name=None):
        Actions.Interface.Action.__init__(self, state, [state.lock_gpxdata])
        threading.Thread.__init__(self)
        self.geophotos = state.geophotos
        if name:
            self.name = name
        else:
            try:
                self.name = state['photoinputdir']
            except:
                self.name = PhotoPlace_Cfg_GeneratedTrackName
        self.description = PhotoPlace_Cfg_GeneratedTrackDescription
        self.proc_photos = 0
        if not self.state.gpxdata:
            gpx_date = datetime.datetime.utcnow()
            self.gpxdata = gpx.GPX(self.name, gpx_date)
        else:
            for track in self.state.gpxdata.tracks:
                if track.name == self.name:
                    raise ValueError(_("Track name %s already exist!") % (self.name))
            self.gpxdata = self.state.gpxdata


    def ini(self, *args, **kwargs):
        self._notify_ini(self.gpxdata, self.name, self.description)
        self.dgettext['track_name'] = self.name
        self.dgettext['track_description'] = self.description
        msg = _("Generating GPX track '%(track_name)s' ...") % self.dgettext
        self.logger.info(msg)
        return self.gpxdata


    def go(self, rini):
        self.proc_photos = 0
        gpxtrk = gpx.GPXTrack(self.name, self.description)
        gpxtrkseg = gpx.GPXSegment(self.name)
        for photo in self.geophotos:
            self._notify_run(photo, 0)
            if photo.status < 1:
                continue
            self.dgettext['photo'] = photo.name
            if photo.isGeoLocated():
                gpxwpt = gpx.GPXPoint(
                    photo.lat, photo.lon, photo.ele, photo.time, photo.name
                )
                self._notify_run(photo, 1)
                self.dgettext['photo_lon'] = photo.lon
                self.dgettext['photo_lat'] = photo.lat
                self.dgettext['photo_ele'] = photo.ele
                self.dgettext['photo_time'] = photo.time
                self.logger.debug(_("Photo: '%(photo)s' (%(photo_time)s) "
                    "geolocated with coordinates (lon=%(photo_lon).8f, "
                    "lat=%(photo_lat).8f, ele=%(photo_ele).8f). Generated "
                    "WayPoint.") % self.dgettext)
                gpxtrkseg.addPoint(gpxwpt)
                self.proc_photos += 1
            else:
                self._notify_run(photo, -1)
                msg = _("Photo: '%(photo)s' is not geolocated. Nothing to do.")
                self.logger.warning( msg % self.dgettext)
        try:
            gpxtrk.addSegment(gpxtrkseg)
            msg = _("Track '%s' was generated from geolocated photos.")
            self.logger.info(msg % gpxtrk.name)
        except gpx.GPXError:
            # GPXError if len(gpxtrkseg) == 0
            msg = _("Cannot generate GPX Track from no geolocated photos!")
            self.logger.error(msg)
        return gpxtrk


    def end(self, rgo):
        self._notify_end(self.proc_photos)
        msg = _("%s photos/waypoints were processed/generated.")
        self.logger.info(msg % self.proc_photos)
        self.gpxdata.tracks.append(rgo)
        self.state.gpxdata = self.gpxdata
        return self.gpxdata


# EOF
