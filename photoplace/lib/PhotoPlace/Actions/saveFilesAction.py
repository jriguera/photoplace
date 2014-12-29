#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       saveFilesAction.py
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
import zipfile
import zlib
import shutil

import Interface
from PhotoPlace.Facade import Error
from PhotoPlace.definitions import *



class SaveFiles(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, [state.lock_geophotos])
        #### Interface.Action.__init__(self, state)
        threading.Thread.__init__(self)
        self.outputkmz = state.outputkmz
        self.dgettext['outputkmz'] = self.outputkmz  #.encode(PLATFORMENCODING)
        self.outputkml = state.outputkml
        self.dgettext['outputkml'] = self.outputkml  #.encode(PLATFORMENCODING)
        self.photouri = state["photouri"]
        self.outputdir = state.outputdir
        self.dgettext['outputdir'] = ''
        if self.outputdir != None:
            self.dgettext['outputdir'] = self.outputdir.encode(PLATFORMENCODING)
        self.tmpdir = state.tmpdir
        self.dgettext['tmpdir'] = ''
        if self.tmpdir != None:
            self.dgettext['tmpdir'] = self.tmpdir.encode(PLATFORMENCODING)
        self.quality = state.quality['zip']
        ####
        self.jpgsize = state['jpgsize']
        self.jpgquality = state.quality['img']
        self.jpgzoom = state['jpgzoom']
        self.copymode = state['copymode']
        ####
        self.outputkmldir = os.path.dirname(self.outputkml)
        self.fd = None
        try:
            self.fd = open(self.outputkml, 'wb')
        except IOError as (errno, strerror):
            self.dgettext['errno'] = errno
            self.dgettext['strerror'] = strerror
            msg = _("Cannot create KML file '%(outputkml)s': (%(errno)s) %(strerror)s.")
            msg = msg % self.dgettext
            self.logger.error(msg)
            tip = _("Check if output dir '%s' exists and is writable.") % self.outputdir
            raise Error(msg, tip, "IOError")


    def ini(self, *args, **kwargs):
        ####
        self.num_photos = 0
        self.num_copies = 0
        if (self.copymode > 0) and (self.outputdir != None):
            msg = _("Generating copy of JPEG files in '%(outputdir)s' ...")
            self.logger.info(msg % self.dgettext)
        ####
        self.num_files = 0
        self._notify_ini(self.fd, self.outputkml, self.outputkmz, 
            self.photouri, self.outputdir, self.quality)
        try:
            kmldom = self.state.kmldata.getKml()
            kmldom.writexml(self.fd, u"", u"   ", u"\n", "utf-8")
            self.num_files += 1
        except Exception as e:
            self.dgettext['error'] = str(e)
            msg = _("Cannot write to file '%(outputkml)s': %(error)s.") % self.dgettext
            self.logger.error(msg)
            tip = _("Check if output dir '%s' is writable.") % self.outputdir
            raise Error(msg, tip, "IOError")
        finally:
            self.fd.close()
        return kmldom


    def go(self, rini):
        #####
        if (self.copymode > 0) and (self.outputdir != None):
            for photo in self.state.geophotos:
                self._notify_run(photo.path, 0)
                if photo.status < self.state.status:
                    continue
                self.dgettext['photo'] = photo.name.encode(PLATFORMENCODING)
                self.dgettext['photo_lon'] = photo.lon
                self.dgettext['photo_lat'] = photo.lat
                self.dgettext['photo_ele'] = photo.ele
                self.dgettext['photo_time'] = photo.time
                if (self.copymode == 2) or ((self.copymode == 1) and photo.isGeoLocated()):
                    new_file = os.path.join(self.outputdir, photo.name)
                    self.dgettext['new_path'] = new_file.encode(PLATFORMENCODING)
                    try:
                        if photo.isGeoLocated():
                            photo.attrToExif()
                        photo.copy(new_file, True, self.jpgzoom, self.jpgsize, self.jpgquality)
                        self.num_copies += 1
                    except Exception as e:
                        self.dgettext['error'] = str(e)
                        msg = _("Cannot copy '%(photo)s' to '%(new_path)s': %(error)s.")
                        self.logger.error(msg % self.dgettext)
                    else:
                        self._notify_run(new_file, 1)
                        msg = _("Photo '%(photo)s' has been copied to '%(new_path)s'.") 
                        self.logger.debug(msg % self.dgettext)
                    self.num_photos += 1
                else:
                    msg = _("Ignoring not geolocated photo '%(photo)s' (%(photo_time)s).")
                    self.logger.warning(msg % self.dgettext)
                    self._notify_run(photo.path, -1)
        #####
        self.num_files += self.num_copies
        kmz_out = None
        if self.outputkmz == None:
            self._notify_run(self.outputkml, 1)
            msg = _("KML output file '%(outputkml)s' has been generated.")
            self.logger.info(msg % self.dgettext)
        else:
            msg = _("Generating KMZ file '%(outputkmz)s' ...")
            self.logger.info(msg % self.dgettext)
            kmz_out = zipfile.ZipFile(self.outputkmz, "w")
            self.rzip(kmz_out, self.outputkmldir)
        return kmz_out


    def rzip(self, zipf, folder, base=u''): 
        for f in os.listdir(folder):
            full_path = os.path.join(folder, f)
            if os.path.isfile(full_path):
                base_path = os.path.join(base, f)
                self.logger.debug(_("Adding file '%s' to KMZ ...") % \
                    base_path.encode(PLATFORMENCODING))
                self._notify_run(base_path, 1)
                zipf.write(full_path, base_path, self.quality)
                self.num_files += 1
            elif os.path.isdir(full_path):
                self.rzip(zipf, full_path, f)


    def end(self, rgo):
        ####
        if (self.copymode > 0) and (self.outputdir != None):
            self.dgettext['num_photos'] = self.num_photos
            self.dgettext['num_copies'] = self.num_copies
            msg = _("%(num_photos)d photos have been processed, %(num_copies)d were copied.")
            self.logger.info(msg % self.dgettext)
        ####
        self._notify_end(self.num_files)
        if rgo:
            rgo.close()
            msg = _("KMZ file '%(outputkmz)s' has been generated.")
            self.logger.info(msg % self.dgettext)
            if self.tmpdir:
                try:
                    shutil.rmtree(self.tmpdir, False)
                    msg = _("Deleting directory '%(tmpdir)s' ...")
                    self.logger.debug(msg % self.dgettext)
                except Exception as exception:
                    self.dgettext['error'] = str(exception)
                    msg = _("Cannot delete directory '%(tmpdir)s': %(error)s.")
                    self.logger.error(msg % self.dgettext)
        return self.num_files


# EOF
