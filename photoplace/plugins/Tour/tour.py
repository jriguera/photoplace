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
__version__ = "0.2.0"
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

import pyGPX
from PhotoPlace.Plugins.Interface import *
from PhotoPlace.userFacade import TemplateDict
from PhotoPlace.definitions import *


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
KmlTour_BEGIN_DESC = ''
KmlTour_BEGIN_STYLE =  '#tour-first'
KmlTour_END_NAME = _("End")
KmlTour_END_DESC = ''
KmlTour_END_STYLE = '#tour-last'
KmlTour_FLYMODE = "smooth"
KmlTour_ALTMODE = "absolute"
KmlTour_POINT_DISTANCE_LIMIT = 10
KmlTour_FLYTIME_LIMIT = 0.001
KmlTour_CRANGE_LIMIT = 10

KmlTour_BEGIN_WAIT = 10.0
KmlTour_BEGIN_HEADING = None
KmlTour_BEGIN_FLYTIME = 8.0
KmlTour_BEGIN_TILT = 50.0
KmlTour_BEGIN_RANGE = 1000.0
KmlTour_TILT = 30.0
KmlTour_WAIT = 7.0
KmlTour_FLYTIME = 4.0
KmlTour_HEADING = None
KmlTour_RANGE = 200.0
KmlTour_FOLLOWPATH = True
KmlTour_END_FLYTIME = 5.0
KmlTour_END_HEADING = None
KmlTour_END_TILT = 50.0
KmlTour_END_RANGE = 500.0
KmlTour_END_FOLLOWPATH = True

