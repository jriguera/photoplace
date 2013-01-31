#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       copyFilesAction.py
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

import Interface
from PhotoPlace.definitions import *



class CopyFiles(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, [state.lock_geophotos])
        threading.Thread.__init__(self)
        self.outputdir = state.outputdir
        self.jpgsize = state['jpgsize']
        self.quality = state.quality['img']
        self.jpgzoom = state['jpgzoom']
        self.onlygeolocated = state['copyonlygeolocated']


    def ini(self, *args, **kwargs):
        self._notify_ini(self.outputdir, self.onlygeolocated, 
            self.jpgsize, self.jpgzoom, self.quality)
        self.num_copies = 0
        self.num_photos = 0
        if self.outputdir != None:
            self.dgettext['outputdir'] = self.outputdir.encode(PLATFORMENCODING)
            msg = _("Generating copy of JPEG files in '%(outputdir)s' ...")
            self.logger.info(msg % self.dgettext)
            return True
        self.logger.debug(_("Nothing to do!. No output dir!"))
        return False


    def go(self, rini):
        if self.outputdir == None:
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
            if not self.onlygeolocated or photo.isGeoLocated():
                new_file = os.path.join(self.outputdir, photo.name)
                self.dgettext['new_path'] = new_file.encode(PLATFORMENCODING)
                try:
                    if photo.isGeoLocated():
                        photo.attrToExif()
                    photo.copy(new_file, True, self.jpgzoom, self.jpgsize, self.quality)
                    self.num_copies += 1
                except Exception as e:
                    self.dgettext['error'] = str(e)
                    msg = _("Cannot copy '%(photo)s' to '%(new_path)s': %(error)s.")
                    self.logger.error(msg % self.dgettext)
                    ok = False
                else:
                    self._notify_run(photo, 1)
                    msg = _("Photo '%(photo)s' has been copied to '%(new_path)s'.") 
                    self.logger.debug(msg % self.dgettext)
                self.num_photos += 1
            else:
                msg = _("Ignoring not geolocated photo '%(photo)s' (%(photo_time)s).")
                self.logger.warning(msg % self.dgettext)
                self._notify_run(photo, -1)
        return ok


    def end(self, rgo):
        self.dgettext['num_photos'] = self.num_photos
        self.dgettext['num_copies'] = self.num_copies
        msg = _("%(num_photos)d photos have been processed, %(num_copies)d were copied.")
        self.logger.info(msg % self.dgettext)
        self._notify_end(self.num_photos, self.num_copies)
        return rgo


# EOF
