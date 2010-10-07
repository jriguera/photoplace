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


import os.path
import threading
import datetime

import Actions.Interface
from definitions import *



class MakeKML(Actions.Interface.Action, threading.Thread):

    def __init__(self, state, rootdata={}):
        Actions.Interface.Action.__init__(self, state,
            [state.lock_geophotos, state.lock_gpxdata, state.lock_kmldata])
        threading.Thread.__init__(self)
        self.photouri = state['photouri']
        self.jpgsize = state['jpgsize']
        self.quality = state.quality['img']
        self.jpgzoom = state['jpgzoom']
        self.outputdir = state.outputdir
        utczoneminutes = state['utczoneminutes']
        self.str_tzdiff = '-'
        if utczoneminutes < 0:
            utczoneminutes = -utczoneminutes
            self.str_tzdiff = '+'
        hours, remainder = divmod(utczoneminutes, 60)
        minutes, seconds = divmod(remainder, 60)
        self.str_tzdiff = self.str_tzdiff + "%.2d:%.2d" % (hours, minutes)
        self.rootdata = rootdata


    def ini(self, *args, **kwargs):
        self._notify_ini(self.outputdir, self.photouri,
            self.jpgsize, self.jpgzoom, self.quality)
        self.dgettext['jpgsize'] = self.jpgsize
        self.dgettext['jpgzoom'] = self.jpgzoom
        self.dgettext['quality'] = self.quality
        self.dgettext['photouri'] = self.photouri
        self.dgettext['exifmode'] = self.state['exifmode']
        self.dgettext['outputdir'] = self.outputdir
        self.logger.info(_("Generating KML from photos' geodata ..."))
        msg = _("Generating KML from photos with options: <%s>.") % self.dgettext
        self.logger.debug(msg)
        self.num_photos = 0


    def go(self, rini):
        photodata = dict()
        mode = 0
        if '%(' in self.photouri:
            mode = 1
        elif '%s' in self.photouri:
            mode = 2
        for photo in self.state.geophotos:
            self._notify_run(photo, 0)
            if photo.status < self.state.status:
                continue
            photodata.clear()
            self.dgettext['photo'] = photo.name
            self.dgettext['photo_lon'] = photo.lon
            self.dgettext['photo_lat'] = photo.lat
            self.dgettext['photo_ele'] = photo.ele
            self.dgettext['photo_time'] = photo.time
            if photo.isGeoLocated():
                photodata.update(photo.attr)
                photodata[PhotoPlace_PhotoLAT] = photo.lat
                photodata[PhotoPlace_PhotoLON] = photo.lon
                photodata[PhotoPlace_PhotoELE] = photo.ele
                photodata[PhotoPlace_PhotoNAME] = photo.name
                photodata[PhotoPlace_PhotoDATE] = photo.time
                photodata[PhotoPlace_PhotoWIDTH] = self.jpgsize[0]
                photodata[PhotoPlace_PhotoHEIGHT] = self.jpgsize[1]
                photodata[PhotoPlace_PhotoZOOM] = self.jpgzoom
                photodata[PhotoPlace_URI] = self.photouri
                str_utctime = photo.time.strftime("%Y-%m-%dT%H:%M:%S")
                photodata[PhotoPlace_PhotoTZDATE] = str_utctime + self.str_tzdiff
                for k in photo.exif.exif_keys:
                    try:
                        photodata[k] = str(photo.exif[k].value)
                    except:
                        pass
                if mode == 1:
                    photodata[PhotoPlace_PhotoURI] = self.photouri % photodata
                elif mode == 2:
                    photodata[PhotoPlace_PhotoURI] = self.photouri % photo.name
                else:
                    photodata[PhotoPlace_PhotoURI] = self.photouri + photo.name
                # data to template.
                self.state.kmldata.setData(photodata)
                self._notify_run(photo, 1)
                self.logger.debug(
                    _("Photo '%(photo)s' was processed for KML data") % self.dgettext)
                self.num_photos += 1
            else:
                self.logger.warning(
                    _("Ignoring not geolocated photo '%(photo)s' (%(photo_time)s).") \
                    % self.dgettext)
                self._notify_run(photo, -1)
        return self.state.kmldata


    def end(self, rgo):
        self.state.kmldata.close(self.rootdata)
        self._notify_end(self.num_photos)
        self.dgettext['num_photos'] = self.num_photos
        msg = _("%(num_photos)s photos have been processed for KML data.")
        self.logger.info(msg % self.dgettext)
        return self.num_photos


# EOF
