#! /usr/bin/env python

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
from definitions import *
import DataTypes.kmlData
import gpx


# I18N gettext support
__GETTEXT_DOMAIN__ = "photoplace-tour"
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
KmlTour_KMLTOUR_MUSIC_MIX = False
KmlTour_MUSIC_URI = ''
KmlTour_BEGIN_PLCMK = _("Presentation")
KmlTour_END_PLCMK = _("The end")
KmlTour_BEGIN_STYLE =  '#tourfirst'
KmlTour_END_STYLE = '#tourlast'

KmlTour_BEGIN_WAIT = 10.0
KmlTour_BEGIN_HEADING = 0.0
KmlTour_BEGIN_FLYTIME = 8.0
KmlTour_BEGIN_TILT = 80.0
KmlTour_BEGIN_RANGE = 5000.0

KmlTour_TILT = 60.0      # angulo desde, sentido tierra, sobre la vertical del punto y la camara
KmlTour_WAIT = 7.0
KmlTour_FLYTIME = 4.0
KmlTour_HEADING = 0.0    # rumbo u orientacion (grados desde el norte)
KmlTour_RANGE = 1000.0   # distancia desde la que observar los puntos

KmlTour_FLYMODE = "smooth"
KmlTour_ALTMODE = "clampToGround"

KmlTour_END_FLYTIME = 5.0
KmlTour_END_HEADING = 0.0
KmlTour_END_TILT = 45.0
KmlTour_END_RANGE = 100.0


# Configuration keys
KmlTour_CONFKEY = "kmltour"
KmlTour_CONFKEY_KMLTOUR_NAME = "name"
KmlTour_CONFKEY_KMLTOUR_DESC = "description"
KmlTour_CONFKEY_KMLTOUR_MUSIC = "mp3list"
KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX = "mp3mix"
KmlTour_CONFKEY_KMLTOUR_MUSIC_URI = "mp3uri"

KmlTour_CONFKEY_BEGIN_PLCMK = 'beginplacemark'
KmlTour_CONFKEY_BEGIN_STYLE = 'beginstyle'
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

KmlTour_CONFKEY_END_PLCMK = 'endplacemark'
KmlTour_CONFKEY_END_STYLE = 'endstyle'
KmlTour_CONFKEY_END_HEADING = "endheading"
KmlTour_CONFKEY_END_FLYTIME = "endflytime"
KmlTour_CONFKEY_END_TILT = "endtilt"
KmlTour_CONFKEY_END_RANGE = "endrange"


from gxTour import *
import GTKui



