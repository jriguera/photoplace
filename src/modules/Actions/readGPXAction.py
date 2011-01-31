#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       readGPXAction.py
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
import codecs
import urllib

import gpx

from userFacade import Error
import Actions.Interface



class ReadGPX(Actions.Interface.Action, threading.Thread):

    def __init__(self, state):
        Actions.Interface.Action.__init__(self, state, [state.lock_gpxdata])
        threading.Thread.__init__(self)
        self.gpxinputfile = state['gpxinputfile']
        self.dgettext['gpxinputfile'] = self.gpxinputfile
        #self.utczoneminutes = state['utczoneminutes']
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
        #self.utc_time_delta = datetime.timedelta(minutes=self.utczoneminutes)


    def ini(self, *args, **kwargs):
        #self._notify_ini(self.fd, self.utc_time_delta)
        self._notify_ini(self.fd)
        #self.dgettext['utc_time_delta'] = self.utc_time_delta
        msg = _("Processing GPX data from '%(gpxinputfile)s' ...")
        self.logger.info(msg % self.dgettext)
        return self.state.gpxdata


    def go(self, rini):
        try:
            gpxparser = gpx.GPXParser(self.fd, os.path.basename(self.gpxinputfile))
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
        msg = msg % self.dgettext
        self.logger.info(msg)
        return self.state.gpxdata


# EOF
