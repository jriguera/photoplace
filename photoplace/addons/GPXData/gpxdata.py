#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       gpxdata.py
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
Add-on for PhotoPlace to generate paths and waypoints from GPX tracks to show them in the KML layer.
"""
__program__ = "photoplace.gpxdata"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.2.2"
__date__ = "August 2012"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera Lopez"


import os.path
import sys
import time
import codecs
import datetime
import urlparse
import gettext
import locale

import pyGPX
from PhotoPlace.Facade import TemplateDict
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

PhotoPlace_WptNAME = "PhotoPlace.WptNAME"
PhotoPlace_WptDESC = "PhotoPlace.WptDESC"
PhotoPlace_WptLAT = "PhotoPlace.WptLAT"
PhotoPlace_WptLON = "PhotoPlace.WptLON"
PhotoPlace_WptELE = "PhotoPlace.WptELE"
PhotoPlace_WptTIME  = "PhotoPlace.WptTIME"

# Configuration keys
GPXData_CONFKEY = "gpxdata"
GPXData_CONFKEY_NAME = "foldername"
GPXData_CONFKEY_GENTRACK = "generatetrack"
GPXData_CONFKEY_GENPATH = "generatepath"
GPXData_CONFKEY_GENPOINTS = "generatewpoints"
GPXData_CONFKEY_WPT_DESC = "wpointdesctemplate"
GPXData_CONFKEY_WPT_FTEMPLATE = "wpointtemplate"
GPXData_CONFKEY_WPT_ICON = "wpointicon"
GPXData_CONFKEY_WPT_ICONSCALE = "wpointscale"
GPXData_CONFKEY_TRACKS_SEPARATOR = '.'
GPXData_CONFKEY_TRACKS_NAME = 'trackname'
GPXData_CONFKEY_TRACKS_FTEMPLATE = 'tracktemplate'
GPXData_CONFKEY_TRACKS_DESC = 'trackdesctemplate'
GPXData_CONFKEY_TRACKS_COLOR = 'trackcolor'
GPXData_CONFKEY_TRACKS_WIDTH = 'trackwidth'

GPXData_VARIABLES = 'defaults'

# Default values
GPXData_NAME = _("Paths")
GPXData_GPX_GENNAME = _('Photos')
GPXData_GENPATH_NAME = _("Geotagged Photo's path")
GPXData_GENPATH_DESC = "%(PhotoPlace.PathDESC|)s"
GPXData_GENPATH = True
GPXData_GENTRACK = True
GPXData_GENPOINTS = True
GPXData_GENCOLOR = '64FFFF00'
GPXData_GENWIDTH = '2'

GPXData_WPT_ICON = u'http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
GPXData_WPT_ICONSCALE = 0.5
GPXData_WPT_FTEMPLATE = "WptDescription.xhtml"
GPXData_WPT_DESC = None

GPXData_TRACKS_COLOR = '7F0000FF'
GPXData_TRACKS_WIDTH = '3'
GPXData_TRACKS_FTEMPLATE = "PathDescription.xhtml"
GPXData_TRACKS_DESC = None



import KMLGpxdata



class GPXData(Plugin):

    description = _(
        "Add-on to generate paths and waypoints from GPX tracks in order to "
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


    def __init__(self, logger, userfacade, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, userfacade, args, argfiles, gtkbuilder)
        # GTK widgets
        self.gui = None
        self.tracksinfo = None
        self.wptsinfo = None
        self.defaultsinfo = None
        self.options = None
        self.track_id = 0
        self.photodirlist = None
        self.photoliststyles = None
        self.wptlist = None
        self.wptstyles = None
        self.tracklist = None
        self.trackstyles = None
        if gtkbuilder:
            import GTKGpxdata
            self.gui = GTKGpxdata.GTKGPXData(gtkbuilder, userfacade, logger)
        self.ready = -1


    def init(self, options, widget):
        if not options.has_key(GPXData_CONFKEY):
            options[GPXData_CONFKEY] = dict()
        opt = options[GPXData_CONFKEY]
        self.defaultsinfo = options[GPXData_VARIABLES]
        self.options = None
        self.process_variables(opt)
        if self.gui:
            if self.ready == -1:
                # 1st time
                self.gui.show(widget, self.options, self.tracksinfo, self.wptsinfo, options)
            else:
                self.gui.show(None, self.options, self.tracksinfo, self.wptsinfo, options)
        self.ready = 1
        self.logger.debug(_("Starting Add-on ..."))


    def _set_bool(self, options, key, default):
        value = options.setdefault(key, default)
        if not isinstance(value, bool):
            options[key] = value.strip().lower() in ["yes", "true", "on", "si", "1", "y"]


    def process_variables(self, options):
        dgettext = dict()
        name = options.setdefault(GPXData_CONFKEY_NAME, GPXData_NAME)
        if name == "-":
            options[GPXData_CONFKEY_NAME] = None
        self._set_bool(options, GPXData_CONFKEY_GENPATH, GPXData_GENPATH)
        self._set_bool(options, GPXData_CONFKEY_GENTRACK, GPXData_GENTRACK)
        self._set_bool(options, GPXData_CONFKEY_GENPOINTS, GPXData_GENPOINTS)
        if options.has_key(GPXData_CONFKEY_WPT_FTEMPLATE):
            filename = self.state.get_template(options[GPXData_CONFKEY_WPT_FTEMPLATE])
            if filename == None:
                dgettext['template'] = options[GPXData_CONFKEY_WPT_FTEMPLATE]
                dgettext['key'] = GPXData_CONFKEY_WPT_FTEMPLATE
                msg = _("Value of '%(key)s' incorrect: Cannot find template file '%(template)s'.")
                self.logger.warning(msg % dgettext)
                options[GPXData_CONFKEY_WPT_FTEMPLATE] = self.state.get_template(GPXData_WPT_FTEMPLATE)
            else:
                options[GPXData_CONFKEY_WPT_FTEMPLATE] = filename
        else:
            options[GPXData_CONFKEY_WPT_FTEMPLATE] = self.state.get_template(GPXData_WPT_FTEMPLATE)
        if options.has_key(GPXData_CONFKEY_WPT_ICONSCALE):
            try:
                value = options[GPXData_CONFKEY_WPT_ICONSCALE]
                options[GPXData_CONFKEY_WPT_ICONSCALE] = float(value)
            except Exception as e:
                options[GPXData_CONFKEY_WPT_ICONSCALE] = GPXData_WPT_ICONSCALE
                dgettext['error'] = str(e)
                dgettext['key'] = GPXData_CONFKEY_WPT_ICONSCALE
                dgettext['value'] = GPXData_WPT_ICONSCALE
                msg = _("Value of '%(key)s' incorrect: %(error)s. Setting up default value '%(value)s'.")
                self.logger.warning(msg % dgettext)
        else:
            options[GPXData_CONFKEY_WPT_ICONSCALE] = GPXData_WPT_ICONSCALE
        options.setdefault(GPXData_CONFKEY_WPT_ICON, GPXData_WPT_ICON)
        options.setdefault(GPXData_CONFKEY_WPT_DESC, GPXData_WPT_DESC)
        self.wptsinfo = {
            0:{
                GPXData_CONFKEY_WPT_ICON      : options[GPXData_CONFKEY_WPT_ICON],
                GPXData_CONFKEY_WPT_ICONSCALE : options[GPXData_CONFKEY_WPT_ICONSCALE],
                GPXData_CONFKEY_WPT_DESC      : options[GPXData_CONFKEY_WPT_DESC],
                GPXData_CONFKEY_WPT_FTEMPLATE : options[GPXData_CONFKEY_WPT_FTEMPLATE],
            }
        }
        filename = self.state.get_template(GPXData_TRACKS_FTEMPLATE)
        self.track_id = 0
        self.tracksinfo = {
            0:{
                GPXData_CONFKEY_TRACKS_COLOR    : GPXData_GENCOLOR,
                GPXData_CONFKEY_TRACKS_WIDTH    : GPXData_GENWIDTH,
                GPXData_CONFKEY_TRACKS_DESC     : GPXData_GENPATH_DESC,
                GPXData_CONFKEY_TRACKS_FTEMPLATE: filename,
            },
            1:{
                GPXData_CONFKEY_TRACKS_COLOR    : GPXData_TRACKS_COLOR,
                GPXData_CONFKEY_TRACKS_WIDTH    : GPXData_TRACKS_WIDTH,
                GPXData_CONFKEY_TRACKS_DESC     : GPXData_TRACKS_DESC,
                GPXData_CONFKEY_TRACKS_FTEMPLATE: filename,
            }
        }
        for key, value in options.iteritems():
            tmp = key.split(GPXData_CONFKEY_TRACKS_SEPARATOR)
            dgettext['key'] = key
            dgettext['value'] = value
            if len(tmp) > 1:
                try:
                    number = int(tmp[1])
                    if number < 0:
                        raise ValueError(_("Negative index for key"))
                    tkey = tmp[0]
                    if tkey == GPXData_CONFKEY_TRACKS_COLOR:
                        tmp_val = int(value[0:2], 16)
                        tmp_val = int(value[6:8], 16)
                        tmp_val = int(value[4:6], 16)
                        tmp_val = int(value[2:4], 16)
                    elif tkey == GPXData_CONFKEY_TRACKS_WIDTH:
                        tmp_val = int(value)
                    elif tkey == GPXData_CONFKEY_TRACKS_FTEMPLATE:
                        value = self.state.get_template(value)
                        if value == None:
                            raise ValueError(_("Cannot find template file"))
                except Exception as e:
                    dgettext['error'] = str(e)
                    msg = _("Cannot understand the key '%(key)s' in config file: %(error)s.")
                    self.logger.warning(msg % dgettext)
                    continue
                if not self.tracksinfo.has_key(number):
                    self.tracksinfo[number] = dict()
                self.tracksinfo[number][tkey] = value
        self.options = options


    def get_file(self, filename, bytes=102400):
        description = ''
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            description = fd.read(bytes)
        except Exception as e:
            dgettext = dict()
            dgettext['file'] = filename
            dgettext['error'] = str(e)
            msg = _("Cannot read file '%(file)s': %(error)s")
            self.logger.error(msg % dgettext)
        finally:
            if fd != None:
                fd.close()
        return description


    @DRegister("ReadGPX:end")
    def update(self, *args, **kwargs):
        self.tracklist = dict()
        self.trackstyles = dict()
        style = 1
        track_limit = len(self.tracksinfo) - 1
        for track in self.state.gpxdata.tracks:
            if style > track_limit:
                style = 1
            trackstyle = dict(self.tracksinfo[style])
            track.attr['.orig-name'] = str(track.name)
            track.attr['.orig-desc'] = str(track.desc)
            if trackstyle.has_key(GPXData_CONFKEY_TRACKS_NAME):
                track.name = trackstyle[GPXData_CONFKEY_TRACKS_NAME]
            if not trackstyle.has_key(GPXData_CONFKEY_TRACKS_DESC):
                trackstyle[GPXData_CONFKEY_TRACKS_DESC] = GPXData_TRACKS_DESC
            if not trackstyle.has_key(GPXData_CONFKEY_TRACKS_FTEMPLATE):
                trackstyle[GPXData_CONFKEY_TRACKS_FTEMPLATE] = \
                    self.state.get_template(GPXData_TRACKS_FTEMPLATE)
            self.trackstyles[self.track_id] = trackstyle
            self.tracklist[self.track_id] = track
            self.track_id += 1
            style += 1
        wpt_id = 0
        self.wptlist = dict()
        self.wptstyles = dict()
        style = 0
        for wpt in self.state.gpxdata.waypoints:
            wpt.attr['.orig-name'] = wpt.attr.setdefault('name', '')
            wpt.attr['.orig-desc'] = wpt.attr.setdefault('desc', '')
            wptstyle = dict(self.wptsinfo[style])
            if not wptstyle.has_key(GPXData_CONFKEY_WPT_DESC):
                wptstyle[GPXData_CONFKEY_WPT_DESC] = GPXData_WPT_DESC
            if not wptstyle.has_key(GPXData_CONFKEY_WPT_FTEMPLATE):
                wptstyle[GPXData_CONFKEY_WPT_FTEMPLATE] = \
                    self.state.get_template(GPXData_WPT_FTEMPLATE)
            self.wptstyles[wpt_id] = wptstyle
            self.wptlist[wpt_id] = wpt
            wpt_id += 1
        if self.gui:
            self.gui.add_tracks(self.tracklist, self.trackstyles)
            self.gui.add_wpts(self.wptlist, self.wptstyles)
            self.gui.set_tracks_widget(True)
            self.gui.set_wpts_widget(True)


    @DRegister("LoadPhotos:end")
    def loadphotos(self, num_photos):
        if num_photos > 0:
            gengpx, geo_photos = self.maketrack(self.state.geophotos)
            self.photodirlist = dict()
            self.photoliststyles = dict()
            style = 0
            for track in gengpx.tracks:
                trackstyle = dict(self.tracksinfo[style])
                track.attr['.orig-name'] = str(track.name)
                track.attr['.orig-desc'] = str(track.desc)
                if trackstyle.has_key(GPXData_CONFKEY_TRACKS_NAME):
                    track.name = trackstyle[GPXData_CONFKEY_TRACKS_NAME]
                if not trackstyle.has_key(GPXData_CONFKEY_TRACKS_DESC):
                    trackstyle[GPXData_CONFKEY_TRACKS_DESC] = GPXData_GENPATH_DESC
                if not trackstyle.has_key(GPXData_CONFKEY_TRACKS_FTEMPLATE):
                    trackstyle[GPXData_CONFKEY_TRACKS_FTEMPLATE] = \
                        self.state.get_template(GPXData_TRACKS_FTEMPLATE)
                self.photoliststyles[self.track_id] = trackstyle
                self.photodirlist[self.track_id] = track
                self.track_id += 1
            if self.gui:
                self.gui.add_paths(self.photodirlist, self.photoliststyles)
                if geo_photos > 1:
                     self.gui.set_paths_widget(True)


    def maketrack(self, geophotos):
        dgettext = dict()
        tracks = dict()
        gengpx = pyGPX.GPX(GPXData_GPX_GENNAME, datetime.datetime.utcnow())
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
                photo_tutc = photo.time - self.userfacade.state.tzdiff
                dgettext['photo_tutc'] = photo_tutc
                gpxwpt = pyGPX.GPXPoint(photo.lat, photo.lon, photo.ele, photo_tutc, {'id': photo.path})
                msg = _("Generated WayPoint from '%(photo)s' at %(photo_time)s (UTC=%(photo_tutc)s) "
                    "with coordinates (lon=%(photo_lon).8f, lat=%(photo_lat).8f, ele=%(photo_ele).8f).")
                self.logger.debug(msg % dgettext)
                gpxtrkseg.addPoint(gpxwpt)
        proc_photos = 0
        for name, gpxtrkseg in tracks.iteritems():
            dgettext['track_name'] = name
            gpxtrk = pyGPX.GPXTrack(name)
            gpxtrk.status = True
            gengpx.tracks.append(gpxtrk)
            try:
                gpxtrk.addSegment(gpxtrkseg)
                num_photos = len(gpxtrkseg.lwpts)
                proc_photos += num_photos
                dgettext['track_nphotos'] = num_photos
                msg = _("Track '%(track_name)s' was generated from %(track_nphotos)s geotagged photos.")
                self.logger.info(msg % dgettext)
            except pyGPX.GPXError:
                # GPXError if len(gpxtrkseg) == 0
                msg = _("Photo track '%(track_name)s' is empty due to no geotagged photos!")
                self.logger.warning(msg % dgettext)
                gpxtrk.status = False
        return gengpx, proc_photos


    @DRegister("MakeKML:finish")
    def generate(self, *args, **kwargs):
        if not self.state.outputkml:
            return
        name = self.options[GPXData_CONFKEY_NAME]
        kmlgpx = KMLGpxdata.KMLGPXData(name, None, self.state.kmldata.getKml())
        num_tracks = 0
        self.logger.debug(_("Processing all tracks (paths) from GPX data ... "))
        if self.options[GPXData_CONFKEY_GENPATH]:
            self.disable_photo_points()
            num_tracks += self.gentrack(kmlgpx, self.photodirlist, self.photoliststyles)
        if self.state.gpxdata:
            if self.options[GPXData_CONFKEY_GENTRACK]:
                num_tracks += self.gentrack(kmlgpx, self.tracklist, self.trackstyles)
            self.logger.info(_("%s paths have been generated for KML data.") % num_tracks)
            if self.options[GPXData_CONFKEY_GENPOINTS]:
                num_wpoints = self.genwpoints(kmlgpx, self.wptlist, self.wptstyles)
                self.logger.info(_("%s waypoints have been processed for KML data.") % num_wpoints)


    def disable_photo_points(self):
        # Sinc un/selected fotos with path points
        for track_id, track in self.photodirlist.iteritems():
            if not track.status:
                continue
            for point in track.listpoints():
                for gphoto in self.state.geophotos:
                    if point.attr['id'] == gphoto.path:
                        point.status = gphoto.status
                        break


    def gentrack(self, kml, tracklist, styleslist):
        num_tracks = 0
        dgettext = dict()
        for track_id, track in tracklist.iteritems():
            if not track.status:
                continue
            pathdata = TemplateDict(track.attr)
            # Options from 'defaults' section of config file
            pathdata.update(self.defaultsinfo)
            pathdata[PhotoPlace_PathNAME] = track.name
            pathdata[PhotoPlace_PathDESC] = track.desc
            dgettext['path'] = track.name
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
                    if point.status:
                        coor = (point.lon, point.lat, point.ele)
                        coordinates.append(coor)
                        num_points = num_points + 1
                pathdata[PhotoPlace_PathNWPT] = num_points
                # Set data
                style = styleslist[track_id]
                if style[GPXData_CONFKEY_TRACKS_DESC] != None:
                    description = style[GPXData_CONFKEY_TRACKS_DESC] % pathdata
                elif style[GPXData_CONFKEY_TRACKS_FTEMPLATE]:
                    filename = self.state.get_template(style[GPXData_CONFKEY_TRACKS_FTEMPLATE])
                    if filename == None:
                        dgettext['template'] = style[GPXData_CONFKEY_TRACKS_FTEMPLATE]
                        raise ValueError(_("Cannot find template file '%(template)s'") % dgettext)
                    description = self.get_file(filename)
                    description = description % pathdata
                else:
                    description = track.desc
                self.settrack(kml, track.name, description, coordinates, style, track_id)
                # write all data to log
                dgettext['path_npoints'] = num_points
                dgettext['path_nsegments'] = len(track.ltrkseg)
                dgettext['path_len'] = length
                dgettext['path_avgsp'] = savg
                dgettext['path_time'] = duration
                msg = _("Path '%(path)s': points=%(path_npoints)d, segments=%(path_nsegments)d, "
                    "length=%(path_len)s, avgspeed=%(path_avgsp).3f, time='%(path_time)s'")
                self.logger.debug(msg % dgettext)
                num_tracks += 1
            except Exception as e:
                dgettext["error"] = str(e)
                msg = _("Error while processing track '%(path)s': %(error)s.")
                self.logger.error(msg % dgettext)
        return num_tracks


    def settrack(self, kml, name, description, coordinates, style, track_id):
        color = GPXData_TRACKS_COLOR
        if style.has_key(GPXData_CONFKEY_TRACKS_COLOR):
            color = style[GPXData_CONFKEY_TRACKS_COLOR]
        width = GPXData_TRACKS_WIDTH
        if style.has_key(GPXData_CONFKEY_TRACKS_WIDTH):
            width = style[GPXData_CONFKEY_TRACKS_WIDTH]
        styleid = 'track_' + str(track_id)
        kml.new_track_style(styleid, color, width)
        styleid = '#' + styleid
        kml.new_track(coordinates, name, description, styleid)


    def genwpoints(self, kml, wptlist, wptstyles):
        num_wpoints = 0
        dgettext = dict()
        for wpt_id, point in wptlist.iteritems():
            if not point.status:
                continue
            wptdata = TemplateDict(point.attr)
            # Options from 'defaults' section of config file
            wptdata.update(self.defaultsinfo)
            name = point.attr['name']
            desc = point.attr['desc']
            wptdata[PhotoPlace_WptNAME] = name
            wptdata[PhotoPlace_WptDESC] = desc
            wptdata[PhotoPlace_WptLAT] = point.lat
            wptdata[PhotoPlace_WptLON] = point.lon
            wptdata[PhotoPlace_WptELE] = point.ele
            wptdata[PhotoPlace_WptTIME] = point.time
            dgettext['wpt'] = name
            dgettext['wpt_lat'] = "%.8f" % point.lat
            dgettext['wpt_lon'] = "%.8f" % point.lon
            try:
                # Set data
                style = wptstyles[wpt_id]
                if style[GPXData_CONFKEY_WPT_DESC] != None:
                    description = style[GPXData_CONFKEY_WPT_DESC] % wptdata
                elif style[GPXData_CONFKEY_WPT_FTEMPLATE]:
                    filename = self.state.get_template(style[GPXData_CONFKEY_WPT_FTEMPLATE])
                    if filename == None:
                        dgettext['template'] = style[GPXData_CONFKEY_WPT_FTEMPLATE]
                        raise ValueError(_("Cannot find template file '%(template)s'") % dgettext)
                    description = self.get_file(filename)
                    description = description % wptdata
                else:
                    description = desc
                self.setwpt(kml, name, description, point.lat, point.lon, point.ele, style, wpt_id)
                # write all data to log
                msg = _("Setting up WayPoint '%(wpt)s' lat=%(wpt_lat)s, lon=%(wpt_lon)s")
                self.logger.debug(msg % dgettext)
                num_wpoints += 1
            except Exception as e:
                dgettext["error"] = str(e)
                msg = _("Error while processing waypoint '%(wpt)s': %(error)s.")
                self.logger.error(msg % dgettext)
        return num_wpoints


    def setwpt(self, kml, name, description, lat, lon, ele, style, wpt_id):
        icon = GPXData_WPT_ICON
        if style.has_key(GPXData_CONFKEY_WPT_ICON):
            icon = style[GPXData_CONFKEY_WPT_ICON]
        scale = GPXData_WPT_ICONSCALE
        if style.has_key(GPXData_CONFKEY_WPT_ICONSCALE):
            scale = style[GPXData_CONFKEY_WPT_ICONSCALE]
        placemarkid = name
        styleid = 'wpt_' + str(wpt_id)
        kml.new_placemark_style(styleid, icon, scale)
        styleid = '#' + styleid
        kml.new_placemark(lon, lat, ele, name, placemarkid, description, True, styleid)


    def reset(self):
        if self.ready:
            self.track_id = 0
            self.photodirlist = None
            self.photoliststyles = None
            self.wptlist = None
            self.wptstyles = None
            self.tracklist = None
            self.trackstyles = None
            if self.gui:
                self.gui.reset()
            self.logger.debug(_("Resetting Add-on ..."))


    def end(self, options):
        self.ready = 0
        self.tracksinfo = None
        self.wptsinfo = None
        self.defaultsinfo = None
        self.options = None
        self.track_id = 0
        self.photodirlist = None
        self.photoliststyles = None
        self.wptlist = None
        self.wptstyles = None
        self.tracklist = None
        self.trackstyles = None
        if self.gui:
            self.gui.hide(True)
        self.logger.debug(_("Ending Add-on ..."))


# EOF
