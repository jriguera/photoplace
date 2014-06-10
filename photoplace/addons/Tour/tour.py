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
__version__ = "0.5.0"
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
from PhotoPlace.Facade import TemplateDict
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
KmlTour_TRACK_SIMPLTOLERANCE = 2.0 # 1%
KmlTour_FLYTIME_LIMIT = 0.001
KmlTour_CRANGE_MINLIMIT = 100.0
KmlTour_CRANGE_MAXLIMIT = 5000.0
KmlTour_CRANGE_DEFAULTFACTOR = 0.5
KmlTour_TILT_MAXLIMIT = 45.0
KmlTour_TILT_MINLIMIT = 20.0
KmlTour_FROM_FIRST_PHOTO = False
KmlTour_TO_LAST_PHOTO = False
KmlTour_COPYMUSIC = True

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
KmlTour_CONFKEY_KMLTOUR_COPYMUSIC = "copymp3"
KmlTour_CONFKEY_KMLTOUR_MUSIC = "mp3list"
KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX = "mp3mix"
KmlTour_CONFKEY_KMLTOUR_MUSIC_URI = "mp3uri"
KmlTour_CONFKEY_KMLTOUR_FIRST_PHOTO = "fromfirstphoto"
KmlTour_CONFKEY_KMLTOUR_LAST_PHOTO = "tolastphoto"

KmlTour_CONFKEY_BEGIN_NAME = "start_name"
KmlTour_CONFKEY_BEGIN_DESC = "start_desc_file"
KmlTour_CONFKEY_BEGIN_DESC_TEXT = "start_desc"
KmlTour_CONFKEY_BEGIN_STYLE = "start_style"
KmlTour_CONFKEY_BEGIN_ICON = "start_icon"
KmlTour_CONFKEY_BEGIN_SCALE = "start_scale"

KmlTour_CONFKEY_BEGIN_WAIT = "start_camera_wait"
KmlTour_CONFKEY_BEGIN_HEADING = "start_camera_heading"
KmlTour_CONFKEY_BEGIN_FLYTIME = "start_camera_fly_time"
KmlTour_CONFKEY_BEGIN_TILT = "start_camera_tilt"
KmlTour_CONFKEY_BEGIN_RANGE = "start_camera_range"

KmlTour_CONFKEY_KMLTOUR_RANGE_MAX = "camera_range_max"
KmlTour_CONFKEY_KMLTOUR_RANGE_MIN = "camera_range_min"
KmlTour_CONFKEY_KMLTOUR_TILT_MAX = "camera_tilt_max"
KmlTour_CONFKEY_KMLTOUR_TILT_MIN = "camera_tilt_min"

KmlTour_CONFKEY_WAIT = "camera_wait"
KmlTour_CONFKEY_HEADING = "camera_heading"
KmlTour_CONFKEY_FLYTIME = "camera_fly_time"
KmlTour_CONFKEY_TILT = "camera_tilt"
KmlTour_CONFKEY_RANGE = "camera_range"
KmlTour_CONFKEY_FOLLOWPATH = "camera_follow_path"

KmlTour_CONFKEY_END_NAME = "end_name"
KmlTour_CONFKEY_END_DESC = "end_desc_file"
KmlTour_CONFKEY_END_DESC_TEXT = "end_desc"
KmlTour_CONFKEY_END_STYLE = "end_style"
KmlTour_CONFKEY_END_ICON = "end_icon"
KmlTour_CONFKEY_END_SCALE = "end_scale"

