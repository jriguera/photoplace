#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       writeExifAction.py
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



class WriteExif(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, [state.lock_geophotos])
        threading.Thread.__init__(self)
        self.geolocation = state['exifmode'] != -1


    def ini(self, *args, **kwargs):
        self._notify_ini(self.geolocation)
        self.num_wexif = 0
        self.num_photos = 0
        if self.geolocation:
            self.logger.info(_("Writing new EXIF data to JPEG files ..."))
            return True
        self.logger.debug(_("Nothing to do!. Not in geolocate mode!"))
        return False


    def go(self, rini):
        if not self.geolocation:
            return False
        ok = True
        for photo in self.state.geophotos:
            self._notify_run(photo, 0)
            if photo.status < self.state.status:
                continue
            self.dgettext['photo'] = photo.name.encode(PLATFORMENCODING)
            self.dgettext['photo_lon'] = photo.lon
            self.dgettext['photo_lat'] = photo.lat
            self.dgettext['photo_ele'] = photo.ele
            self.dgettext['photo_time'] = photo.time
            if photo.isGeoLocated():
                try:
                    photo.writeExif()
                    self.num_wexif += 1
                except Exception as exception:
                    self.dgettext['error'] = str(exception)
                    self.logger.error(_("Error while EXIF data was being written to "
                        "'%(photo)s': %(error)s") % self.dgettext)
                    ok = False
                else:
                    self._notify_run(photo, 1)
                    self.logger.debug(_("Photo '%(photo)s' (%(photo_time)s) "
                        "geolocated. EXIF data written: (lon=%(photo_lon).8f, "
                        "lat=%(photo_lat).8f, ele=%(photo_ele).8f).") % self.dgettext)
                self.num_photos += 1
            else:
                msg = _("Ignoring not geolocated photo '%(photo)s' (%(photo_time)s).")
                self.logger.warning(msg % self.dgettext)
                self._notify_run(photo, -1)
        return ok


    def end(self, rgo):
        self.dgettext['num_photos'] = self.num_photos
        self.dgettext['num_wexif'] = self.num_wexif
        msg = _("%(num_photos)s photos have been processed, "
            "exif data of %(num_wexif)s updated.")
        self.logger.info(msg % self.dgettext)
        self._notify_end(self.num_photos, self.num_wexif)
        return rgo


# EOF