# Configuration keys
KmlTour_CONFKEY = "tour"
KmlTour_CONFKEY_KMLTOUR_POINT_DISTANCE_LIMIT = "wptdistanceomit"
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
KmlTour_CONFKEY_FOLLOWPATH = "followpath"
KmlTour_CONFKEY_END_NAME = "endname"
KmlTour_CONFKEY_END_DESC = "enddescfile"
KmlTour_CONFKEY_END_STYLE = "endstyle"
KmlTour_CONFKEY_END_HEADING = "endheading"
KmlTour_CONFKEY_END_FLYTIME = "endflytime"
KmlTour_CONFKEY_END_TILT = "endtilt"
KmlTour_CONFKEY_END_RANGE = "endrange"
KmlTour_CONFKEY_END_FOLLOWPATH = "endfollowpath"


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
        self.options = None
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
        mix = options.setdefault(KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX,
            KmlTour_KMLTOUR_MUSIC_MIX)
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
        self._set_option_float(options, KmlTour_CONFKEY_KMLTOUR_POINT_DISTANCE_LIMIT,
            KmlTour_POINT_DISTANCE_LIMIT, (0, 100000))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_WAIT, KmlTour_BEGIN_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_HEADING,
            KmlTour_BEGIN_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_FLYTIME, KmlTour_BEGIN_FLYTIME,
            (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_TILT,
            KmlTour_BEGIN_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_RANGE, KmlTour_BEGIN_RANGE)
        self._set_option_float(options, KmlTour_CONFKEY_WAIT, KmlTour_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_HEADING, KmlTour_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_FLYTIME, KmlTour_FLYTIME,
            (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_TILT, KmlTour_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_RANGE, KmlTour_RANGE)
        self._set_option_bool(options, KmlTour_CONFKEY_FOLLOWPATH, KmlTour_FOLLOWPATH)
        options.setdefault(KmlTour_CONFKEY_END_NAME, KmlTour_END_NAME)
        filename = options.setdefault(KmlTour_CONFKEY_END_DESC)
        if filename != None:
            options[KmlTour_CONFKEY_END_DESC] = os.path.expandvars(os.path.expanduser(filename))
        options.setdefault(KmlTour_CONFKEY_END_STYLE, KmlTour_END_STYLE)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_HEADING,
            KmlTour_END_HEADING, (0,360))
        self._set_option_float(options, KmlTour_CONFKEY_END_FLYTIME, KmlTour_END_FLYTIME,
            (KmlTour_FLYTIME_LIMIT, None))
        self._set_option_float_none(options, KmlTour_CONFKEY_END_TILT, KmlTour_END_TILT, (0,180))
        self._set_option_float(options, KmlTour_CONFKEY_END_RANGE, KmlTour_END_RANGE)
        self._set_option_bool(options, KmlTour_CONFKEY_END_FOLLOWPATH, KmlTour_END_FOLLOWPATH)
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


    def set_first(self, str_tzdiff='', time_zone=datetime.timedelta()):
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
                if max_lat < gphoto.lat:
                    max_lat = gphoto.lat
                if min_lat > gphoto.lat:
                    min_lat = gphoto.lat
                if max_lon < gphoto.lon:
                    max_lon = gphoto.lon
                if min_lon > gphoto.lon:
                    min_lon = gphoto.lon
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
        
        found = False
        tracks_pos = 0
        print "tracks-pos", self.tracks_pos
        print geophoto.lat
        print geophoto.lon
        while tracks_pos < len(self.tracks_points):
            path = self.tracks_points[tracks_pos]
            print ">>>>", path
            for point in path:
                if self.first_lat == point.lat and self.first_lon == point.lon:
                    self.first_lat = path[0].lat
                    self.first_lon = path[0].lon
                    self.first_ele = path[0].ele
                    time = path[0].time + time_zone
                    found = True
                    break
            if found:
                # we have the first point
                self.tracks_pos = tracks_pos
                print "Encuentro primera latlon", self.first_lat, self.first_lon
                break
            tracks_pos += 1
            
        begin_name = self.options[KmlTour_CONFKEY_BEGIN_NAME]
        begin_style = self.options[KmlTour_CONFKEY_BEGIN_STYLE]
        begin_wait = self.options[KmlTour_CONFKEY_BEGIN_WAIT]
        begin_heading = self.options[KmlTour_CONFKEY_BEGIN_HEADING]
        begin_flytime = self.options[KmlTour_CONFKEY_BEGIN_FLYTIME]
        begin_tilt = self.options[KmlTour_CONFKEY_BEGIN_TILT]
        begin_range = self.options[KmlTour_CONFKEY_BEGIN_RANGE]
        begin_desc = self.get_description(KmlTour_CONFKEY_BEGIN_DESC)
        strtime = time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        if begin_heading == None:
            begin_heading = pyGPX.bearingCoord(
                self.first_lat, self.first_lon,
                self.center_lat, self.center_lon)
        if begin_range <= KmlTour_CRANGE_LIMIT:
            distance = pyGPX.distanceCoord(
                self.center_lat, self.center_lon,
                self.first_lat, self.first_lon)
            distance = distance * begin_range
        else:
            distance = begin_range
        self.gxtour.begin(self.first_lon, self.first_lat, self.first_ele, strtime,
            begin_name, begin_desc, begin_style, begin_wait, begin_heading,
            begin_tilt, distance, begin_flytime)
        return geophoto


    def set_last(self, str_tzdiff='', time_zone=datetime.timedelta()):
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
        found = False
        prev_last = False
        for path in self.tracks_points:
            path_len = len(path)
            for point in path:
                if self.last_lat == point.lat and self.last_lon == point.lon:
                    self.last_lat = path[path_len -1].lat
                    self.last_lon = path[path_len -1].lon
                    self.last_ele = path[path_len -1].ele
                    time = path[path_len -1].time + time_zone
                    if path_len > 1:
                        prev_last_lat = path[path_len -2].lat
                        prev_last_lon = path[path_len -2].lat
                        prev_last_ele = path[path_len -2].lat
                        prev_last_time = path[path_len -2].time + time_zone
                        # prev_last != last
                        if prev_last_lat != self.last_lat and prev_last_lon != self.last_lon:
                            prev_last = True
                    found = True
                    break
            if found:
                # we have the first point
                break
        end_name = self.options[KmlTour_CONFKEY_END_NAME]
        end_style = self.options[KmlTour_CONFKEY_END_STYLE]
        end_heading = self.options[KmlTour_CONFKEY_END_HEADING]
        end_flytime = self.options[KmlTour_CONFKEY_END_FLYTIME]
        end_tilt = self.options[KmlTour_CONFKEY_END_TILT]
        end_range = self.options[KmlTour_CONFKEY_END_RANGE]
        end_desc = self.get_description(KmlTour_CONFKEY_END_DESC)
        strtime = time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
        if end_heading == None:
            end_heading = pyGPX.bearingCoord( self.last_lat, self.last_lon,
                self.center_lat, self.center_lon)
        distance = end_range
        if end_range <= KmlTour_CRANGE_LIMIT:
            distance = pyGPX.distanceCoord(self.center_lat, self.center_lon,
                self.last_lat, self.last_lon)
            distance = distance * end_range
        if prev_last:
            follow = self.get_description(KmlTour_CONFKEY_END_FOLLOWPATH)
            prev_strtime = prev_last_time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
            self.set_path(geophoto.lon, geophoto.lat, geophoto.ele,
                prev_last_lon, prev_last_lat, prev_last_ele,
                prev_strtime, end_flytime, end_tilt, distance, end_heading, follow)
        self.gxtour.end(self.last_lon, self.last_lat, self.last_ele, strtime,
            end_name, end_desc, end_style, end_heading, end_tilt, distance, end_flytime)
        return geophoto


    def follow_track(self, prev_lon, prev_lat, lon, lat):
        found_first = False
        found_last = False
        list_points = []
        while self.tracks_pos < len(self.tracks_points):
            path = self.tracks_points[self.tracks_pos]
            path_len = len(path)
            while self.points_pos < path_len:
                point = path[self.points_pos]
                if found_first:
                    list_points.append(point)
                    if point.lat == lat and point.lon == lon:
                        found_last = True
                        break
                else:
                    if point.lat == prev_lat and point.lon == prev_lon:
                        found_first = True
                        list_points.append(point)
                    elif point.lat == lat and point.lon == lon:
                        list_points = list_points + path[:self.points_pos + 1]
                        found_last = True
                        break
                self.points_pos += 1
            if self.points_pos == path_len:
                self.points_pos = 0
            if found_last:
                break
            self.tracks_pos += 1
        # removes repeated points
        new_list_points = []
        len_list_points = len(list_points)
        if len_list_points > 1:
            position = 1
            new_list_points = [list_points[0]]
            while position < len_list_points:
                current = list_points[position]
                previous = list_points[position - 1]
                if current.lat != previous.lat or current.lon != previous.lon:
                    new_list_points.append(current)
                position += 1
        else:
            new_list_points = list_points
        return new_list_points


    def set_path(self, prev_lon, prev_lat, prev_ele, lon, lat, ele, strtime,
        fly_time, fly_tilt, fly_crange, fly_bearing, follow_path=True):

        list_points = []
        total_distance = pyGPX.distanceCoord(prev_lat, prev_lon, lat, lon)
        print "FROM %s %s -> %s %s" % (prev_lat, prev_lon, lat, lon)
        if total_distance < self.options[KmlTour_CONFKEY_KMLTOUR_POINT_DISTANCE_LIMIT]:
            heading = fly_bearing
            if not fly_bearing:
                heading = pyGPX.bearingCoord(prev_lat, prev_lon, lat, lon)
            crange = fly_crange
            if fly_crange <= KmlTour_CRANGE_LIMIT:
                crange = total_distance * fly_crange
            tilt = fly_tilt
            flytime = fly_time
            print "Simplificando: %d" % total_distance
            self.gxtour.do_flyto(lon, lat, ele, strtime, heading, tilt, crange, flytime)
            return
        if follow_path:
            list_points = self.follow_track(prev_lon, prev_lat, lon, lat)
        points_len = len(list_points)
        print "%d -> LISTA de puntos: %s" % (total_distance, list_points)
        if points_len > 1:
            total_speed = total_distance / float(fly_time)
            position_counter = 1
            while position_counter < points_len:
                prev = list_points[position_counter - 1]
                current = list_points[position_counter]
                distance = prev.distance(current)
                flytime = distance / total_speed
                heading = fly_bearing
                if not fly_bearing:
                    heading = pyGPX.bearingCoord(prev.lat, prev.lon, current.lat, current.lon)
                crange = fly_crange
                if fly_crange <= KmlTour_CRANGE_LIMIT:
                    crange = distance * fly_crange
                tilt = fly_tilt
                self.gxtour.do_flyto(current.lon, current.lat, current.ele, strtime, heading, tilt, crange, flytime)
                print "VOLANDO -> ",current.lon, current.lat, current.ele
                position_counter += 1
            return
        heading = fly_bearing
        if fly_bearing == None:
            heading = pyGPX.bearingCoord(prev_lat, prev_lon, lat, lon)
        crange = fly_crange
        if fly_crange <= KmlTour_CRANGE_LIMIT:
            crange = total_distance * fly_crange
        tilt = fly_tilt
        flytime = fly_time
        self.gxtour.do_flyto(lon, lat, ele, strtime, heading, tilt, crange, flytime)
        return


    @DRegister("LoadPhotos:run")
    def load_photo(self, geophoto, *args, **kwargs):
        geophoto.attr[KmlTour_CONFKEY_WAIT] = self.options[KmlTour_CONFKEY_WAIT]
        geophoto.attr[KmlTour_CONFKEY_HEADING] = self.options[KmlTour_CONFKEY_HEADING]
        geophoto.attr[KmlTour_CONFKEY_FLYTIME] = self.options[KmlTour_CONFKEY_FLYTIME]
        geophoto.attr[KmlTour_CONFKEY_TILT] = self.options[KmlTour_CONFKEY_TILT]
        geophoto.attr[KmlTour_CONFKEY_RANGE] = self.options[KmlTour_CONFKEY_RANGE]
        geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH] = 0
        if self.options[KmlTour_CONFKEY_FOLLOWPATH]:
            geophoto.attr[KmlTour_CONFKEY_FOLLOWPATH] = 1


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
                self.tracks_points.append(track.listpoints())
        # firt point for camera
        geophoto = self.set_first(str_tzdiff, time_zone)
        if not geophoto:
            self.ready = 0
            self.logger.debug(_("No photos! Cowardly refusing to create a tour!"))
            return
        previous = (self.first_lat, self.first_lon, 0.0)
        for geophoto in self.state.geophotos:
            if geophoto.status < 1 or not geophoto.isGeoLocated():
                # not selected
                continue
            lat = geophoto.lat
            lon = geophoto.lon
            ele = geophoto.ele
            name = geophoto.name
            wait = float(geophoto.attr.setdefault(KmlTour_CONFKEY_WAIT,
                self.options[KmlTour_CONFKEY_WAIT]))
            bearing = geophoto.attr.setdefault(KmlTour_CONFKEY_HEADING,
                self.options[KmlTour_CONFKEY_HEADING])
            flytime = float(geophoto.attr.setdefault(KmlTour_CONFKEY_FLYTIME,
                self.options[KmlTour_CONFKEY_FLYTIME]))
            tilt = float(geophoto.attr.setdefault(KmlTour_CONFKEY_TILT,
                self.options[KmlTour_CONFKEY_TILT]))
            crange = float(geophoto.attr.setdefault(KmlTour_CONFKEY_RANGE,
                self.options[KmlTour_CONFKEY_RANGE]))
            follow = bool(geophoto.attr.setdefault(KmlTour_CONFKEY_FOLLOWPATH,
                self.options[KmlTour_CONFKEY_FOLLOWPATH]))
            strtime = geophoto.time.strftime("%Y-%m-%dT%H:%M:%S") + str_tzdiff
            self.set_path(previous[1], previous[0], previous[2], lon, lat, ele, strtime,
                flytime, tilt, crange, bearing, follow)
            self.gxtour.do_balloon(name)
            self.gxtour.do_wait(wait)
            self.gxtour.do_balloon(name, False)
            self.gxtour.music()
            previous = (lat, lon, ele)
        # last point
        self.set_last(str_tzdiff, time_zone)


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
            self.logger.debug(_("Resetting plugin ..."))


    def end(self, options):
        self.ready = 0
        self.gxtour = None
        self.options = None
        self.tracks_points = []
        self.tracks_pos = 0
        self.points_pos = 0
        if self.gui:
            self.gui.hide()
        self.logger.debug(_("Ending plugin ..."))


# EOF