KmlTour_CONFKEY_END_HEADING = "camera_end_heading"
KmlTour_CONFKEY_END_FLYTIME = "camera_end_fly_time"
KmlTour_CONFKEY_END_TILT = "camera_end_tilt"
KmlTour_CONFKEY_END_RANGE = "camera_end_range"


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


    def _set_option(self, options, key, value):
        options.setdefault(key, value)


    def process_variables(self, options, *args, **kwargs):
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_NAME, KmlTour_NAME)
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_DESC, KmlTour_DESC)
        folder = options.setdefault(KmlTour_CONFKEY_KMLTOUR_FOLDER, KmlTour_FOLDER)
        if folder == "-":
            options[KmlTour_CONFKEY_KMLTOUR_FOLDER] = None
        self._set_option_bool(options, KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX, KmlTour_MUSIC_MIX)
        self._set_option_bool(options, KmlTour_CONFKEY_KMLTOUR_FIRST_PHOTO, KmlTour_FROM_FIRST_PHOTO)
        self._set_option_bool(options, KmlTour_CONFKEY_KMLTOUR_LAST_PHOTO, KmlTour_TO_LAST_PHOTO)
        self._set_option_bool(options, KmlTour_CONFKEY_KMLTOUR_COPYMUSIC, KmlTour_COPYMUSIC)
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
        options.setdefault(KmlTour_CONFKEY_BEGIN_DESC_TEXT, '')
        options.setdefault(KmlTour_CONFKEY_BEGIN_STYLE, KmlTour_BEGIN_STYLE)
        options.setdefault(KmlTour_CONFKEY_BEGIN_ICON, KmlTour_BEGIN_ICON)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_SCALE, KmlTour_BEGIN_SCALE, (0.0, 10.0))
        self._set_option_float_none(options, KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE, KmlTour_SIMPL_DISTANCE, (0, 1000000))
        if options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE] == None:
            options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE] = -1
        self._set_option_float(options, KmlTour_CONFKEY_KMLTOUR_RANGE_MAX, KmlTour_CRANGE_MAXLIMIT)
        self._set_option_float(options, KmlTour_CONFKEY_KMLTOUR_RANGE_MIN, KmlTour_CRANGE_MINLIMIT)
        self._set_option_float(options, KmlTour_CONFKEY_KMLTOUR_TILT_MAX, KmlTour_TILT_MAXLIMIT)
        self._set_option_float(options, KmlTour_CONFKEY_KMLTOUR_TILT_MIN, KmlTour_TILT_MINLIMIT)
        # begin
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_WAIT, KmlTour_BEGIN_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_HEADING, KmlTour_BEGIN_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_FLYTIME, KmlTour_BEGIN_FLYTIME, (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_TILT, KmlTour_BEGIN_TILT, (0,90))
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_RANGE, KmlTour_BEGIN_RANGE)
        # geophotos
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
        options.setdefault(KmlTour_CONFKEY_END_DESC_TEXT, '')
        options.setdefault(KmlTour_CONFKEY_END_STYLE, KmlTour_END_STYLE)
        options.setdefault(KmlTour_CONFKEY_END_ICON, KmlTour_END_ICON)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_SCALE, KmlTour_END_SCALE, (0.0, 10.0))
        # ends
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
        self.setup_geophotos()
        self.logger.debug(_("Starting add-on ..."))


    @DRegister("MakeKML:ini")
    def process_ini(self, *args, **kwargs):
        if not self.state.kmldata:
            return
        mp3list = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC]
        mp3mix = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX]
        mp3uri = self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_URI]
        try:
            self.gxtour = gxTour(mp3list, mp3mix, mp3uri)
        except Exception as e:
            self.logger.error(_("Cannot set mp3 sound files: %s.") % str(e))
            self.gxtour = gxTour([], False, mp3uri)


    def get_description(self, key, fallback_key, bytes=102400):
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
            else:
                description =  self.options[fallback_key]
        templatedata = TemplateDict(self.defaultsinfo)
        return description % templatedata


    def _border_range(self, angle, lat, lon):
        # using ellipse polar equation
        max_lat = self.center_lat
        min_lat = lat
        if min_lat > max_lat:
            max_lat = lat
            min_lat = self.center_lat
        max_lon = self.center_lon
        min_lon = lon
        if min_lon > max_lon:
            max_lon = lon
            min_lon = self.center_lon
        #b_distance = self.altitude            
        b_distance = pyGPX.bestViewAltitude(max_lat, max_lon, min_lat, min_lon)
        c_distance = pyGPX.distanceCoord(self.center_lat, self.center_lon, lat, lon) / 2.0
        a_distance = math.sqrt(c_distance * c_distance + b_distance * b_distance)
        eccentricity = float(c_distance) / a_distance
        rangle = math.radians(angle)
        r = (a_distance * (1.0 - eccentricity * eccentricity)) / (1.0 + eccentricity * math.cos(rangle))
        return r


    def set_first(self):
        begin_name = self.options[KmlTour_CONFKEY_BEGIN_NAME]
        begin_desc = self.get_description(KmlTour_CONFKEY_BEGIN_DESC, KmlTour_CONFKEY_BEGIN_DESC_TEXT)
        begin_style = self.options[KmlTour_CONFKEY_BEGIN_STYLE]
        begin_flytime = self.options[KmlTour_CONFKEY_BEGIN_FLYTIME]
        begin_wait = self.options[KmlTour_CONFKEY_BEGIN_WAIT]
        strtime = self.first_time.strftime("%Y-%m-%dT%H:%M:%S") + self.state.stzdiff
        begin_heading = self.options[KmlTour_CONFKEY_BEGIN_HEADING]
        if begin_heading == None \
        or begin_heading == PhotoPlace_estimated \
        or begin_heading == PhotoPlace_default:
            begin_heading = pyGPX.bearingCoord(
                self.first_lat, self.first_lon, self.center_lat, self.center_lon)
        begin_tilt = self.options[KmlTour_CONFKEY_BEGIN_TILT]
        if begin_tilt == None:
            begin_tilt = KmlTour_BEGIN_TILT
        elif begin_tilt == PhotoPlace_estimated:
            begin_tilt = KmlTour_BEGIN_TILT
        elif begin_tilt == PhotoPlace_default:
            begin_tilt = KmlTour_BEGIN_TILT
        begin_range = self.options[KmlTour_CONFKEY_BEGIN_RANGE]
        try:
            begin_range = float(begin_range)
        except:
            begin_range = self._border_range(begin_tilt, self.first_lat, self.first_lon)
        if begin_style == None or len(begin_style) < 2:
            begin_icon = self.options[KmlTour_CONFKEY_BEGIN_ICON]
            begin_scale = self.options[KmlTour_CONFKEY_BEGIN_SCALE]
            begin_style = datetime.datetime.now().strftime("tour-start" + "%Y%j%I%M")
            self.gxtour.do_placemark_style(begin_style, begin_icon, begin_scale)
            begin_style = '#' + begin_style
        self.gxtour.begin(self.first_lon, self.first_lat, self.first_ele, strtime, begin_name, 
            begin_desc, begin_style, begin_wait, begin_heading, begin_tilt, begin_range, begin_flytime)


    def set_last(self, last_photo_id):
        end_name = self.options[KmlTour_CONFKEY_END_NAME]
        end_desc = self.get_description(KmlTour_CONFKEY_END_DESC, KmlTour_CONFKEY_END_DESC_TEXT)
        end_style = self.options[KmlTour_CONFKEY_END_STYLE]
        strtime = self.last_time.strftime("%Y-%m-%dT%H:%M:%S") + self.state.stzdiff
        end_flytime = self.options[KmlTour_CONFKEY_END_FLYTIME]
        end_heading = self.options[KmlTour_CONFKEY_END_HEADING]
        if end_heading == None \
        or end_heading == PhotoPlace_estimated \
        or end_heading == PhotoPlace_default:
            end_heading = pyGPX.bearingCoord(
                self.last_lat, self.last_lon, self.center_lat, self.center_lon)
        end_tilt = self.options[KmlTour_CONFKEY_END_TILT]
        if end_tilt == None:
            end_tilt = KmlTour_END_TILT
        elif end_tilt == PhotoPlace_estimated:
            end_tilt = KmlTour_END_TILT
        elif end_tilt == PhotoPlace_default:
            end_tilt = KmlTour_END_TILT
        end_range = self.options[KmlTour_CONFKEY_END_RANGE]
        try:
            end_range = float(end_range)
        except:
            end_range = self._border_range(end_tilt, self.last_lat, self.last_lon)
        self.set_path(last_photo_id, end_flytime, end_tilt, end_range, end_heading)
        if end_style == None or len(end_style) < 2:
            end_icon = self.options[KmlTour_CONFKEY_END_ICON]
            end_scale = self.options[KmlTour_CONFKEY_END_SCALE]
            end_style = datetime.datetime.now().strftime("tour-end" + "%Y%j%I%M")
            self.gxtour.do_placemark_style(end_style, end_icon, end_scale)
            end_style = '#' + end_style
        self.gxtour.end(self.last_lon, self.last_lat, self.last_ele, strtime,
            end_name, end_desc, end_style, end_heading, end_tilt, end_range, end_flytime)


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
        points = list()
        if prev_time != None and time != None:
            points = self.get_track_bytime(prev_time, time)
        else:
            points = self.get_track_bypos(prev_lon, prev_lat, lon, lat)
        result = list()
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


    def setup_geophoto(self, geophoto):
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


    def setup_geophotos(self, mode=True):
        if mode:
            for geophoto in self.state.geophotos:
                self.setup_geophoto(geophoto)
        else:
            for geophoto in self.state.geophotos:
                del geophoto.attr[KmlTour_CONFKEY_WAIT]
                del geophoto.attr[KmlTour_CONFKEY_HEADING]
                del geophoto.attr[KmlTour_CONFKEY_FLYTIME]
                del geophoto.attr[KmlTour_CONFKEY_TILT]
                del geophoto.attr[KmlTour_CONFKEY_RANGE]
                del geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH]


    @DRegister("LoadPhotos:run")
    def load_photo(self, geophoto, *args, **kwargs):
        self.setup_geophoto(geophoto)


    def set_bounds(self, status=1, from_first_photo=False, to_last_photo=False):
        self.max_lat = -90.0
        self.min_lat = 90.0
        self.max_lon = -180.0
        self.min_lon = 180.0
        self.center_lon = 0.0
        self.center_lat = 0.0
        self.geophotos_center_lon = None
        self.geophotos_center_lat = None
        self.geophotos_max_lat = -90.0
        self.geophotos_min_lat = 90.0
        self.geophotos_max_lon = -180.0
        self.geophotos_min_lon = 180.0
        self.geophoto_first = None
        self.geophoto_last = None
        self.first_ele = None
        self.first_time = None
        self.last_ele = None
        self.last_time = None
        ready = 0
        # Photos
        num_photos = 0
        first_geophoto = None
        last_geophoto = None
        for gphoto in self.state.geophotos:
            if gphoto.status >= status and gphoto.isGeoLocated():
                if num_photos == 0:
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
                num_photos += 1
        if num_photos > 0:
            self.center_lon = (self.max_lon + self.min_lon)/2.0
            self.center_lat = (self.max_lat + self.min_lat)/2.0
            self.first_lat = first_geophoto.lat
            self.first_lon = first_geophoto.lon
            self.first_ele = first_geophoto.ele
            self.first_time = first_geophoto.ptime
            if self.first_time == None:
                self.first_time = first_geophoto.time - self.state.tzdiff
            self.last_lat = last_geophoto.lat
            self.last_lon = last_geophoto.lon
            self.last_ele = last_geophoto.ele
            self.last_time = last_geophoto.ptime
            if self.last_time == None:
                self.last_time = last_geophoto.time - self.state.tzdiff
            self.geophotos_center_lon = self.center_lon
            self.geophotos_center_lat = self.center_lat
            self.geophotos_max_lat = self.max_lat
            self.geophotos_min_lat = self.min_lat
            self.geophotos_max_lon = self.max_lon
            self.geophotos_min_lon = self.min_lon
            ready += 1
        # Tracks
        self.tracks_points = list()
        self.tracks_pos = 0
        self.points_pos = 0
        if self.state.gpxdata:
            for track in self.state.gpxdata.tracks:
                if track.status:
                    self.tracks_points.append(track.listpoints())
        if self.tracks_points:
            if not from_first_photo:
                self.first_lat = self.tracks_points[0][0].lat
                self.first_lon = self.tracks_points[0][0].lon
                self.first_ele = self.tracks_points[0][0].ele
                self.first_time = self.tracks_points[0][0].time
            if not to_last_photo:
                self.last_lat = self.tracks_points[-1][-1].lat
                self.last_lon = self.tracks_points[-1][-1].lon
                self.last_ele = self.tracks_points[-1][-1].ele
                self.last_time = self.tracks_points[-1][-1].time
            ready += 1
        return ready


    def estimate_bounds(self, simpl_distance=None, status=1, from_first_photo=False, to_last_photo=False):
        if not self.set_bounds(status, from_first_photo, to_last_photo):
            self.logger.debug(_("No data! Cowardly refusing to create a tour!"))
            return -1
        self.altitude = 0.0
        self.distance = 0.0
        self.distance_avg = 0.0
        self.distance_med = 0.0
        distances = list()
        lat_prev = self.first_lat
        lon_prev = self.first_lon
        ele_prev = self.first_ele
        time_prev = self.first_time
        # Calculate the best values for altitude
        try:
            self.altitude = pyGPX.bestViewAltitude(self.max_lat, self.max_lon, self.min_lat, self.min_lon)
        except:
            self.altitude = self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN] + 50
        if self.altitude < self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN]:
            self.altitude = self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN] + 50
        if self.altitude > self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MAX]:
            self.altitude = self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MAX]
        self.tour_points = dict()
        epsilon = simpl_distance
        if simpl_distance == None:
            epsilon = self.options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE]
        if epsilon == None or epsilon < 0:
            epsilon = self.altitude * KmlTour_TRACK_SIMPLTOLERANCE / 100.0
            if epsilon < 1:
                epsilon = 1
        #print "SIMPL (si > 0):", epsilon
        num_photos = 0
        for gphoto in self.state.geophotos:
            if gphoto.status >= status and gphoto.isGeoLocated():
                follow = self.options[KmlTour_CONFKEY_FOLLOWPATH]
                follow = self.userfacade.get_geophoto_attr_bool(gphoto, self.options, 
                    KmlTour_CONFKEY_FOLLOWPATH, follow, follow)
                points_len = 0
                points = list()
                if follow and time_prev != None and gphoto.ptime != None:
                    points = self.get_track(lon_prev, lat_prev, time_prev, gphoto.lon, gphoto.lat, gphoto.ptime)
                    points_len = len(points)
                    if points_len > 1 and epsilon > 0:
                        points = pyGPX.simplDouglasPeucker(points, epsilon)
                        points_len = len(points)
                total_distance = 0.0
                if points_len < 1:
                    gphoto_tutc = gphoto.time - self.state.tzdiff
                    gpoint = pyGPX.GPXPoint(gphoto.lat, gphoto.lon, gphoto.ele, gphoto_tutc)
                    points.append(gpoint)
                    total_distance = gpoint.distance(lat_prev, lon_prev)
                if points_len > 1:
                    for pos in xrange(1, points_len):
                        prev = points[pos - 1]
                        current = points[pos]
                        total_distance += prev.distance(current)
                self.distance += total_distance
                distances.append(total_distance)
                lat_prev = gphoto.lat
                lon_prev = gphoto.lon
                ele_prev = gphoto.ele
                time_prev = gphoto.ptime
                self.tour_points[num_photos] = (total_distance, gphoto.ptime, gphoto.time, points)
                num_photos += 1
        # Last path
        if not to_last_photo:
            follow = self.options[KmlTour_CONFKEY_FOLLOWPATH]
            points_len = 0
            points = list()
            if follow and time_prev != None and self.last_time != None:
                points = self.get_track(lon_prev, lat_prev, time_prev, self.last_lon, self.last_lat, self.last_time)
                points_len = len(points)
                if points_len > 1 and epsilon > 0:
                    points = pyGPX.simplDouglasPeucker(points, epsilon)
                    points_len = len(points)
            total_distance = 0.0
            if points_len < 1:
                gpoint = pyGPX.GPXPoint(self.last_lat, self.last_lon, self.last_ele, self.last_time)
                points.append(gpoint)
                total_distance = gpoint.distance(lat_prev, lon_prev)
            if points_len > 1:
                for pos in xrange(1, points_len):
                    prev = points[pos - 1]
                    current = points[pos]
                    total_distance += prev.distance(current)
            self.distance += total_distance
            distances.append(total_distance)
            self.tour_points[num_photos] = (total_distance, self.last_time, self.last_time + self.state.tzdiff, points)
        # Some calculations
        if num_photos > 0:
            # Avg
            self.distance_avg = self.distance / num_photos
            distances.sort()
            # Median
            self.distance_med = distances[int(num_photos / 2)]
            if num_photos % 2 == 0 :
                self.distance_med = (self.distance_med + distances[int(num_photos / 2) - 1]) / 2
        return num_photos


    def set_path(self, idpath, fly_time, fly_tilt, fly_crange, fly_bearing):
        (distance, ptime, gtime, points) = self.tour_points[idpath]
        points_len = len(points)
        if ptime != None:
            strtime = ptime.strftime("%Y-%m-%dT%H:%M:%S") + self.state.stzdiff
        else:
            strtime = gtime.strftime("%Y-%m-%dT%H:%M:%S")
        range_offset = self.altitude - self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN]
        range_mid = range_offset / 2.0
        # f(x) = (x/(self.distance / 15))^3 + range_mid + range_offset
        # f(x) = -x + range_mid
        if fly_crange == None:
            x = distance - self.distance_med
            y = -1 * x + range_mid
            camera = y + KmlTour_CRANGE_MINLIMIT
            if camera > self.altitude:
                crange = self.altitude
            elif camera < self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN]:
                crange = self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN]
            else:
                crange = camera
        else:
            crange = fly_crange
        #print "RANGE", crange
        if fly_tilt == None:
            if crange == self.altitude:
                tilt = self.options[KmlTour_CONFKEY_KMLTOUR_TILT_MAX]
            elif crange == self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN]:
                tilt = self.options[KmlTour_CONFKEY_KMLTOUR_TILT_MIN]
            else:
                tilt = (crange - self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN])
                tilt = tilt / (range_offset) * self.options[KmlTour_CONFKEY_KMLTOUR_TILT_MAX]
        else:
            tilt = fly_tilt
        #print "TILT", tilt
        if points_len > 1:
            total_speed = distance / float(fly_time)
            for pos in xrange(0, points_len - 1):
                next = points[pos + 1]
                current = points[pos]
                distance = current.distance(next)
                flytime = distance / total_speed
                heading = fly_bearing
                if fly_bearing == None:
                    heading = current.bearing(next.lat, next.lon)
                if pos == 0:
                    heading_prev = heading
                else: 
                    # heading_prev - heading) >= KmlTour_FOLLOW_ANGLECORNER
                    # using cos difference
                    rad_heading = math.radians(heading)
                    rad_heading_prev = math.radians(heading_prev)
                    cos_diff = math.cos(rad_heading_prev) * math.cos(rad_heading_prev)
                    cos_diff += math.sin(rad_heading) * math.sin(rad_heading)
                    if cos_diff >= self.cos_max_diff_corner:
                        self.gxtour.do_flyto(current.lon, current.lat, current.ele, 
                            strtime, heading, tilt, crange, flytime)
                heading_prev = heading
                self.gxtour.do_flyto(next.lon, next.lat, next.ele, 
                    strtime, heading, tilt, crange, flytime)
        else:
            if idpath == 0:
                prev_lat = self.first_lat
                prev_lon = self.first_lon
            else:
                (prev_distance, prev_ptime, prev_gtime, prev_points) = self.tour_points[idpath - 1]
                prev_lat = prev_points[-1].lat
                prev_lon = prev_points[-1].lon
            lat = points[0].lat
            lon = points[0].lon
            ele = points[0].ele
            heading = fly_bearing
            if fly_bearing == None:
                heading = pyGPX.bearingCoord(prev_lat, prev_lon, lat, lon)
            flytime = fly_time
            self.gxtour.do_flyto(lon, lat, ele, strtime, heading, tilt, crange, flytime)


    @DRegister("MakeKML:end")
    def process_end(self, number_photos, *args, **kwargs):
        name = self.options[KmlTour_CONFKEY_KMLTOUR_NAME]
        description = self.options[KmlTour_CONFKEY_KMLTOUR_DESC]
        folder = self.options[KmlTour_CONFKEY_KMLTOUR_FOLDER]
        from_first_photo = self.options[KmlTour_CONFKEY_KMLTOUR_FIRST_PHOTO]
        to_last_photo = self.options[KmlTour_CONFKEY_KMLTOUR_LAST_PHOTO]
        kml = self.state.kmldata.getKml()
        if not kml:
            self.logger.debug(_("No KML output! Cowardly refusing to create a tour!"))
            return
        num_photos = self.estimate_bounds(None, self.state.status, from_first_photo, to_last_photo)
        if num_photos < 0:
            self.logger.debug(_("No geolocated photos! Cowardly refusing to create a tour!"))
            return
        # KmlTour_FOLLOW_ANGLECORNER with cos(X - Y)
        self.cos_max_diff_corner = math.cos(math.radians(KmlTour_FOLLOW_ANGLECORNER))
        spanbegin = self.first_time.strftime("%Y-%m-%dT%H:%M:%S") + self.state.stzdiff
        spanend = self.last_time.strftime("%Y-%m-%dT%H:%M:%S") + self.state.stzdiff
        self.gxtour.ini(name, description, spanbegin, spanend, kml, folder)
        # firt point for camera
        if not from_first_photo:
            self.set_first()
        num_photos = 0
        for geophoto in self.state.geophotos:
            if geophoto.status < self.state.status or not geophoto.isGeoLocated():
                # not selected
                continue
            wait = self.options[KmlTour_CONFKEY_WAIT]
            wait = self.userfacade.get_geophoto_attr_number(geophoto, self.options, 
                KmlTour_CONFKEY_WAIT, wait, wait)
            #print "WAIT ", wait
            bearing = self.options[KmlTour_CONFKEY_HEADING]
            bearing = self.userfacade.get_geophoto_attr_number(geophoto, self.options, 
                KmlTour_CONFKEY_HEADING, bearing, None)
            #print "Bearing ", bearing
            flytime = self.options[KmlTour_CONFKEY_FLYTIME]
            flytime = self.userfacade.get_geophoto_attr_number(geophoto, self.options, 
                KmlTour_CONFKEY_FLYTIME, flytime, flytime)
            #print "FLYTIME ", flytime
            tilt = self.options[KmlTour_CONFKEY_TILT]
            tilt = self.userfacade.get_geophoto_attr_number(geophoto, self.options, 
                KmlTour_CONFKEY_TILT, tilt, None)
            #print "TILT ", tilt
            crange = self.options[KmlTour_CONFKEY_RANGE]
            crange = self.userfacade.get_geophoto_attr_number(geophoto, self.options,
                KmlTour_CONFKEY_RANGE, crange, None)
            #print "CRANGE ", crange
            self.set_path(num_photos, flytime, tilt, crange, bearing)
            self.gxtour.do_balloon(geophoto.name)
            self.gxtour.do_wait(wait)
            self.gxtour.do_balloon(geophoto.name, False)
            self.gxtour.music()
            num_photos += 1
        # Last path
        if not to_last_photo:
            self.set_last(num_photos)
        

    @DRegister("SaveFiles:ini")
    def save(self, fd, outputkml, outputkmz, photouri, outputdir, quality):
        if not self.options[KmlTour_CONFKEY_KMLTOUR_COPYMUSIC]:
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
            self.traks_points = list()
            self.tracks_pos = 0
            self.points_pos = 0
            self.tour_points = dict()
            self.altitude = 0.0
            self.distance = 0.0
            self.distance_avg = 0.0
            self.distance_med = 0.0
            self.max_lat = -90.0
            self.min_lat = 90.0
            self.max_lon = -180.0
            self.min_lon = 180.0
            self.geophotos_center_lon = None
            self.geophotos_center_lat = None
            self.geophotos_max_lat = -90.0
            self.geophotos_min_lat = 90.0
            self.geophotos_max_lon = -180.0
            self.geophotos_min_lon = 180.0
            self.geophoto_first = None
            self.geophoto_last = None
            self.first_ele = None
            self.first_time = None
            self.last_ele = None
            self.last_time = None
            self.logger.debug(_("Resetting add-on ..."))


    def end(self, options):
        self.ready = 0
        self.setup_geophotos(False)
        self.gxtour = None
        self.options = None
        self.tracks_points = list()
        self.tracks_pos = 0
        self.points_pos = 0
        self.tour_points = dict()
        self.altitude = 0.0
        self.distance = 0.0
        self.distance_avg = 0.0
        self.distance_med = 0.0
        self.center_lon = 0.0
        self.center_lat = 0.0
        self.max_lat = -90.0
        self.min_lat = 90.0
        self.max_lon = -180.0
        self.min_lon = 180.0
        self.geophotos_center_lon = None
        self.geophotos_center_lat = None
        self.geophotos_max_lat = -90.0
        self.geophotos_min_lat = 90.0
        self.geophotos_max_lon = -180.0
        self.geophotos_min_lon = 180.0
        self.geophoto_first = None
        self.geophoto_last = None
        self.first_ele = None
        self.first_time = None
        self.last_ele = None
        self.last_time = None
        if self.gui:
            self.gui.hide()
        self.logger.debug(_("Ending add-on ..."))


# EOF
