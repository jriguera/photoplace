#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       readGPXAction.py
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
import codecs
import urllib

import pyGPX

import Interface
from PhotoPlace.Facade import Error
from PhotoPlace.definitions import *



class ReadGPX(Interface.Action, threading.Thread):

    def __init__(self, state):
        Interface.Action.__init__(self, state, [state.lock_gpxdata])
        threading.Thread.__init__(self)
        self.gpxinputfile = state['gpxinputfile']
        self.dgettext['gpxinputfile'] = self.gpxinputfile  #.encode(PLATFORMENCODING)
        try:
            try:
                self.fd = urllib.urlopen(self.gpxinputfile)
            except:
                # try to open with native open function (if source is pathname)
                self.fd = codecs.open(self.gpxinputfile, "r", encoding="utf-8")
        except IOError as (errno, strerror):
            self.dgettext['errno'] = errno
            self.dgettext['strerror'] = strerror
            msg = _("Cannot read GPX file '%(gpxinputfile)s': (%(errno)s) %(strerror)s.")
            msg = msg % self.dgettext
            self.logger.error(msg)
            tip = _("Check file path, permissions ... ")
            raise Error(msg, tip, "IOError")
        except ValueError as valueerror:
            self.dgettext['error'] = str(valueerror)
            msg = _("GPX file '%(gpxinputfile)s' not in UTF-8 format: %(error)s.")
            msg = msg % self.dgettext
            self.logger.error(msg)
            tip = _("Check file format. Maybe you need to export that file again.")
            raise Error(msg, tip, "ValueError")


    def ini(self, *args, **kwargs):
        self._notify_ini(self.fd)
        msg = _("Processing GPX data from '%(gpxinputfile)s' ...")
        self.logger.info(msg % self.dgettext)
        return self.state.gpxdata


    def go(self, rini):
        try:
            gpxparser = pyGPX.GPXParser(self.fd, os.path.basename(self.gpxinputfile))
            #    os.path.basename(self.gpxinputfile), self.utc_time_delta)
            self._notify_run(gpxparser)
        except Exception as exception:
            self.dgettext['error'] = str(exception)
            msg = _("Cannot parse GPX file '%(gpxinputfile)s': %(error)s") % self.dgettext
            self.logger.error(msg)
            tip = _("Check if file is compatible with GPS eXchange Format (GPX)")
            raise Error(msg, tip, exception.__class__.__name__)
        finally:
            self.fd.close()
        return gpxparser


    def end(self, rgo):
        self.state.gpxdata = rgo.gpx
        self.dgettext['num_wpts'] = len(rgo.gpx.waypoints)
        self.dgettext['num_trks'] = len(rgo.gpx.tracks)
        self._notify_end(rgo.gpx)
        msg = _("'%(gpxinputfile)s': %(num_trks)s tracks and %(num_wpts)s waypoints.")
        self.logger.info(msg % self.dgettext)
        return self.state.gpxdata


# EOF
