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
__version__ = "0.3.3"
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

import pyGPX
from PhotoPlace.userFacade import TemplateDict
from PhotoPlace.Plugins.Interface import *
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
KmlPaths_KMLPATH_GENTRACK = False
KmlPaths_TRACKS_COLOR = '20FFFF00'
KmlPaths_TRACKS_WIDTH = '3'
KmlPaths_GPX_GENNAME = _('Photos')
KmlPaths_VARIABLES = 'defaults'



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
        # GTK widgets
        self.gui = None
        self.tracksinfo = None
        self.defaultsinfo = None
        self.kmlpath = None
        self.gengpx = None
        self.options = None
        self.track_num = 0
        self.photodirlist = None
        if gtkbuilder:
            import GTKPaths
            self.gui = GTKPaths.GTKPaths(gtkbuilder, state, logger)
        self.ready = -1


    def init(self, options, widget):
        if not options.has_key(KmlPaths_CONFKEY):
            options[KmlPaths_CONFKEY] = dict()
        opt = options[KmlPaths_CONFKEY]
        self.defaultsinfo = options[KmlPaths_VARIABLES]
        self.options = None
        self.photodirlist = []
        self.process_variables(opt)
        if self.gui:
            if self.ready == -1:
                # 1st time
                self.gui.show(widget, self.options, self.tracksinfo, options, self.photodirlist)
            else:
                self.gui.show(None, self.options, self.tracksinfo, options, self.photodirlist)
        self.ready = 1
        self.logger.debug(_("Starting plugin ..."))


    def process_variables(self, options):
        name = options.setdefault(KmlPaths_CONFKEY_KMLPATH_NAME, KmlPaths_KMLPATH_NAME)
        if name == "-":
            options[KmlPaths_CONFKEY_KMLPATH_NAME] = None
        gentrack = options.setdefault(KmlPaths_CONFKEY_KMLPATH_GENTRACK, KmlPaths_KMLPATH_GENTRACK)
        if not isinstance(gentrack, bool):
            generate = gentrack.strip().lower() in ["yes", "true", "on", "si", "1"]
            options[KmlPaths_CONFKEY_KMLPATH_GENTRACK] = generate
        self.tracksinfo = {
        0:{
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
                        value = os.path.normpath(value)
                        try:
                            value = unicode(value, 'UTF-8')
                        except:
                            pass
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


    @DRegister("ReadGPX:end")
    def update(self, *args, **kwargs):
        if self.gui:
            self.gui.clear_tracks()
            dgettext = dict()
            num_tracks = 0
            for track in self.state.gpxdata.tracks:
                num_tracks += 1
                dgettext['path_name'] = track.name
                dgettext['path_desc'] = track.desc
                dgettext['path_number'] = num_tracks
                tip = _("Track #%(path_number)s, original name: %(path_name)s\n%(path_desc)s\n")
                try:
                    (tmin, tmax, duration) = track.timeMinMaxDuration()
                    (lmin, lmax, length) = track.lengthMinMaxTotal()
                    dgettext['path_npoints'] = len(track.listpoints())
                    dgettext['path_len'] = length
                    dgettext['path_time'] = duration
                    dgettext['path_end'] = tmax
                    dgettext['path_begin'] = tmin
                    tip = tip + _("Points: %(path_npoints)s, length: %(path_len).3f m.\n")
                    tip = tip + _("Duration: %(path_time)s\n")
                    tip = tip + _("Begin time: %(path_begin)s\n")
                    tip = tip + _("Final time: %(path_end)s\n")
                except Exception as e:
                    dgettext["error"] = str(e)
                    msg = _("Error processing track #%(path_number)s '%(path_name)s': %(error)s.")
                    self.logger.error(msg % dgettext)
                tip = tip % dgettext
                self.gui.add_track(track.name, track.desc, tip)


    @DRegister("LoadPhotos:end")
    def loadphotos(self, num_photos):
        if num_photos > 0:
            name = os.path.basename(self.state['photoinputdir'])
            self.photodirlist.insert(0, (name, True))
            if self.gui:
                dgettext = dict()
                dgettext['path_name'] = name
                dgettext['path_desc'] = KmlPaths_KMLPATH_GENDESC
                dgettext['path_npoints'] = num_photos
                tip = _("Track '%(path_name)s'\n%(path_desc)s\nNumber of photos: %(path_npoints)s")
                tip = tip % dgettext
                self.gui.photo_path(newtrackname=name, tooltip=tip)


    @DRegister("MakeKML:finish")
    def generate(self, *args, **kwargs):
        if not self.ready \
            or not self.state.gpxdata \
            or not self.state.outputkml:
            self.ready = 0
            return None
        self.track_num = 0
        kml = self.state.kmldata.getKml()
        self.gengpx = pyGPX.GPX(KmlPaths_GPX_GENNAME, datetime.datetime.utcnow())
        name = self.options[KmlPaths_CONFKEY_KMLPATH_NAME]
        self.kmlpath = KmlPath.KmlPath(name, None, kml)
        num_tracks = 0
        self.logger.debug(_("Processing all tracks (paths) from GPX data ... "))
        if self.options[KmlPaths_CONFKEY_KMLPATH_GENTRACK]:
            self.maketrack(self.state.geophotos)
            num_tracks += self.gentrack(self.gengpx.tracks)
        num_tracks += self.gentrack(self.state.gpxdata.tracks)
        self.logger.info(_("%s paths have been generated for KML data.") % num_tracks)
        self.track_num = 0
        self.gengpx = None
        self.kmlpath = None


    def maketrack(self, geophotos):
        dgettext = dict()
        time_zone = datetime.timedelta(minutes=self.state['utczoneminutes'])
        tracks = dict()
        for photo in geophotos:
            foto_path = os.path.dirname(photo.path)
            foto_path = os.path.split(foto_path)[1]
            if not tracks.has_key(foto_path):
                gpxtrkseg = pyGPX.GPXSegment(foto_path)
                tracks[foto_path] = gpxtrkseg
            else:
                gpxtrkseg = tracks[foto_path]
            if photo.isGeoLocated():
                dgettext['photo'] = photo.name
                dgettext['photo_lon'] = photo.lon
                dgettext['photo_lat'] = photo.lat
                dgettext['photo_ele'] = photo.ele
                dgettext['photo_time'] = photo.time
                photo_tutc = photo.time - time_zone
                dgettext['photo_tutc'] = photo_tutc
                gpxwpt = pyGPX.GPXPoint(
                    photo.lat, photo.lon, photo.ele, photo_tutc, photo.name)
                self.logger.debug(_("Generated WayPoint from '%(photo)s' at %(photo_time)s "
                    "(UTC=%(photo_tutc)s) with coordinates (lon=%(photo_lon).8f, "
                    "lat=%(photo_lat).8f, ele=%(photo_ele).8f).") % dgettext)
                gpxtrkseg.addPoint(gpxwpt)
        proc_photos = 0
        for name, gpxtrkseg in tracks.iteritems():
            dgettext['track_name'] = name
            active = True
            # See if that track is disabled by the user
            for phototrackname, phototrackactive in self.photodirlist:
                if phototrackname == name:
                    active = phototrackactive
                    break
            gpxtrk = pyGPX.GPXTrack(name)
            gpxtrk.status = active
            self.gengpx.tracks.append(gpxtrk)
            try:
                gpxtrk.addSegment(gpxtrkseg)
                num_photos = len(gpxtrkseg.lwpts)
                proc_photos += num_photos
                dgettext['track_numphotos'] = num_photos
                msg = _("Track '%(track_name)s' was generated from %(track_numphotos)s geotagged photos.")
                self.logger.info(msg % dgettext)
            except pyGPX.GPXError:
                # GPXError if len(gpxtrkseg) == 0
                msg = _("Photo track '%(track_name)s' is empty due to no geotagged photos!")
                self.logger.warning(msg % dgettext)
                gpxtrk.status = False
        return proc_photos


    def gentrack(self, tracklist):
        num_tracks = 0
        dgettext = dict()
        for track in tracklist:
            if not track.status:
                self.track_num += 1
                continue
            pathdata = TemplateDict(track.attr)
            # Options from 'defaults' section of config file
            pathdata.update(self.defaultsinfo)
            pathdata[PhotoPlace_PathNAME] = track.name
            pathdata[PhotoPlace_PathDESC] = track.desc
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
                self.settrack(pathdata, coordinates, self.track_num)
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
                msg = _("Error while processing track '%(path_name)s': %(error)s.")
                self.logger.error(msg % dgettext)
            self.track_num += 1
        return num_tracks


    def settrack(self, data, coordinates, index):
        # Only a photo directory with text mode -> only one photo track
        styleid = KmlPaths_CONFKEY
        length = len(self.tracksinfo)
        times, number = divmod(index, length - 1)
        trackid = 0
        createstyle = False
        # Calculate module, but 0 is reserved for style of first path
        # and cannot be repeated ...
        if times == 0 and number == 0 and index == 0:
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
            name = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_NAME, index)
            description = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_DESC, index)
            color = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_COLOR, index)
            width = self.gui.get_data(KmlPaths_CONFKEY_TRACKS_WIDTH, index)
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
                        fd = codecs.open(filename, "r", encoding="utf-8")
                        description = fd.read()
                    except Exception as e:
                        self.logger.error(_("Cannot read file '%s'.") % str(e))
                    finally:
                        if fd != None:
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


    def reset(self):
        if self.ready:
            self.gengpx = None
            self.kmlpath = None
            self.photodirlist = []
            if self.gui:
                self.gui.clear_tracks()
                self.gui.reset()
            self.logger.debug(_("Resetting plugin ..."))


    def end(self, options):
        self.ready = 0
        self.tracksinfo = None
        self.defaultsinfo = None
        self.options = None
        self.gengpx = None
        self.kmlpath = None
        self.photodirlist = None
        if self.gui:
            self.gui.hide(True)
        self.logger.debug(_("Ending plugin ..."))


# EOF
