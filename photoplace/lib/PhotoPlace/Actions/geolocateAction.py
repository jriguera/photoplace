#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       geolocateAction.py
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
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import threading
import datetime

import Interface
from PhotoPlace.definitions import *



class Geolocate(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, 
            [state.lock_geophotos, state.lock_gpxdata])
        threading.Thread.__init__(self)
        self.geophotos = state.geophotos
        self.gpxdata = state.gpxdata
        self.tzdiff = state.tzdiff
        self.maxdeltaseconds = state["maxdeltaseconds"]
        self.forcegeolocation = state["exifmode"] == 1
        self.dgettext['exifmode'] = self.state["exifmode"]
        self.geolocated = []


    def ini(self, *args, **kwargs):
        self._notify_ini(self.maxdeltaseconds, self.forcegeolocation)
        self.dgettext['maxdeltaseconds'] = self.maxdeltaseconds
        self.dgettext['timezone'] = self.tzdiff
        msg = _("Geotagging mode <%(exifmode)s>, diff from UTC %(timezone)s "
            "and delta of %(maxdeltaseconds)s seconds ...") % self.dgettext
        self.logger.info(msg)
        return self.geolocated


    def go(self, rini):
        self.photo_counter = len(self.geolocated)
        max_delta = datetime.timedelta(seconds=self.maxdeltaseconds)
        self.dgettext['time_delta'] = max_delta
        for photo in self.geophotos:
            self._notify_run(photo, 0)
            if photo.status < self.state.status:
                continue
            self.dgettext['photo'] = photo.name.encode(PLATFORMENCODING)
            self.dgettext['photo_time'] = photo.time
            photo_tutc = photo.time - self.tzdiff
            self.dgettext['photo_tutc'] = photo_tutc
            self.dgettext['photo_lon'] = photo.lon
            self.dgettext['photo_lat'] = photo.lat
            self.dgettext['photo_ele'] = photo.ele
            if photo.isGeoLocated():
                if not self.forcegeolocation:
                    self.logger.debug(_("Photo: '%(photo)s' at %(photo_time)s "
                        "(UTC=%(photo_tutc)s) is geotagged with (lon=%(photo_lon).8f, "
                        "lat=%(photo_lat).8f, ele=%(photo_ele).8f). Calculated "
                        "coordinates ignored due to <nooverwrite> option.") % self.dgettext)
                    photo.ptime = photo_tutc
                    self.photo_counter += 1
                    photo.status += 1
                    self.geolocated.append(photo)
                    #self._notify_run(photo, 1)
                    self._notify_run(photo, -1)
                    continue
            tracksegs = list()
            for track in self.gpxdata.tracks:
                if not track.status:
                    continue
                tracksegs += track.closest(photo_tutc, max_delta)
            if len(tracksegs) == 0:
                self.logger.warning(_("It is impossible geotag '%(photo)s' "
                    "taken at %(photo_time)s (UTC=%(photo_tutc)s) with time "
                    "delta %(time_delta)s. No closed points.") % self.dgettext)
                self._notify_run(photo, -2)
            else:
                min_tdiff = datetime.timedelta.max
                closed_point = None
                for tragseg in tracksegs:
                    point = tragseg.closest(photo_tutc)
                    delta = abs(point.time - photo_tutc)
                    if delta < min_tdiff:
                        min_tdiff = delta
                        closed_point = point
                self.dgettext['point_time'] = closed_point.time
                if min_tdiff > max_delta:
                    self.logger.warning(_("It is impossible geotag '%(photo)s' "
                        "taken at %(photo_time)s (UTC=%(photo_tutc)s) with time delta "
                        "%(time_delta)s. The nearest point is too far "
                        "(time=%(point_time)s).") % self.dgettext)
                    self._notify_run(photo, -3)
                else:
                    photo.lat = closed_point.lat
                    photo.lon = closed_point.lon
                    photo.ele = closed_point.ele
                    photo.ptime = closed_point.time
                    self.dgettext['photo_lon'] = photo.lon
                    self.dgettext['photo_lat'] = photo.lat
                    self.dgettext['photo_ele'] = photo.ele
                    self.dgettext['time_diff'] = min_tdiff
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
