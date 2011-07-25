#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       writeExifAction.py
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
