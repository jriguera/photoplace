#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       loadPhotosAction.py
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


import os.path
import threading
import datetime
import re

import Interface
from PhotoPlace.DataTypes import geoPhotoData
from PhotoPlace.Facade import Error
from PhotoPlace.definitions import *


class LoadPhotos(Interface.Action, threading.Thread):

    def __init__(self, state, append=True):
        Interface.Action.__init__(self, state, [state.lock_geophotos])
        threading.Thread.__init__(self)
        self.append = append
        self.photoinputdir = state['photoinputdir']
        self.dgettext['photoinputdir'] = self.photoinputdir  #.encode(PLATFORMENCODING)
        self.allowed_names = PhotoPlace_Cfg_PhotoRegExp.search
        self.toffset = state['timeoffsetseconds']
        self.num_photos = 0
        try:
            self.listphotoinputdir = os.listdir(self.photoinputdir)
        except OSError as oserror:
            self.dgettext['error'] = str(oserror)
            msg = _("Cannot read '%(photoinputdir)s' directory: %(error)s.")
            msg = msg % self.dgettext
            self.logger.error(msg)
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
                self.dgettext['photo'] = filename  #.encode(PLATFORMENCODING)
                try:
                    #geophoto = geoPhotoData.GeoPhoto(filename, re.sub(r"\s+", '_', fname))
                    geophoto = geoPhotoData.GeoPhoto(filename, re.sub(r"\s+", '_', fname.lower()))
                    #geophoto = geoPhotoData.GeoPhoto(filename, fname)
                except Exception as e:
                    self.dgettext['error'] = str(e)
                    msg = _("Error processing photo '%(photo)s': %(error)s.")
                else:
                    geophoto.status = 1
                    offset = geophoto.toffset + self.toffset
                    geophoto.time = geophoto.time + datetime.timedelta(seconds=offset)
                    geophoto.toffset = -self.toffset
                    self._notify_run(geophoto)
                    position = 0
                    for photo in self.state.geophotos:
                        if geophoto.time <= photo.time:
                            self.state.geophotos.insert(position, geophoto)
                            break
                        position += 1
                    else:
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