class KmlTour(Plugin):

    description = _("A plugin to generate a presentation tour with your photos.")
    version = "0.1.0"
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://code.google.com/p/photoplace/"
    copyright = "(c) Jose Riguera"
    date = "Oct 2010"
    license = "GPLv3"
    capabilities = {
        'GUI' : PLUGIN_GUI_GTK,
        'NeedGUI' : False,
    }
    
    def __init__(self, logger, state, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, state, args, argfiles, gtkbuilder)
        self.options = dict()
        # GTK widgets
        self.gtkui = None
        if gtkbuilder:
            self.gtkui = GTKui.GTKTour(gtkbuilder)
        self.ready = -1


    def _set_option_float(self, options, key, value):
        if options.has_key(key):
            try:
                tmp = options[key]
                options[key] = float(tmp)
            except:
                options[key] = value
                dgettext = dict(key=key, value=value)
                self.logger.debug(
                    _("Incorrect value for '%(key)s', setting default value '%(value)s'.") \
                    % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.debug(
                _("'%(key)s' not defined, setting default value '%(value)s'.") % dgettext)


    def _set_option_float_none(self, options, key, value):
        if options.has_key(key):
            begin_heading = options[key]
            if begin_heading:
                try:
                    options[key] = float(begin_heading)
                except:
                    options[key] = value
                    dgettext = dict(key=key, value=value)
                    self.logger.debug(
                        _("Incorrect value for '%(key)s', setting default value '%(value)s'.") \
                        % dgettext)
        else:
            options[key] = value
            dgettext = dict(key=key, value=value)
            self.logger.debug(
                _("'%(key)s' not defined, setting default value '%(value)s'.") % dgettext)


    def process_variables(self, options, *args, **kwargs):
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_NAME, KmlTour_NAME)
        options.setdefault(KmlTour_CONFKEY_KMLTOUR_DESC, KmlTour_DESC)
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
                    if os.path.isfile(mp3):
                        mp3list.append(mp3)
            except:
                self.logger.debug(_("Incorrect value for '%s'.") % KmlTour_CONFKEY_KMLTOUR_MUSIC)
                pass
            options[KmlTour_CONFKEY_KMLTOUR_MUSIC] = mp3list
        # Placemarks
        options.setdefault(KmlTour_CONFKEY_BEGIN_PLCMK, KmlTour_BEGIN_PLCMK)
        options.setdefault(KmlTour_CONFKEY_BEGIN_STYLE, KmlTour_BEGIN_STYLE)
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_WAIT, KmlTour_BEGIN_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_HEADING, KmlTour_BEGIN_HEADING)
        self._set_option_float(options, KmlTour_CONFKEY_BEGIN_FLYTIME, KmlTour_BEGIN_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_TILT, KmlTour_BEGIN_TILT)
        self._set_option_float_none(options, KmlTour_CONFKEY_BEGIN_RANGE, KmlTour_BEGIN_RANGE)
        self._set_option_float(options, KmlTour_CONFKEY_WAIT, KmlTour_WAIT)
        self._set_option_float_none(options, KmlTour_CONFKEY_HEADING, KmlTour_HEADING)
        self._set_option_float(options, KmlTour_CONFKEY_FLYTIME, KmlTour_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_TILT, KmlTour_TILT)
        self._set_option_float_none(options, KmlTour_CONFKEY_RANGE, KmlTour_RANGE)
        options.setdefault(KmlTour_CONFKEY_END_PLCMK, KmlTour_END_PLCMK)
        options.setdefault(KmlTour_CONFKEY_END_STYLE, KmlTour_END_STYLE)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_HEADING, KmlTour_END_HEADING)
        self._set_option_float(options, KmlTour_CONFKEY_END_FLYTIME, KmlTour_END_FLYTIME)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_TILT, KmlTour_END_TILT)
        self._set_option_float_none(options, KmlTour_CONFKEY_END_RANGE, KmlTour_END_RANGE)
        self.options = options


    def init(self, options, widget):
        if not options.has_key(KmlTour_CONFKEY):
            options[KmlTour_CONFKEY] = dict()
        opt = options[KmlTour_CONFKEY]
        self.process_variables(opt)
        if self.gtkui:
            if self.ready == -1:
                # 1st time
                self.gtkui.show(widget, opt)
            else:
                self.gtkui.show()
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


    def get_description(self, key):
        description = ''
        if self.gtkui:
            description = self.gtkui.get_textview(key)
        else:
            filename = os.path.expandvars(os.path.expanduser(self.options[key]))
            if os.path.isfile(filename):
                try:
                    fd = open(filename, "r")
                    description = fd.read()
                except Exception as exception:
                    self.logger.error(_("Cannot read file '%s'.") % str(exception))
                finally:
                    if fd:
                        fd.close()
        return description


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
                self.center_lat, self.center_lon, self.first_lat, self.first_lon)
        self.gxtour.begin(self.first_lon, self.first_lat, self.first_ele, strtime, 
            begin_name, begin_desc, begin_style, begin_wait, begin_heading, 
            begin_tilt, begin_range, begin_flytime)
        return geophoto


    def set_last(self, str_tzdiff=''):
        num_photo = len(self.state.geophotos) - 1
        geophoto = None
        while num_photo >= 0:
            gphoto = self.state.geophotos[num_photo]
            if gphoto.status > 0 and gphoto.isGeoLocated():
                geophoto = gphoto
                break
            num_photos -= 1
        if num_photo < 0:
            self.logger.debug(_("No photos to process!"))
            return None
        self.last_lat = geophoto.lat
        self.last_lon = geophoto.lon
        self.last_ele = geophoto.ele
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
                self.center_lat, self.center_lon, self.last_lat, self.last_lon)
        self.gxtour.end(self.last_lon, self.last_lat, self.last_ele, strtime,
            end_name, end_desc, end_style, end_heading,
            end_tilt, end_range, end_flytime)
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
        wait = self.options[KmlTour_CONFKEY_WAIT]
        heading = self.options[KmlTour_CONFKEY_HEADING]
        flytime = self.options[KmlTour_CONFKEY_FLYTIME]
        tilt = self.options[KmlTour_CONFKEY_TILT]
        crange = self.options[KmlTour_CONFKEY_RANGE]
        kml = self.state.kmldata.getKml()
        if not kml:
            self.ready = 0
            return
        self.gxtour.ini(name, description, kml)
        # firt point for camera
        geophoto = self.set_first(str_tzdiff)
        if not geophoto:
            self.ready = 0
            return
        self.gxtour.ini(name, description, kml)
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
            bearing = gpx.bearingCoord(previous[0], previous[1], lat, lon)
            if crange < 11:
                distance = gpx.distanceCoord(previous[0], previous[1], lat, lon)
                distance = distance * crange
            else:
                distance = crange
            self.gxtour.do_flyto(lon, lat, ele, strtime, bearing, tilt, distance, flytime)
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
        if self.gtkui:
            self.gtkui.hide()
        self.logger.debug(_("Ending plugin ..."))


# EOF
