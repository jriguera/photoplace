#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       tour.py
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
This plugin makes a visual tour with all pictures ....
"""
__program__ = "photoplace.tour"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.1"
__date__ = "December 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import codecs
import shutil
import getpass
import datetime
import gettext
import locale
import urlparse
import warnings
warnings.filterwarnings('ignore', module='gtk')
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except Exception as e:
    warnings.resetwarnings()
    print("Warning: %s" % str(e))
    print("You don't have the PyGTK 2.0 module installed")
    raise
warnings.resetwarnings()


from Plugins.Interface import *
import DataTypes.kmlData
import gpx
from userFacade import TemplateDict
from definitions import *


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.dirname(__file__)
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
except Exception as e:
    _ = lambda s: s
    print("Error setting up the translations: %s" % (e))


# Default values
KmlTour_SPLIT_CHAR = ";"
KmlTour_NAME = _("Play me")
KmlTour_DESC = _("A visual tour")
KmlTour_FOLDER = _("Tour")
KmlTour_KMLTOUR_MUSIC_MIX = False
KmlTour_MUSIC_URI = ''
KmlTour_BEGIN_NAME = _("Start")
KmlTour_BEGIN_DESC = _("Presentation ...")
KmlTour_BEGIN_STYLE =  '#tour-first'
KmlTour_END_NAME = _("End")
KmlTour_END_DESC = _("The end ...")
KmlTour_END_STYLE = '#tour-last'
KmlTour_FLYMODE = "smooth"
KmlTour_ALTMODE = "absolute"

KmlTour_BEGIN_WAIT = 10.0
KmlTour_BEGIN_HEADING = None
KmlTour_BEGIN_FLYTIME = 8.0
KmlTour_BEGIN_TILT = 80.0
KmlTour_BEGIN_RANGE = 5000.0
KmlTour_TILT = 30.0
KmlTour_WAIT = 7.0
KmlTour_FLYTIME = 4.0
KmlTour_HEADING = None
KmlTour_RANGE = 1000.0
KmlTour_END_FLYTIME = 5.0
KmlTour_END_HEADING = None
KmlTour_END_TILT = 80.0
KmlTour_END_RANGE = 1000.0

# Configuration keys
KmlTour_CONFKEY = "tour"
KmlTour_CONFKEY_KMLTOUR_FOLDER = "foldername"
KmlTour_CONFKEY_KMLTOUR_NAME = "name"
KmlTour_CONFKEY_KMLTOUR_DESC = "description"
KmlTour_CONFKEY_KMLTOUR_MUSIC = "mp3list"
KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX = "mp3mix"
KmlTour_CONFKEY_KMLTOUR_MUSIC_URI = "mp3uri"
KmlTour_CONFKEY_BEGIN_NAME = "beginname"
KmlTour_CONFKEY_BEGIN_DESC = "begindescfile"
KmlTour_CONFKEY_BEGIN_STYLE = "beginstyle"
KmlTour_CONFKEY_BEGIN_WAIT = "beginwait"
KmlTour_CONFKEY_BEGIN_HEADING = "beginheading"
KmlTour_CONFKEY_BEGIN_FLYTIME = "beginflytime"
KmlTour_CONFKEY_BEGIN_TILT = "begintilt"
KmlTour_CONFKEY_BEGIN_RANGE = "beginrange"
KmlTour_CONFKEY_WAIT = "wait"
KmlTour_CONFKEY_HEADING = "heading"
KmlTour_CONFKEY_FLYTIME = "flytime"
KmlTour_CONFKEY_TILT = "tilt"
KmlTour_CONFKEY_RANGE = "range"
KmlTour_CONFKEY_END_NAME = "endname"
KmlTour_CONFKEY_END_DESC = "enddescfile"
KmlTour_CONFKEY_END_STYLE = "endstyle"
KmlTour_CONFKEY_END_HEADING = "endheading"
KmlTour_CONFKEY_END_FLYTIME = "endflytime"
KmlTour_CONFKEY_END_TILT = "endtilt"
KmlTour_CONFKEY_END_RANGE = "endrange"


from KmlgxTour import *



class KmlTour(Plugin):

    description = _("A plugin to generate a visual tour with your photos.")
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://code.google.com/p/photoplace/"
    version = __version__
    copyright = __copyright__
    date = __date__
    license = __license__
    capabilities = {
        'GUI' : PLUGIN_GUI_GTK,
        'NeedGUI' : False,
    }
    
    def __init__(self, logger, state, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, state, args, argfiles, gtkbuilder)
        self.options = dict()
        # GTK widgets
        self.gui = None
        if gtkbuilder:
            import GTKtour
            self.gui = GTKtour.GTKTour(gtkbuilder, logger)
        self.ready = -1


    def _set_option_float(self, options, key, value, threshold=(0, None)):
        if options.has_key(key):
            try:
                val = float(options[key])
                l_threshold = threshold[0]
                h_threshold = threshold[1]
                if not h_threshold:
                    h_threshold = val
                if not l_threshold:
                    l_threshold = val
                if val > h_threshold or val < l_threshold:
                    raise UserWarning
                options[key] = val
            except:
                options[key] = value
                dgettext = dict(key=key, value=value)
                self.logger.debug(_("Incorrect value for '%(key)s', "
                    "setting default value '%(value)s'.") % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.debug(_("'%(key)s' not defined, setting "
                "default value '%(value)s'.") % dgettext)


    def _set_option_float_none(self, options, key, value, threshold=(0, None)):
        if options.has_key(key):
            current = options[key]
            if current:
                l_threshold = threshold[0]
                h_threshold = threshold[1]
                try:
                    val = float(current)
                    if not h_threshold:
                        h_threshold = val
                    if not l_threshold:
                        l_threshold = val
                    if val > h_threshold or val < l_threshold:
                        raise UserWarning
                    options[key] = val
                except:
                    options[key] = value
                    dgettext = dict(key=key, value=value)
                    self.logger.debug(_("Incorrect value for '%(key)s', "
                        "setting default value '%(value)s'.") % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.debug(_("'%(key)s' not defined, setting "
                "default value '%(value)s'.") % dgettext)


    def process_variables(self, options, *args, **kwargs):
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_NAME, KmlTour_NAME)
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_DESC, KmlTour_DESC)
        folder = options.setdefault(KmlTour_CONFKEY_KMLTOUR_FOLDER, KmlTour_FOLDER)
        if folder == "-":
            options[KmlTour_CONFKEY_KMLTOUR_FOLDER] = None
        mix = options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX, KmlTour_KMLTOUR_MUSIC_MIX)
        if not isinstance(mix, bool):
            mp3mix = mix.lower().strip() in ["yes", "true", "si", "1"]
            options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX] = mp3mix
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC_URI, KmlTour_MUSIC_URI)
        mp3s = options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC, [])
        if not isinstance(mp3s, list):
            mp3list = []
            try:
                for mp3 in mp3s.split(KmlTour_SPLIT_CHAR):
                    mp3 = mp3.strip()
                    if os.path.isfile(mp3):
                        mp3list.append(mp3)
                    else:
                        self.logger.error(_("Cannot read mp3 file '%s'.") % mp3)
            except:
                self.logger.error(_("Incorrect value for '%s'.") % KmlTour_CONFKEY_KMLTOUR_MUSIC)
            options[KmlTour_CONFKEY_KMLTOUR_MUSIC] = mp3list
        # Placemarks
        options.setdefault(KmlTour_CONFKEY_BEGIN_NAME, KmlTour_BEGIN_NAME)
        filename = options.setdefault(KmlTour_CONFKEY_BEGIN_DESC)
        if filename != None:
            options[KmlTour_CONFKEY_BEGIN_DESC] = os.path.expandvars(os.path.expanduser(filename))
        options.setdefault(KmlTour_CONFKEY_BEGIN_STYLE, KmlTour_BEGIN_STYLE)
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_WAIT, KmlTour_BEGIN_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_HEADING, KmlTour_BEGIN_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_FLYTIME, KmlTour_BEGIN_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_TILT, KmlTour_BEGIN_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_RANGE, KmlTour_BEGIN_RANGE)
        self._set_option_float(options, KmlTour_CONFKEY_WAIT, KmlTour_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_HEADING, KmlTour_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_FLYTIME, KmlTour_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_TILT, KmlTour_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_RANGE, KmlTour_RANGE)
        options.setdefault(KmlTour_CONFKEY_END_NAME, KmlTour_END_NAME)
        filename = options.setdefault(KmlTour_CONFKEY_END_DESC)
        if filename != None:
            options[KmlTour_CONFKEY_END_DESC] = os.path.expandvars(os.path.expanduser(filename))
        options.setdefault(KmlTour_CONFKEY_END_STYLE, KmlTour_END_STYLE)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_HEADING, KmlTour_END_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_END_FLYTIME, KmlTour_END_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_TILT, KmlTour_END_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_END_RANGE, KmlTour_END_RANGE)
        self.options = options


    def init(self, options, widget):
        if not options.has_key(KmlTour_CONFKEY):
            options[KmlTour_CONFKEY] = dict()
        self.defaultsinfo = options['defaults']
        opt = options[KmlTour_CONFKEY]
        self.process_variables(opt)
        if self.gui:
            if self.ready == -1:
                # 1st time
                self.gui.show(widget, opt)
            else:
                self.gui.show(None, opt)
        self.ready = 1
        self.logger.debug(_("Starting plugin ..."))


    @DRegister("MakeKML:ini")
    def process_ini(self, *args, **kwargs):
        if not self.ready or not self.state.kmldata:
            self.ready = 0
            return
        mp3list = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC]
        mp3mix = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX]
        mp3uri = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_URI]
        try:
            self.gxtour = gxTour(mp3list, mp3mix, mp3uri)
        except Exception as exception:
            self.logger.error(_("Cannot set mp3 sound files: %s.") % str(exception))
            self.gxtour = gxTour([], False, mp3uri)


    def get_description(self, key, bytes=102400):
        description = ''
        if self.gui:
            description = self.gui.get_textview(key)
        else:
            filename = self.options[key]
            if filename != None:
                fd = None
                try:
                    fd = open(filename, "r")
                    description = fd.read(bytes)
                except Exception as exception:
                    self.logger.error(_("Cannot read file '%s'.") % str(exception))
                    if key == KmlTour_CONFKEY_BEGIN_DESC:
                        description = KmlTour_BEGIN_DESC
                    elif key == KmlTour_CONFKEY_END_DESC:
                        description = KmlTour_END_DESC
                finally:
                    if fd:
                        fd.close()
        templatedata = TemplateDict(self.defaultsinfo)
        return description % templatedata


    def set_first(self, str_tzdiff=''):
        # firt point for camera
        geophoto = None
        num_photo = 0
        max_lat = -90.0
        min_lat = 90.0
        max_lon = -180.0
        min_lon = 180.0
        for gphoto in self.state.geophotos:
            if gphoto.status > 0 and gphoto.isGeoLocated():
                if num_photo == 0:
                    geophoto = gphoto
                if max_lat < geophoto.lat:
                    max_lat = geophoto.lat
                if min_lat > geophoto.lat:
                    min_lat = geophoto.lat
                if max_lon < geophoto.lon:
                    max_lon = geophoto.lon
                if min_lon > geophoto.lon:
                    min_lon = geophoto.lon
                num_photo += 1
        if num_photo < 1:
            self.logger.debug(_("No photos to process!"))
            return None
        self.center_lon = (max_lon + min_lon)/2.0
        self.center_lat = (max_lat + min_lat)/2.0
        self.first_lat = geophoto.lat
        self.first_lon = geophoto.lon
        self.first_ele = geophoto.ele
        time = geophoto.time
        if self.state.gpxdata:
            found = False
            for track in self.state.gpxdata.tracks:
                points = track.listpoints()
                for point in points:
                    if self.first_lat == point.lat and self.first_lon == point.lon:
                        self.first_lat = points[0].lat
                        self.first_lon = points[0].lon
                        self.first_ele = points[0].ele
                        time = points[0].time
                        found = True
                        break
                if found:
                    # we have the first point
                    break
        begin_name = self.options[KmlTour_CONFKEY_BEGIN_NAME]
        begin_style = self.options[KmlTour_CONFKEY_BEGIN_STYLE]
        begin_wait = self.options[KmlTour_CONFKEY_BEGIN_WAIT]
        begin_heading = self.options[KmlTour_CONFKEY_BEGIN_HEADING]
        begin_flytime = self.options[KmlTour_CONFKEY_BEGIN_FLYTIME]
        begin_tilt = self.options[KmlTour_CONFKEY_BEGIN_TILT]
        begin_range = self.options[KmlTour_CONFKEY_BEGIN_RANGE]
        begin_desc = self.get_description(KmlTour_CONFKEY_BEGIN_DESC)
        strtime = time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        if not begin_heading:
            begin_heading = gpx.bearingCoord(
                self.center_lat, self.center_lon, 
                self.first_lat, self.first_lon)
        if begin_range <= 10:
            distance = gpx.distanceCoord(
                self.center_lat, self.center_lon, 
                self.first_lat, self.first_lon)
            distance = distance * begin_range
        else:
            distance = begin_range
        self.gxtour.begin(self.first_lon, self.first_lat, self.first_ele, strtime, 
            begin_name, begin_desc, begin_style, begin_wait, begin_heading, 
            begin_tilt, distance, begin_flytime)
        return geophoto


    def set_last(self, str_tzdiff=''):
        num_photo = len(self.state.geophotos) - 1
        geophoto = None
        while num_photo >= 0:
            gphoto = self.state.geophotos[num_photo]
            if gphoto.status > 0 and gphoto.isGeoLocated():
                geophoto = gphoto
                break
            num_photo -= 1
        if num_photo < 0:
            self.logger.debug(_("No photos to process!"))
            return None
        self.last_lat = geophoto.lat
        self.last_lon = geophoto.lon
        self.last_ele = geophoto.ele
        time = geophoto.time
        if self.state.gpxdata:
            found = False
            for track in self.state.gpxdata.tracks:
                points = track.listpoints()
                for point in points:
                    if self.last_lat == point.lat and self.last_lon == point.lon:
                        self.last_lat = points[-1].lat
                        self.last_lon = points[-1].lon
                        self.last_ele = points[-1].ele
                        time = points[-1].time
                        found = True
                        break
                if found:
                    break
        end_name = self.options[KmlTour_CONFKEY_END_NAME]
        end_style = self.options[KmlTour_CONFKEY_END_STYLE]
        end_heading = self.options[KmlTour_CONFKEY_END_HEADING]
        end_flytime = self.options[KmlTour_CONFKEY_END_FLYTIME]
        end_tilt = self.options[KmlTour_CONFKEY_END_TILT]
        end_range = self.options[KmlTour_CONFKEY_END_RANGE]
        end_desc = self.get_description(KmlTour_CONFKEY_END_DESC)
        strtime = time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        if not end_heading:
            end_heading = gpx.bearingCoord(
                self.center_lat, self.center_lon, 
                self.last_lat, self.last_lon)
        if end_range <= 10:
            distance = gpx.distanceCoord(
                self.center_lat, self.center_lon, 
                self.last_lat, self.last_lon)
            distance = distance * end_range
        else:
            distance = end_range
        self.gxtour.end(self.last_lon, self.last_lat, self.last_ele, strtime,
            end_name, end_desc, end_style, end_heading,
            end_tilt, distance, end_flytime)
        return geophoto


    @DRegister("MakeKML:end")
    def process_end(self, num_photos, *args, **kwargs):
        if not self.ready:
            return
        utczoneminutes = self.state['utczoneminutes']
        str_tzdiff = '-'
        if utczoneminutes < 0:
            utczoneminutes = -utczoneminutes
            str_tzdiff = '+'
        hours, remainder = divmod(utczoneminutes, 60)
        minutes, seconds = divmod(remainder, 60)
        str_tzdiff = str_tzdiff + "%.2d:%.2d" % (hours, minutes)
        name = self.options[KmlTour_CONFKEY_KMLTOUR_NAME]
        description = self.options[KmlTour_CONFKEY_KMLTOUR_DESC]
        folder = self.options[KmlTour_CONFKEY_KMLTOUR_FOLDER]
        wait = self.options[KmlTour_CONFKEY_WAIT]
        heading = self.options[KmlTour_CONFKEY_HEADING]
        flytime = self.options[KmlTour_CONFKEY_FLYTIME]
        tilt = self.options[KmlTour_CONFKEY_TILT]
        crange = self.options[KmlTour_CONFKEY_RANGE]
        kml = self.state.kmldata.getKml()
        if not kml:
            self.ready = 0
            self.logger.debug(_("No KML output! Cowardly refusing to create a tour!"))
            return
        self.gxtour.ini(name, description, kml, folder)
        # firt point for camera
        geophoto = self.set_first(str_tzdiff)
        if not geophoto:
            self.ready = 0
            self.logger.debug(_("No photos! Cowardly refusing to create a tour!"))
            return
        previous = (geophoto.lat, geophoto.lon, geophoto.ele)
        for geophoto in self.state.geophotos:
            if geophoto.status < 1:
                # not selected
                continue
            lat = geophoto.lat
            lon = geophoto.lon
            ele = geophoto.ele
            name = geophoto.name
            strtime = geophoto.time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
            if not heading:
                heading = gpx.bearingCoord(previous[0], previous[1], lat, lon)
            if crange <= 10:
                distance = gpx.distanceCoord(previous[0], previous[1], lat, lon)
                distance = distance * crange
            else:
                distance = crange
            self.gxtour.do_flyto(lon, lat, ele, strtime, heading, tilt, distance, flytime)
            self.gxtour.do_balloon(name)
            self.gxtour.do_wait(wait)
            self.gxtour.do_balloon(name, False)
            self.gxtour.music()
            previous = (lat, lon, ele)
        # last point
        self.set_last(str_tzdiff)


    @DRegister("SaveFiles:ini")
    def save(self, fd, outputkml, outputkmz, photouri, outputdir, quality):
        if not self.ready:
            return
        dgettext = dict()
        try:
            outdir = os.path.dirname(outputkml)
            for mp3 in self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC]:
                basefile = os.path.basename(mp3)
                dgettext['outputfile'] = os.path.join(outdir, basefile)
                shutil.copy(mp3, dgettext['outputfile'])
        except Exception as exception:
            dgettext['error'] = str(exception)
            msg = _("Cannot create '%(outputfile)s' for writing: %(error)s.")
            self.logger.error(msg % dgettext)
            raise


    def end(self, options):
        self.ready = 0
        self.gxtour = None
        self.options = None
        if self.gui:
            self.gui.hide()
        self.logger.debug(_("Ending plugin ..."))


# EOF
