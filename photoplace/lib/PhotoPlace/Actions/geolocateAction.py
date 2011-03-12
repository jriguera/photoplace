#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       geolocateAction.py
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

import Interface



class Geolocate(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, 
            [state.lock_geophotos, state.lock_gpxdata])
        threading.Thread.__init__(self)
        self.geophotos = state.geophotos
        self.gpxdata = state.gpxdata
        self.time_zone = datetime.timedelta(minutes=state['utczoneminutes'])
        self.maxdeltaseconds = state["maxdeltaseconds"]
        self.forcegeolocation = state["exifmode"] == 1
        self.dgettext['exifmode'] = self.state["exifmode"]
        self.geolocated = []


    def ini(self, *args, **kwargs):
        self._notify_ini(self.maxdeltaseconds, self.forcegeolocation)
        self.dgettext['maxdeltaseconds'] = self.maxdeltaseconds
        self.dgettext['timezone'] = self.time_zone
        msg = _("Geotagging with mode <%(exifmode)s>, diff from UTC %(timezone)s "
            "and time delta of %(maxdeltaseconds)s seconds ...") % self.dgettext
        self.logger.info(msg)
        return self.geolocated


    def go(self, rini):
        self.photo_counter = len(self.geolocated)
        max_delta = datetime.timedelta(seconds=self.maxdeltaseconds)
        self.dgettext['time_delta'] = max_delta
        for photo in self.geophotos:
            self._notify_run(photo, 0)
            if photo.status < 1:
                continue
            self.dgettext['photo'] = photo.name
            self.dgettext['photo_time'] = photo.time
            photo_tutc = photo.time - self.time_zone
            self.dgettext['photo_tutc'] = photo_tutc
            self.dgettext['photo_lon'] = photo.lon
            self.dgettext['photo_lat'] = photo.lat
            self.dgettext['photo_ele'] = photo.ele
            if photo.isGeoLocated() and not self.forcegeolocation:
                self.logger.debug(_("Photo: '%(photo)s' at %(photo_time)s "
                    "(UTC=%(photo_tutc)s) is geotagged with (lon=%(photo_lon).8f, "
                    "lat=%(photo_lat).8f, ele=%(photo_ele).8f). Calculated "
                    "coordinates ignored due to <nooverwrite> option.") % self.dgettext)
                self._notify_run(photo, -1)
                continue
            tracksegs = []
            for track in self.gpxdata.tracks:
                tracksegs += track.closest(photo_tutc, max_delta)
            if len(tracksegs) == 0:
                self.logger.warning(_("It is impossible geotag '%(photo)s' "
                    "taken at %(photo_time)s (UTC=%(photo_tutc)s) with time "
                    "delta %(time_delta)s. No closed points.") % self.dgettext)
                self._notify_run(photo, -2)
            else:
                min_diff = datetime.timedelta.max
                closed_point = None
                for tragseg in tracksegs:
                    point = tragseg.closest(photo_tutc)
                    delta = abs(point.time - photo_tutc)
                    if delta < min_diff:
                        min_diff = delta
                        closed_point = point
                self.dgettext['point_time'] = closed_point.time
                if min_diff > max_delta:
                    self.logger.warning(_("It is impossible geotag '%(photo)s' "
                        "taken at %(photo_time)s (UTC=%(photo_tutc)s) with time delta "
                        "%(time_delta)s. The nearest point is too far "
                        "(time=%(point_time)s).") % self.dgettext)
                    self._notify_run(photo, -3)
                else:
                    photo.lat = closed_point.lat
                    photo.lon = closed_point.lon
                    photo.ele = closed_point.ele
                    self.dgettext['photo_lon'] = photo.lon
                    self.dgettext['photo_lat'] = photo.lat
                    self.dgettext['photo_ele'] = photo.ele
                    self.dgettext['time_diff'] = min_diff
                    self.logger.debug(_("Photo: '%(photo)s' at %(photo_time)s "
                        "(UTC=%(photo_tutc)s) geotagged with (lon=%(photo_lon).8f, "
                        "lat=%(photo_lat).8f, ele=%(photo_ele).8f, time=%(point_time)s) "
                        "and time delta '%(time_diff)s'.") % self.dgettext)
                    self.photo_counter += 1
                    photo.status += 1
                    self.geolocated.append(photo)
                    self._notify_run(photo, 1)
        return self.geolocated


    def end(self, rgo):
        proc_photos = len(rgo)
        self._notify_end(proc_photos)
        self.dgettext['num_photos'] = len(self.geophotos)
        self.dgettext['proc_photos'] = proc_photos
        msg = _("%(proc_photos)s of %(num_photos)s photos have been geotagged.")
        msg = msg % self.dgettext
        self.logger.info(msg)
        return rgo


# EOF
