#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       loadPhotosAction.py
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

from userFacade import Error
import DataTypes.geoPhotoData
import Actions.Interface
from definitions import *



class LoadPhotos(Actions.Interface.Action, threading.Thread):

    def __init__(self, state, append=True):
        Actions.Interface.Action.__init__(self, state, [state.lock_geophotos])
        threading.Thread.__init__(self)
        self.append = append
        self.photoinputdir = state['photoinputdir']
        self.dgettext['photoinputdir'] = self.photoinputdir
        self.allowed_names = PhotoPlace_Cfg_PhotoRegExp.search
        self.num_photos = 0
        try:
            self.listphotoinputdir = os.listdir(self.photoinputdir)
        except OSError as oserror:
            self.dgettext['error'] = str(oserror)
            msg = _("Cannot read '%(photoinputdir)s' directory: %(error)s.")
            self.logger.error(msg % self.dgettext)
            tip = _("Check directory permissions")
            raise Error(msg, tip, "OSError")


    def ini(self, *args, **kwargs):
        self._notify_ini(self.append, self.allowed_names, self.listphotoinputdir)
        msg = _("Processing photos in '%(photoinputdir)s' ...")
        self.logger.info(msg % self.dgettext)
        if not self.append:
            self.state.geophotos = []
        return self.state.geophotos


    def go(self, rini):
        self.num_photos = 0
        for fname in self.listphotoinputdir:
            if self.allowed_names(fname):
                filename = os.path.join(self.photoinputdir, fname)
                self.dgettext['photo'] = filename
                try:
                    geophoto = DataTypes.geoPhotoData.GeoPhoto(filename)
                except Exception as e:
                    self.dgettext['error'] = str(e)
                    msg = _("Error processing photo '%(photo)s': %(error)s.")
                else:
                    geophoto.status = 1
                    self._notify_run(geophoto)
                    self.state.geophotos.append(geophoto)
                    self.num_photos += 1
                    msg = _("Photo file name '%(photo)s' was processed properly.")
                self.logger.debug(msg % self.dgettext)
        return self.state.geophotos


    def end(self, rgo):
        self._notify_end(self.num_photos)
        self.dgettext['num_photos'] = self.num_photos
        msg = _("'%(photoinputdir)s': %(num_photos)s photos have been processed.")
        self.logger.info(msg % self.dgettext)
        return self.state.geophotos


# EOF
