#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       paths.py
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
A plugin for PhotoPlace to generate paths from GPX tracks to show them in the KML layer.
"""
__program__ = "photoplace.paths"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.2.0"
__date__ = "December 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import time
import codecs
import datetime
import urlparse
import gettext
import locale


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


import gpx
from userFacade import TemplateDict
from Plugins.Interface import *
from definitions import *


# Simbols exported to templates
PhotoPlace_PathNAME = "PhotoPlace.PathNAME"
PhotoPlace_PathDESC = "PhotoPlace.PathDESC"
PhotoPlace_PathTINI = "PhotoPlace.PathTINI"
PhotoPlace_PathTEND = "PhotoPlace.PathTEND"
PhotoPlace_PathDRTN = "PhotoPlace.PathDRTN"
PhotoPlace_PathLEN = "PhotoPlace.PathLEN"
PhotoPlace_PathLENMIN = "PhotoPlace.PathLENMIN"
PhotoPlace_PathLENMAX = "PhotoPlace.PathLENMAX"
PhotoPlace_PathSPMIN = "PhotoPlace.PathSPMIN"
PhotoPlace_PathSPMAX = "PhotoPlace.PathSPMAX"
PhotoPlace_PathSPAVG = "PhotoPlace.PathSPAVG"
PhotoPlace_PathNSEG = "PhotoPlace.PathNSEG"
PhotoPlace_PathNWPT = "PhotoPlace.PathNWPT"

# Configuration keys
KmlPaths_CONFKEY = "paths"
KmlPaths_CONFKEY_KMLPATH_NAME = "foldername"
KmlPaths_CONFKEY_KMLPATH_GENTRACK = "generatetrack"
KmlPaths_CONFKEY_TRACKS_SEPARATOR = '.'
KmlPaths_CONFKEY_TRACKS_NAME = 'trackname'
KmlPaths_CONFKEY_TRACKS_DESC = 'trackdescription'
KmlPaths_CONFKEY_TRACKS_COLOR = 'trackcolor'
KmlPaths_CONFKEY_TRACKS_WIDTH = 'trackwidth'

# Default values
KmlPaths_KMLPATH_NAME = _("Paths")
KmlPaths_KMLPATH_GENNAME = _("Photo path")
KmlPaths_KMLPATH_GENDESC = _("Generated path from geotagged photos")
KmlPaths_KMLPATH_GENTRACK = True
KmlPaths_TRACKS_COLOR = '20FFFF00'
KmlPaths_TRACKS_WIDTH = '3'
KmlPaths_GPX_GENNAME = _('Pictures')


import KmlPath



class KmlPaths(Plugin):

    description = _(
        "A plugin to generate paths from GPX tracks to "
        "show them in the KML layer."
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


    def __init__(self, logger, state, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, state, args, argfiles, gtkbuilder)
        self.options = dict()
        # GTK widgets
        self.gui = None
        self.tracksinfo = None
        self.track_num = 0
        self.defaultsinfo = None
        self.kmlpath = None
        self.phototrack = None
        self.gengpx = None
        if gtkbuilder:
            import GTKPaths
            self.gui = GTKPaths.GTKPaths(gtkbuilder, state, logger)
        self.ready = -1


    def init(self, options, widget):
        if not options.has_key(KmlPaths_CONFKEY):
            options[KmlPaths_CONFKEY] = dict()
        opt = options[KmlPaths_CONFKEY]
        self.defaultsinfo = options['defaults']
        self.process_variables(opt)
        self.kmlpath = None
        self.gengpx = gpx.GPX(KmlPaths_GPX_GENNAME, datetime.datetime.utcnow())
        self.phototrack = dict()
        if self.gui:
            if self.ready == -1:
                # 1st time
                self.gui.show(widget, self.options, self.tracksinfo)
            else:
                self.gui.show(None, self.options, self.tracksinfo)
        self.ready = 1
        self.logger.debug(_("Starting plugin ..."))


    def process_variables(self, options):
        name = options.setdefault(KmlPaths_CONFKEY_KMLPATH_NAME, KmlPaths_KMLPATH_NAME)
        if name == "-":
            options[KmlPaths_CONFKEY_KMLPATH_NAME] = None
        gentrack = options.setdefault(KmlPaths_CONFKEY_KMLPATH_GENTRACK, KmlPaths_KMLPATH_GENTRACK)
        if not isinstance(gentrack, bool):
            generate = gentrack.lower().strip() in ["yes", "true", "on", "si", "1"]
            options[KmlPaths_CONFKEY_KMLPATH_GENTRACK] = generate
        self.tracksinfo = { 
        0:{
            KmlPaths_CONFKEY_TRACKS_NAME : KmlPaths_KMLPATH_GENNAME,
            KmlPaths_CONFKEY_TRACKS_DESC : '',
            KmlPaths_CONFKEY_TRACKS_COLOR : KmlPaths_TRACKS_COLOR,
            KmlPaths_CONFKEY_TRACKS_WIDTH : KmlPaths_TRACKS_WIDTH,
        },
        1:{
            KmlPaths_CONFKEY_TRACKS_COLOR : KmlPaths_TRACKS_COLOR,
            KmlPaths_CONFKEY_TRACKS_WIDTH : KmlPaths_TRACKS_WIDTH,
        }}
        for key, value in options.iteritems():
            tmp = key.split(KmlPaths_CONFKEY_TRACKS_SEPARATOR)
            if len(tmp) > 1:
                try:
                    number = int(tmp[1])
                    if number < 0:
                        raise UserWarning
                    tkey = tmp[0]
                    if tkey == KmlPaths_CONFKEY_TRACKS_COLOR:
                        tmp_val = int(value[0:2], 16)
                        tmp_val = int(value[6:8], 16)
                        tmp_val = int(value[4:6], 16)
                        tmp_val = int(value[2:4], 16)
                    elif tkey == KmlPaths_CONFKEY_TRACKS_WIDTH:
                        tmp_val = int(value)
                    elif tkey == KmlPaths_CONFKEY_TRACKS_DESC:
                        if not os.path.isfile(value):
                            tmp_val = os.path.join(self.state.resourcedir, value)
                            if not os.path.isfile(tmp_val):
                                raise UserWarning
                            else:
                                value = tmp_val
                except:
                    msg = _("Cannot understand the key '%s' in config file.")
                    self.logger.warning(msg % key)
                    continue
                if not self.tracksinfo.has_key(number):
                    self.tracksinfo[number] = dict()
                self.tracksinfo[number][tkey] = value
        self.options = options


    @DRegister("ReadGPX:finish")
    def update(self, *args, **kwargs):
        if self.gui:
            self.gui.clear_tracks()
            for track in self.state.gpxdata.tracks:
                name = str(track.name)
                desc = str(track.desc)
                self.gui.add_track(name, desc)


    @DRegister("LoadPhotos:finish")
    def loadphotos(self, *args, **kwargs):
        name = os.path.basename(self.state['photoinputdir'])
        self.phototrack[name] = list()
        self.tracksinfo[0][KmlPaths_CONFKEY_TRACKS_NAME] = name
        for photo in self.state.geophotos:
            if photo.isGeoLocated():
                geoinfo = (photo.path, photo.lon, photo.lat, photo.ele, photo.time)
                self.phototrack[name].append(geoinfo)
        if self.gui:
            self.gui.photo_path()


    @DRegister("MakeKML:finish")
    def generate(self, *args, **kwargs):
        if not self.ready \
            or not self.state.gpxdata \
            or not self.state.outputkml:
            self.ready = 0
            return None
        kml = self.state.kmldata.getKml()
        name = self.options[KmlPaths_CONFKEY_KMLPATH_NAME]
        self.kmlpath = KmlPath.KmlPath(name, None, kml)
        num_tracks = 0
        self.logger.debug(_("Processing all tracks (paths) from GPX data ... "))
        if self.options[KmlPaths_CONFKEY_KMLPATH_GENTRACK]:
            self.maketrack()
            num_tracks += self.gentrack(self.gengpx.tracks)
        num_tracks += self.gentrack(self.state.gpxdata.tracks)
        self.logger.info(_("%s paths have been generated for KML data.") % num_tracks)
        self.track_num = 0


    def maketrack(self):
        proc_photos = 0
        dgettext = dict()
        num_tracks = 0
        time_zone = datetime.timedelta(minutes=self.state['utczoneminutes'])
        for name, track in self.phototrack.iteritems():
            gpxtrk = gpx.GPXTrack(name)
            gpxtrkseg = gpx.GPXSegment(name)
            for photo_path, photo_lon, photo_lat, photo_ele, photo_time in track:
                found = None
                for photo in self.state.geophotos:
                    if photo.path == photo_path:
                        found = photo
                        break
                if not found or found.status < 1:
                    continue
                photo_tutc = photo_time - time_zone
                gpxwpt = gpx.GPXPoint(
                    photo_lat, photo_lon, photo_ele, photo_tutc, found.name)
                dgettext['photo'] = found.name
                dgettext['photo_lon'] = photo_lon
                dgettext['photo_lat'] = photo_lat
                dgettext['photo_ele'] = photo_ele
                dgettext['photo_time'] = photo_time
                dgettext['photo_tutc'] = photo_tutc
                self.logger.debug(_("Generated WayPoint from '%(photo)s' at %(photo_time)s "
                    "(UTC=%(photo_tutc)s) with coordinates (lon=%(photo_lon).8f, "
                    "lat=%(photo_lat).8f, ele=%(photo_ele).8f).") % dgettext)
                gpxtrkseg.addPoint(gpxwpt)
                proc_photos += 1
            try:
                gpxtrk.addSegment(gpxtrkseg)
                dgettext['track_name'] = name
                dgettext['track_points'] = proc_photos
                msg = _("Track '%(track_name)s' was generated from "
                    "%(track_points)s geotagged photos.")
                self.logger.info(msg % dgettext)
            except gpx.GPXError:
                # GPXError if len(gpxtrkseg) == 0
                self.logger.warning(_("Cannot generate empty GPX Track!"))
            self.gengpx.tracks.append(gpxtrk)
            num_tracks += 1
        return num_tracks


    def gentrack(self, tracklist):
        num_tracks = 0
        dgettext = dict()
        for track in tracklist:
            pathdata = TemplateDict(track.attr)
            # Options from 'defaults' section of config file
            pathdata.update(self.defaultsinfo)
            pathdata[PhotoPlace_PathNAME] = str(track.name)
            pathdata[PhotoPlace_PathDESC] = str(track.desc)
            dgettext['path'] = track.name
            dgettext['path_desc'] = track.desc
            try:
                (tmin, tmax, duration) = track.timeMinMaxDuration()
                pathdata[PhotoPlace_PathTINI] = "%s" % tmin
                pathdata[PhotoPlace_PathTEND] = "%s" % tmax
                pathdata[PhotoPlace_PathDRTN] = "%s" % duration
                (lmin, lmax, length) = track.lengthMinMaxTotal()
                pathdata[PhotoPlace_PathLEN] = "%.3f" % length
                pathdata[PhotoPlace_PathLENMIN] = "%.3f" % lmin
                pathdata[PhotoPlace_PathLENMAX] = "%.3f" % lmax
                (smin, savg, smax) = track.speedMinAvgMax()
                pathdata[PhotoPlace_PathSPMIN] = "%.3f" % smin
                pathdata[PhotoPlace_PathSPMAX] = "%.3f" % smax
                pathdata[PhotoPlace_PathSPAVG] = "%.3f" % savg
                pathdata[PhotoPlace_PathNSEG] = "%s" % len(track.ltrkseg)
                coordinates = list()
                num_points = 0
                for point in track.listpoints():
                    coor = (point.lon, point.lat, point.ele)
                    coordinates.append(coor)
                    num_points = num_points + 1
                pathdata[PhotoPlace_PathNWPT] = num_points
                # Set data
                self.settrack(pathdata, coordinates)
                # write all data to log
                dgettext['path_npoints'] = num_points
                dgettext['path_nsegments'] = len(track.ltrkseg)
                dgettext['path_len'] = length
                dgettext['path_avgsp'] = savg
                dgettext['path_time'] = duration
                self.logger.debug(_("Path '%(path)s', ('%(path_desc)s'): "
                    "points=%(path_npoints)d, segments=%(path_nsegments)d, "
                    "length=%(path_len)s, avgspeed=%(path_avgsp).3f, "
                    "time='%(path_time)s'") % dgettext)
                num_tracks += 1
            except Exception as e:
                dgettext["error"] = str(e)
                msg = _("Error when track (path) '%(path)s' was being "
                    "processed: %(error)s.") % dgettext
                self.logger.error(msg)
        return num_tracks


    def settrack(self, data, coordinates):
        # Only a photo directory with text mode -> only one photo track
        styleid = KmlPaths_CONFKEY
        length = len(self.tracksinfo)
        times, number = divmod(self.track_num, length - 1)
        trackid = 0
        createstyle = False
        # Calculate module, but 0 is reserved for style of first path
        # and cannot be repeated ...
        if times == 0 and number == 0 and self.track_num == 0:
            # Autogenerated track from photos
            styleid = styleid + '0'
            trackid = 0
            createstyle = True
        elif times == 0:
            styleid = styleid + str(number)
            trackid = number
            createstyle = True
        elif times == 1 and number == 0:
            styleid = styleid + str(length - 1)
            trackid = length - 1
            createstyle = True
        elif number == 0:
            styleid = styleid + str(length -1)
            trackid = length - 1
        else:
            styleid = styleid + str(number)
            trackid = number
        trackinfo = self.tracksinfo[trackid]
        if self.gui:
            name = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_NAME, self.track_num)
            description = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_DESC, self.track_num)
            color = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_COLOR, self.track_num)
            width = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_WIDTH, self.track_num)
        else:
            name = data[PhotoPlace_PathNAME]
            if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_NAME):
                name = trackinfo[KmlPaths_CONFKEY_TRACKS_NAME]
            description = data[PhotoPlace_PathDESC]
            if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_DESC):
                filename = trackinfo[KmlPaths_CONFKEY_TRACKS_DESC]
                if filename != None and os.path.isfile(filename):
                    fd = None
                    try:
                        fd = open(filename, "r")
                        description = fd.read()
                    except Exception as exception:
                        self.logger.error(_("Cannot read file '%s'.") % str(exception))
                    finally:
                        if fd:
                            fd.close()
            color = KmlPaths_TRACKS_COLOR
            if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_COLOR):
                color = trackinfo[KmlPaths_CONFKEY_TRACKS_COLOR]
            width = KmlPaths_TRACKS_WIDTH
            if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_WIDTH):
                width = trackinfo[KmlPaths_CONFKEY_TRACKS_WIDTH]
        description = description % data
        if createstyle:
            self.kmlpath.new_style(styleid, color, width)
        styleid = '#' + styleid
        self.kmlpath.new_track(coordinates, name, description, styleid)
        self.track_num += 1


    def reset(self):
        if self.ready:
            self.kmlpath = None
            self.gengpx = gpx.GPX(KmlPaths_GPX_GENNAME, datetime.datetime.utcnow())
            self.phototrack = dict()
            self.track_num = 0
            if self.gui:
                self.gui.clear_tracks()
                self.gui.reset()
            self.logger.debug(_("Resetting plugin ..."))

   
    def end(self, options):
        self.ready = 0
        self.tracksinfo = None
        self.track_num = 0
        self.defaultsinfo = None
        self.options = None
        self.phototrack = None
        self.gengpx = None
        self.kmlpath = None
        if self.gui:
            self.gui.hide()
        self.logger.debug(_("Ending plugin ..."))


# EOF

