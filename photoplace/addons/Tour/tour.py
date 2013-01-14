#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       tour.py
#
#       Copyright 2011 Jose Riguera Lopez <jriguera@gmail.com>
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
This add-on makes a visual tour with all photos ....
"""
__program__ = "photoplace.tour"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.3.1"
__date__ = "August 2012"
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
import math

import pyGPX
from PhotoPlace.Plugins.Interface import *
from PhotoPlace.userFacade import TemplateDict
from PhotoPlace.definitions import *


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, u"locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    #gettext.bindtextdomain(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)


# Default values
KmlTour_SPLIT_CHAR = ";"
KmlTour_NAME = _("Play Tour!")
KmlTour_FOLDER = _("Tour")
KmlTour_DESC = ''
KmlTour_MUSIC_MIX = False
KmlTour_MUSIC_URI = ''
KmlTour_BEGIN_NAME = _("Start")
KmlTour_BEGIN_DESC = ''
KmlTour_BEGIN_STYLE = None      # '#tour-first'
KmlTour_END_NAME = _("End")
KmlTour_END_DESC = ''
KmlTour_END_STYLE = None        # '#tour-last'
KmlTour_FLYMODE = "smooth"
KmlTour_ALTMODE = "absolute"
KmlTour_SIMPL = True
KmlTour_SIMPL_DISTANCE = None
KmlTour_FOLLOW_ANGLECORNER = 30.0
KmlTour_TRACK_SIMPLTOLERANCE = 30.0
KmlTour_FLYTIME_LIMIT = 0.001
KmlTour_CRANGE_MINLIMIT = 50
KmlTour_CRANGE_DEFAULTFACTOR = 0.5
KmlTour_TILT_MAXLIMIT = 40
KmlTour_TILT_MINLIMIT = 0

KmlTour_BEGIN_WAIT = 5.0
KmlTour_BEGIN_HEADING = None
KmlTour_BEGIN_FLYTIME = 8.0
KmlTour_BEGIN_TILT = 40.0
KmlTour_BEGIN_RANGE = None
KmlTour_BEGIN_ICON = "http://maps.google.com/mapfiles/kml/shapes/flag.png"
KmlTour_BEGIN_SCALE = 0.8
KmlTour_TILT = 45.0
KmlTour_WAIT = 7.0
KmlTour_FLYTIME = 5.0
KmlTour_HEADING = None
KmlTour_RANGE = None
KmlTour_FOLLOWPATH = True
KmlTour_END_FLYTIME = 5.0
KmlTour_END_HEADING = None
KmlTour_END_TILT = 40.0
KmlTour_END_RANGE = None
KmlTour_END_ICON = "http://maps.google.com/mapfiles/kml/shapes/flag.png"
KmlTour_END_SCALE = 0.8

# Configuration keys
KmlTour_CONFKEY = "tour"
KmlTour_CONFKEY_KMLTOUR_SIMPL = "simplpath"
KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE = "wptsimpldistance"
KmlTour_CONFKEY_KMLTOUR_FOLDER = "foldername"
KmlTour_CONFKEY_KMLTOUR_NAME = "name"
KmlTour_CONFKEY_KMLTOUR_DESC = "description"
KmlTour_CONFKEY_KMLTOUR_MUSIC = "mp3list"
KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX = "mp3mix"
KmlTour_CONFKEY_KMLTOUR_MUSIC_URI = "mp3uri"
KmlTour_CONFKEY_BEGIN_NAME = "beginname"
KmlTour_CONFKEY_BEGIN_DESC = "begindescfile"
KmlTour_CONFKEY_BEGIN_STYLE = "beginstyle"
KmlTour_CONFKEY_BEGIN_ICON = "beginicon"
KmlTour_CONFKEY_BEGIN_SCALE = "beginscale" 
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
KmlTour_CONFKEY_FOLLOWPATH = "followpath"
KmlTour_CONFKEY_END_NAME = "endname"
KmlTour_CONFKEY_END_DESC = "enddescfile"
KmlTour_CONFKEY_END_STYLE = "endstyle"
KmlTour_CONFKEY_END_ICON = "endicon"
KmlTour_CONFKEY_END_SCALE = "endscale" 
KmlTour_CONFKEY_END_HEADING = "endheading"
KmlTour_CONFKEY_END_FLYTIME = "endflytime"
KmlTour_CONFKEY_END_TILT = "endtilt"
KmlTour_CONFKEY_END_RANGE = "endrange"


from KmlgxTour import *



class KmlTour(Plugin):

    description = _(
        "Add-on to generate a visual tour with your photos."
    )
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

    def __init__(self, logger, userfacade, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, userfacade, args, argfiles, gtkbuilder)
        self.options = None
        self.altitude = 0
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
                if h_threshold == None:
                    h_threshold = val
                if l_threshold == None:
                    l_threshold = val
                if val > h_threshold or val < l_threshold:
                    raise UserWarning
                options[key] = val
            except:
                options[key] = value
                dgettext = dict(key=key, value=value)
                self.logger.warning(_("Incorrect value for '%(key)s', "
                    "setting default value '%(value)s'.") % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.warning(_("'%(key)s' not defined, setting "
                "default value '%(value)s'.") % dgettext)


    def _set_option_float_none(self, options, key, value, threshold=(0, None)):
        if options.has_key(key):
            current = options[key]
            if current != None:
                l_threshold = threshold[0]
                h_threshold = threshold[1]
                try:
                    val = float(current)
                    if h_threshold == None:
                        h_threshold = val
                    if l_threshold == None:
                        l_threshold = val
                    if val > h_threshold or val < l_threshold:
                        raise UserWarning
                    options[key] = val
                except:
                    options[key] = value
                    dgettext = dict(key=key, value=value)
                    self.logger.warning(_("Incorrect value for '%(key)s', "
                        "setting default value '%(value)s'.") % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.warning(_("'%(key)s' not defined, setting "
                "default value '%(value)s'.") % dgettext)


    def _set_option_bool(self, options, key, value):
        current = options.setdefault(key, value)
        if not isinstance(current, bool):
            new = current.lower().strip() in ["yes", "true", "on", "si", "1"]
            options[key] = new


    def process_variables(self, options, *args, **kwargs):
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_NAME, KmlTour_NAME)
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_DESC, KmlTour_DESC)
        folder = options.setdefault(KmlTour_CONFKEY_KMLTOUR_FOLDER, KmlTour_FOLDER)
        if folder == "-":
            options[KmlTour_CONFKEY_KMLTOUR_FOLDER] = None
        self._set_option_bool(options, KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX, KmlTour_MUSIC_MIX)
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC_URI, KmlTour_MUSIC_URI)
        mp3s = options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC, [])
        if not isinstance(mp3s, list):
            mp3list = []
            try:
                for mp3 in mp3s.split(KmlTour_SPLIT_CHAR):
                    mp3 = mp3.strip()
                    try:
                        mp3 = unicode(mp3, 'UTF-8')
                    except:
                        pass
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
            filename = os.path.expandvars(os.path.expanduser(filename))
            try:
                filename = unicode(filename, PLATFORMENCODING)
            except:
                pass
            options[KmlTour_CONFKEY_BEGIN_DESC] = filename
        options.setdefault(KmlTour_CONFKEY_BEGIN_STYLE, KmlTour_BEGIN_STYLE)
        options.setdefault(KmlTour_CONFKEY_BEGIN_ICON, KmlTour_BEGIN_ICON)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_SCALE, KmlTour_BEGIN_SCALE, (0.0, 10.0))
        self._set_option_float_none(options, KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE, KmlTour_SIMPL_DISTANCE, (0, 1000000))
        if options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE] == None:
            options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE] = -1
            
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_WAIT, KmlTour_BEGIN_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_HEADING, KmlTour_BEGIN_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_FLYTIME, KmlTour_BEGIN_FLYTIME, (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_TILT, KmlTour_BEGIN_TILT, (0,90))
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_RANGE, KmlTour_BEGIN_RANGE)
        
        self._set_option_float(options, KmlTour_CONFKEY_WAIT, KmlTour_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_HEADING, KmlTour_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_FLYTIME, KmlTour_FLYTIME, (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_TILT, KmlTour_TILT, (0,180))
        self._set_option_float_none(options, KmlTour_CONFKEY_RANGE, KmlTour_RANGE)
        self._set_option_bool(options, KmlTour_CONFKEY_FOLLOWPATH, KmlTour_FOLLOWPATH)
        options.setdefault(KmlTour_CONFKEY_END_NAME, KmlTour_END_NAME)
        filename = options.setdefault(KmlTour_CONFKEY_END_DESC)
        if filename != None:
            filename = os.path.expandvars(os.path.expanduser(filename))
            try:
                filename = unicode(filename, PLATFORMENCODING)
            except:
                pass
            options[KmlTour_CONFKEY_END_DESC] = filename
        options.setdefault(KmlTour_CONFKEY_END_STYLE, KmlTour_END_STYLE)
        options.setdefault(KmlTour_CONFKEY_END_ICON, KmlTour_END_ICON)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_SCALE, KmlTour_END_SCALE, (0.0, 10.0))
        
        self._set_option_float_none(options, KmlTour_CONFKEY_END_HEADING, KmlTour_END_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_END_FLYTIME, KmlTour_END_FLYTIME, (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_END_TILT, KmlTour_END_TILT, (0,90))
        self._set_option_float_none(options, KmlTour_CONFKEY_END_RANGE, KmlTour_END_RANGE)
        
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
        self.logger.debug(_("Starting add-on ..."))


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
        except Exception as e:
            self.logger.error(_("Cannot set mp3 sound files: %s.") % str(e))
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
                    fd = codecs.open(filename, "r", encoding="utf-8")
                    description = fd.read(bytes)
                except Exception as e:
                    self.logger.error(_("Cannot read file: '%s'.") % str(e))
                    if key == KmlTour_CONFKEY_BEGIN_DESC:
                        description = KmlTour_BEGIN_DESC
                    elif key == KmlTour_CONFKEY_END_DESC:
                        description = KmlTour_END_DESC
                finally:
                    if fd:
                        fd.close()
        templatedata = TemplateDict(self.defaultsinfo)
        return description % templatedata


    def bounds(self, geophotos, time_zone=datetime.timedelta(), status=1):
        # firt point for camera
        self.max_lat = -90.0
        self.min_lat = 90.0
        self.max_lon = -180.0
        self.min_lon = 180.0
        self.photos_center_lon = None
        self.photos_center_lat = None
        first_geophoto = None
        last_geophoto = None
        self.altitude = 0
        ready = -1
        num_photo = 0
        for gphoto in geophotos:
            if gphoto.status >= status and gphoto.isGeoLocated():
                if num_photo == 0:
                    first_geophoto = gphoto
                if self.max_lat < gphoto.lat:
                    self.max_lat = gphoto.lat
                if self.min_lat > gphoto.lat:
                    self.min_lat = gphoto.lat
                if self.max_lon < gphoto.lon:
                    self.max_lon = gphoto.lon
                if self.min_lon > gphoto.lon:
                    self.min_lon = gphoto.lon
                last_geophoto = gphoto
                num_photo += 1
        if num_photo > 1:
            self.center_lon = (self.max_lon + self.min_lon)/2.0
            self.center_lat = (self.max_lat + self.min_lat)/2.0
            self.first_lat = first_geophoto.lat
            self.first_lon = first_geophoto.lon
            self.first_ele = first_geophoto.ele
            self.first_time = first_geophoto.time
            self.last_lat = last_geophoto.lat
            self.last_lon = last_geophoto.lon
            self.last_ele = last_geophoto.ele
            self.last_time = last_geophoto.time
            self.photos_center_lon = self.center_lon
            self.photos_center_lat = self.center_lat
            ready = 0
        if self.tracks_points:
            self.first_lat = self.tracks_points[0][0].lat
            self.first_lon = self.tracks_points[0][0].lon
            self.first_ele = self.tracks_points[0][0].ele
            self.first_time = self.tracks_points[0][0].time + time_zone
            self.last_lat = self.tracks_points[-1][-1].lat
            self.last_lon = self.tracks_points[-1][-1].lon
            self.last_ele = self.tracks_points[-1][-1].ele
            self.last_time = self.tracks_points[-1][-1].time + time_zone
            self.center_lon = (self.max_lon + self.min_lon)/2.0
            self.center_lat = (self.max_lat + self.min_lat)/2.0
            ready = 1
        # Calculate the best values for altitude
        altitude = pyGPX.bestViewAltitude(self.max_lat, self.max_lon, self.min_lat, self.min_lon)
        self.options[KmlTour_CONFKEY_RANGE] = altitude
        self.altitude = altitude
        return ready


    def autocalc_range(self, angle, lat, lon):
        # using ellipse polar equation
        angle = 90.0 + angle
        b_distance = self.altitude
        c_distance = pyGPX.distanceCoord(self.center_lat, self.center_lon, lat, lon)
        a_distance = math.sqrt(c_distance * c_distance + b_distance * b_distance)
        eccentricity = float(c_distance) / a_distance
        rangle = math.radians(angle)
        r = (a_distance * (1.0 - eccentricity * eccentricity)) / (1.0 - eccentricity * math.cos(rangle))
        return r


    def set_first(self, str_tzdiff=''):
        begin_name = self.options[KmlTour_CONFKEY_BEGIN_NAME]
        begin_desc = self.get_description(KmlTour_CONFKEY_BEGIN_DESC)
        begin_style = self.options[KmlTour_CONFKEY_BEGIN_STYLE]
        begin_flytime = self.options[KmlTour_CONFKEY_BEGIN_FLYTIME]
        begin_wait = self.options[KmlTour_CONFKEY_BEGIN_WAIT]
        strtime = self.first_time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        
        begin_heading = self.options[KmlTour_CONFKEY_BEGIN_HEADING]
        if begin_heading == None:
            pass
        elif begin_heading == PhotoPlace_estimated:
            begin_heading = pyGPX.bearingCoord(
                self.first_lat, self.first_lon,
                self.center_lat, self.center_lon)
        elif begin_heading == PhotoPlace_default:
            begin_heading = KmlTour_BEGIN_HEADING
        begin_tilt = self.options[KmlTour_CONFKEY_BEGIN_TILT]
        if begin_tilt == None:
            begin_tilt = KmlTour_BEGIN_TILT
        elif begin_tilt == PhotoPlace_estimated:
            begin_tilt = KmlTour_BEGIN_TILT
        elif begin_tilt == PhotoPlace_default:
            begin_tilt = KmlTour_BEGIN_TILT
        begin_range = self.options[KmlTour_CONFKEY_BEGIN_RANGE]
        try:
            distance = float(begin_range)
        except:
            distance = self.autocalc_range(begin_tilt, self.first_lat, self.first_lon)
        #print "FIRST_DISTANCE=", distance
        if begin_style == None or len(begin_style) < 2:
            begin_icon = self.options[KmlTour_CONFKEY_BEGIN_ICON]
            begin_scale = self.options[KmlTour_CONFKEY_BEGIN_SCALE]
            begin_style = datetime.datetime.now().strftime("tour-start" + "%Y%j%I%M")
            self.gxtour.do_placemark_style(begin_style, begin_icon, begin_scale)
            begin_style = '#' + begin_style
        self.gxtour.begin(self.first_lon, self.first_lat, self.first_ele, strtime, begin_name, 
            begin_desc, begin_style, begin_wait, begin_heading, begin_tilt, distance, begin_flytime)


    def set_last(self, last_geophoto, str_tzdiff=''):
        end_name = self.options[KmlTour_CONFKEY_END_NAME]
        end_desc = self.get_description(KmlTour_CONFKEY_END_DESC)
        end_style = self.options[KmlTour_CONFKEY_END_STYLE]
        strtime = self.last_time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        end_flytime = self.options[KmlTour_CONFKEY_END_FLYTIME]
        
        end_heading = self.options[KmlTour_CONFKEY_END_HEADING]
        if end_heading == None:
            pass
        elif end_heading == PhotoPlace_estimated:
            end_heading = pyGPX.bearingCoord(
                self.last_lat, self.last_lon,
                self.center_lat, self.center_lon)
        elif end_heading == PhotoPlace_default:
            end_heading = KmlTour_END_HEADING
        end_tilt = self.options[KmlTour_CONFKEY_END_TILT]
        if end_tilt == None:
            end_tilt = KmlTour_END_TILT
        elif end_tilt == PhotoPlace_estimated:
            end_tilt = KmlTour_END_TILT
        elif end_tilt == PhotoPlace_default:
            end_tilt = KmlTour_END_TILT
        end_range = self.options[KmlTour_CONFKEY_END_RANGE]
        try:
            distance = float(end_range)
        except:
            distance = self.autocalc_range(end_tilt, self.last_lat, self.last_lon)
        #print "FINAL_DISTANCE=", distance
        if last_geophoto:
            epsilon = self.options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE]
            follow = self.options[KmlTour_CONFKEY_FOLLOWPATH]
            if last_geophoto.attr.has_key(KmlTour_CONFKEY_FOLLOWPATH):
                current = last_geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH]
                if isinstance(current, bool):
                    follow = current
                else:
                    current = current.strip()
                    if len(current) < 1:
                        pass
                    elif current == PhotoPlace_estimated:
                        pass
                    elif current == PhotoPlace_default:
                        pass
                    else:
                        follow = current.lower() in ["yes", "true", "on", "si", "1"]
            self.set_path(self.last_lon, self.last_lat, self.last_ele, self.last_time, strtime, 
                          end_flytime, end_tilt, distance, end_heading, epsilon, follow)
        if end_style == None or len(end_style) < 2:
            end_icon = self.options[KmlTour_CONFKEY_END_ICON]
            end_scale = self.options[KmlTour_CONFKEY_END_SCALE]
            end_style = datetime.datetime.now().strftime("tour-end" + "%Y%j%I%M")
            self.gxtour.do_placemark_style(end_style, end_icon, end_scale)
            end_style = '#' + end_style
        self.gxtour.end(self.last_lon, self.last_lat, self.last_ele, strtime,
            end_name, end_desc, end_style, end_heading, end_tilt, distance, end_flytime)


    def simpl_track_DouglasPeucker(self, points, epsilon):
        # epsilon depth in meters is the maximum allowed distance between the poin,
        # and the paht. It is the height of the triangle abc where a-b and b-c are 
        # two consecutive line segments 
        len_points = len(points)
        # indexes of points to include in the simplification
        index = []
        # if one or two points ...
        if len_points < 3:
            return points
        band_sqr = epsilon * 360.0 / (2.0 * math.pi * pyGPX.EarthsRadius)
        band_sqr = band_sqr * band_sqr
        F = math.pi / 360.0
        stack = [(0, len_points-1)]
        while stack:
            start, end = stack.pop()
            if (end - start) > 1:
                # intermediate points, find most distant intermediate point
                # with the line from start to end points 
                x12 = (points[end].lon - points[start].lon)
                y12 = (points[end].lat - points[start].lat)
                if math.fabs(x12) > 180.0:
                    x12 = 360.0 - math.fabs(x12)
                x12 *= math.cos(F * (points[end].lat + points[start].lat))
                d12 = (x12*x12) + (y12*y12)

                sig = start
                max_dev_sqr = -1.0
                for i in xrange(start + 1, end):
                    x13 = (points[i].lon - points[start].lon)
                    y13 = (points[i].lat - points[start].lat)
                    if math.fabs(x13) > 180.0:
                        x13 = 360.0 - math.fabs(x13)
                    x13 *= math.cos(F * (points[i].lat + points[start].lat))
                    d13 = (x13*x13) + (y13*y13)
                    x23 = (points[i].lon - points[end].lon)
                    y23 = (points[i].lat - points[end].lat)
                    if math.fabs(x23) > 180.0:
                        x23 = 360.0 - math.fabs(x23)
                    x23 *= math.cos(F * (points[i].lat + points[end].lat))
                    d23 = (x23*x23) + (y23*y23)
                    if d13 >= (d12 + d23):
                        dev_sqr = d23
                    elif d23 >= (d12 + d13):
                        dev_sqr = d13
                    else:
                        # solve triangle
                        dev_sqr = (x13 * y12 - y13 * x12) * (x13 * y12 - y13 * x12) / d12
                    if dev_sqr > max_dev_sqr:
                        sig = i;
                        max_dev_sqr = dev_sqr;
                if max_dev_sqr < band_sqr:
                    # no sig. intermediate point, transfer current start point 
                    index.append(start)
                else:
                    stack.append((sig, end))
                    stack.append((start, sig))
            else:
                index.append(start)
        # last point
        index.append(len_points-1)
        return [points[i] for i in index]


    # defautl method
    def get_track_bytime(self, prev_time, time):
        found_first = False
        found_last = False
        not_last = False
        to_back = False
        points = []
        len_tracks = len(self.tracks_points)
        while self.tracks_pos < len_tracks:
            path = self.tracks_points[self.tracks_pos]
            path_len = len(path)
            for pos in xrange(self.points_pos, path_len):
                point = path[pos]
                if found_first:
                    points.append(point)
                    if point.time == time:
                        found_last = True
                        break
                    elif point.time > time:
                        not_last = True
                        found_last = True
                        break
                else:
                    if point.time == prev_time:
                        found_first = True
                        points.append(point)
                        if point.time == time:
                            found_last = True
                            break
                    elif point.time > prev_time:
                        # opps, we are in the future!
                        if path[0].time > prev_time:
                            # opps, back to the past into prev track
                            to_back = True
                            break
                        else:
                            # the present is in that track
                            for auxpos in xrange(0, pos+1):
                                if path[auxpos].time >= prev_time:
                                    points.append(path[auxpos])
                                    if path[auxpos].time <= time:
                                        found_last = True
                                        self.points_pos = auxpos
                                        break
                            found_first = True
                            if found_last:
                                break
                self.points_pos = pos
            if found_last:
                break
            if to_back:
                self.tracks_pos -= 1
                self.points_pos = 0
                to_back = False
                if self.tracks_pos < 0:
                    # no data!
                    break
            self.points_pos = 0
            self.tracks_pos += 1
        return points


    def get_track_bypos(self, prev_lon, prev_lat, lon, lat):
        found_first = False
        found_last = False
        points = []
        while self.tracks_pos < len(self.tracks_points):
            path = self.tracks_points[self.tracks_pos]
            path_len = len(path)
            while self.points_pos < path_len:
                point = path[self.points_pos]
                if found_first:
                    points.append(point)
                    if point.lat == lat and point.lon == lon:
                        found_last = True
                        break
                else:
                    if point.lat == prev_lat and point.lon == prev_lon:
                        found_first = True
                        points.append(point)
                        if point.lat == lat and point.lon == lon:
                            found_last = True
                            break
                    elif point.lat == lat and point.lon == lon:
                        points = points + path[:self.points_pos + 1]
                        found_last = True
                        break
                self.points_pos += 1
            if found_last:
                break
            self.points_pos = 0
            self.tracks_pos += 1
        return points


    def get_track(self, prev_lon, prev_lat, prev_time, lon, lat, time):
        points = []
        if prev_time != None and time != None:
            points = self.get_track_bytime(prev_time, time)
        else:
            points = self.get_track_bypos(prev_lon, prev_lat, lon, lat)
        result = []
        len_points = len(points)
        if len_points > 1:
            result = [points[0]]
            for position in xrange(1, len_points):
                current = points[position]
                previous = points[position - 1]
                if current.lat != previous.lat or current.lon != previous.lon:
                    result.append(current)
        else:
            result = points
        return result


    def set_path(self, lon, lat, ele, time, strtime,
        fly_time, fly_tilt, fly_crange, fly_bearing, simpl_distance=None, follow_path=True):

        print "proceso:"
        points = []
        points_len = 0
        total_distance = pyGPX.distanceCoord(self.prev_lat, self.prev_lon, lat, lon)
        if fly_crange == None:
            # h proportional between altitude and Min Limit (50m)
            if self.prev_d <= 1:
                camera = self.prev_h
            else:
                camera = total_distance * self.prev_h / self.prev_d
            if camera > self.altitude:
                crange = self.altitude
            elif camera < KmlTour_CRANGE_MINLIMIT:
                crange = KmlTour_CRANGE_MINLIMIT
            else:
                crange = camera
        else:
            crange = fly_crange
        print "RANGE", crange
        if fly_tilt == None:
            if crange == self.altitude:
                tilt = KmlTour_TILT_MAXLIMIT
            elif crange == KmlTour_CRANGE_MINLIMIT:
                tilt = KmlTour_TILT_MINLIMIT
            else:
                tilt = (crange - KmlTour_CRANGE_MINLIMIT) / (self.altitude - KmlTour_CRANGE_MINLIMIT) * KmlTour_TILT_MAXLIMIT
        else:
            tilt = fly_tilt
        print "TILT", tilt
        self.prev_h = crange
        self.prev_d = total_distance
        self.prev_t = tilt
        print "1"
        if follow_path and self.prev_time != None and time != None:
            points = self.get_track(self.prev_lon, self.prev_lat, self.prev_time, lon, lat, time)
            points_len = len(points)
            if points_len > 0:
                epsilon = simpl_distance
                if simpl_distance == None or simpl_distance < 0:
                    epsilon = crange / KmlTour_TRACK_SIMPLTOLERANCE
                    if epsilon < 0.5:
                        epsilon = 0.5
                if epsilon > 0:
                    points = self.simpl_track_DouglasPeucker(points, epsilon)
                points_len = len(points)
        print "2"
        if points_len > 1:
            total_distance = 0.0
            for pos in xrange(1, points_len):
                prev = points[pos - 1]
                current = points[pos]
                total_distance += prev.distance(current)
            total_speed = total_distance / float(fly_time)
            for pos in xrange(0, points_len-1):
                next = points[pos + 1]
                current = points[pos]
                distance = current.distance(next)
                flytime = distance / total_speed
                heading = fly_bearing
                if fly_bearing == None:
                    heading = current.bearing(next.lat, next.lon)
                if pos == 0:
                    old_heading = heading
                elif abs(old_heading - heading) >= KmlTour_FOLLOW_ANGLECORNER:
                    self.gxtour.do_flyto(current.lon, current.lat, current.ele, 
                        strtime, heading, tilt, crange, flytime)
                old_heading = heading
                self.gxtour.do_flyto(next.lon, next.lat, next.ele, 
                    strtime, heading, tilt, crange, flytime)
        else:
            heading = fly_bearing
            if fly_bearing == None:
                heading = pyGPX.bearingCoord(self.prev_lat, self.prev_lon, lat, lon)
            flytime = fly_time
            self.gxtour.do_flyto(lon, lat, ele, strtime, heading, tilt, crange, flytime)
        print "FIN"
        self.prev_lat = lat
        self.prev_lon = lon
        self.prev_ele = ele
        self.prev_time = time


    @DRegister("LoadPhotos:run")
    def load_photo(self, geophoto, *args, **kwargs):
        #geophoto.attr[KmlTour_CONFKEY_WAIT] = self.options[KmlTour_CONFKEY_WAIT]
        geophoto.attr[KmlTour_CONFKEY_WAIT] = PhotoPlace_default
        if self.options[KmlTour_CONFKEY_HEADING] == None:
            geophoto.attr[KmlTour_CONFKEY_HEADING] = PhotoPlace_estimated
        else:
            geophoto.attr[KmlTour_CONFKEY_HEADING] = self.options[KmlTour_CONFKEY_HEADING]
        #geophoto.attr[KmlTour_CONFKEY_FLYTIME] = self.options[KmlTour_CONFKEY_FLYTIME]
        geophoto.attr[KmlTour_CONFKEY_FLYTIME] = PhotoPlace_default
        #geophoto.attr[KmlTour_CONFKEY_TILT] = self.options[KmlTour_CONFKEY_TILT]
        geophoto.attr[KmlTour_CONFKEY_TILT] = PhotoPlace_estimated
        #geophoto.attr[KmlTour_CONFKEY_TILT] = PhotoPlace_default
        #geophoto.attr[KmlTour_CONFKEY_RANGE] = self.options[KmlTour_CONFKEY_RANGE]
        geophoto.attr[KmlTour_CONFKEY_RANGE] = PhotoPlace_estimated 
        #geophoto.attr[KmlTour_CONFKEY_RANGE] = PhotoPlace_default
        #geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH] = int(self.options[KmlTour_CONFKEY_FOLLOWPATH])
        geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH] = PhotoPlace_default


    def get_geophoto_attr(self, geophoto, key, default=None, estimated=None):
        value = self.options[key]
        try:
            gvalue = geophoto.attr[key]
            if isinstance(gvalue, str):
                gvalue = gvalue.strip()
                if gvalue == PhotoPlace_estimated:
                    value = estimated
                elif gvalue == PhotoPlace_default:
                    value = default
                else:
                    value = float(gvalue)
            else:
                value = gvalue
        except:
            dgettext['attr'] = key
            self.logger.debug(msg_warning % dgettext)
        return value


    @DRegister("MakeKML:end")
    def process_end(self, num_photos, *args, **kwargs):
        if not self.ready:
            return
        utczoneminutes = self.state['utczoneminutes']
        time_zone = datetime.timedelta(minutes=utczoneminutes)
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
        epsilon = self.options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE]
        kml = self.state.kmldata.getKml()
        if not kml:
            self.ready = 0
            self.logger.debug(_("No KML output! Cowardly refusing to create a tour!"))
            return
        self.gxtour.ini(name, description, kml, folder)
        # get all points
        self.tracks_points = []
        self.tracks_pos = 0
        self.points_pos = 0
        if self.state.gpxdata:
            for track in self.state.gpxdata.tracks:
                if track.status:
                    self.tracks_points.append(track.listpoints())
        mode = self.bounds(self.state.geophotos, time_zone)
        if mode == -1:
            self.ready = 0
            self.logger.debug(_("No data! Cowardly refusing to create a tour!"))
            return
        elif mode == 0:
            first_time = self.state.geophotos[0].time
        elif mode == 1:
            # gpx data
            first_time = self.tracks_points[0][0].time
        # firt point for camera
        self.set_first(str_tzdiff)
        self.prev_h = 1.0
        self.prev_d = 2.0
        self.prev_t = self.options[KmlTour_CONFKEY_TILT]
        self.prev_lat = self.first_lat
        self.prev_lon = self.first_lon
        self.prev_ele = self.first_ele
        self.prev_time = first_time
        last_geophoto = None
        dgettext = dict()
        msg_warning = _("Warning processing '%(name)s.%(attr)s': attribute type not valid!")
        for geophoto in self.state.geophotos:
            if geophoto.status < 1 or not geophoto.isGeoLocated():
                # not selected
                continue
            dgettext['name'] = geophoto.name
            wait = self.options[KmlTour_CONFKEY_WAIT]
            wait = self.get_geophoto_attr(geophoto, KmlTour_CONFKEY_WAIT, wait, wait)
            bearing = self.options[KmlTour_CONFKEY_HEADING]
            bearing = self.get_geophoto_attr(geophoto, KmlTour_CONFKEY_HEADING, bearing, None)
            flytime = self.options[KmlTour_CONFKEY_FLYTIME]
            flytime = self.get_geophoto_attr(geophoto, KmlTour_CONFKEY_FLYTIME, flytime, flytime)
            tilt = self.options[KmlTour_CONFKEY_TILT]
            tilt = self.get_geophoto_attr(geophoto, KmlTour_CONFKEY_TILT, tilt, None)
            crange = self.options[KmlTour_CONFKEY_RANGE]
            crange = self.get_geophoto_attr(geophoto, KmlTour_CONFKEY_RANGE, crange, None)
            follow = self.options[KmlTour_CONFKEY_FOLLOWPATH]
            if geophoto.attr.has_key(KmlTour_CONFKEY_FOLLOWPATH):
                current = geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH]
                if isinstance(current, bool):
                    follow = current
                else:
                    current = current.strip()
                    if len(current) < 1:
                        pass
                    elif current == PhotoPlace_estimated:
                        pass
                    elif current == PhotoPlace_default:
                        pass
                    else:
                        follow = current.lower() in ["yes", "true", "on", "si", "1"]
            strtime = geophoto.time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
            self.set_path(geophoto.lon, geophoto.lat, geophoto.ele, geophoto.ptime, strtime, 
                          flytime, tilt, crange, bearing, epsilon, follow)
            self.gxtour.do_balloon(geophoto.name)
            self.gxtour.do_wait(wait)
            self.gxtour.do_balloon(geophoto.name, False)
            self.gxtour.music()
            last_geophoto = geophoto
        # track to last point
        self.set_last(last_geophoto, str_tzdiff)


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


    def reset(self):
        if self.ready:
            self.gxtour = None
            self.traks_points = []
            self.tracks_pos = 0
            self.points_pos = 0
            self.logger.debug(_("Resetting add-on ..."))


    def end(self, options):
        self.ready = 0
        self.gxtour = None
        self.options = None
        self.tracks_points = []
        self.tracks_pos = 0
        self.points_pos = 0
        self.altitude = 0
        if self.gui:
            self.gui.hide()
        self.logger.debug(_("Ending add-on ..."))


# EOF
