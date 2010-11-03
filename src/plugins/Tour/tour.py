#! /usr/bin/env python


import os.path
import sys
import time
import codecs
import urlparse
import math
import xml.dom.minidom
import gettext
import locale


# I18N gettext support
__GETTEXT_DOMAIN__ = "photoplace-tour"
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname("."))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print "Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__)
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
except Exception as e:
    _ = lambda s: s
    print "Error setting up the translations: %s" % (e)


import MP3Info

import DataTypes.kmlData
import gpx
from Plugins.Interface import *
from definitions import *


# Default values
_KmlTour_DIR_APPEND = ".tour"
_KmlTour_SPLIT_CHAR = ";"
_KmlTour_NAME = _("Play me")
_KmlTour_DESC = ""
_KmlTour_KMLTOUR_MUSIC_MIX = False

_KmlTour_BEGIN_WAIT = 4.0
_KmlTour_BEGIN_HEADING = 0
_KmlTour_BEGIN_FLYTIME = 5.0
_KmlTour_BEGIN_TILT = 45.0
_KmlTour_BEGIN_RANGE = 500

_KmlTour_TILT = 30.0    # angulo desde, sentido tierra, sobre la vertical del punto y la camara
_KmlTour_WAIT = 5.0
_KmlTour_FLYTIME = 3.0
_KmlTour_HEADING = 0    # rumbo u orientacion (grados desde el norte)
_KmlTour_RANGE = 100    # distancia desde la que observar los puntos

_KmlTour_FLYMODE = "smooth"
_KmlTour_ALTMODE = "relativeToSeaFloor"

_KmlTour_END_FLYTIME = 5.0
_KmlTour_END_HEADING = 0
_KmlTour_END_TILT = 45.0
_KmlTour_END_RANGE = 1000.0


# Configuration keys
_KmlTour_CONFKEY = "kmltour"
_KmlTour_CONFKEY_KMLTOUR_NAME = "name"
_KmlTour_CONFKEY_KMLTOUR_DESC = "description"
_KmlTour_CONFKEY_KMLTOUR_MUSIC = "mp3list"
_KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX = "mixmp3"

_KmlTour_CONFKEY_BEGIN_WAIT = "beginwait"
_KmlTour_CONFKEY_BEGIN_HEADING = "beginheading"
_KmlTour_CONFKEY_BEGIN_FLYTIME = "beginflytime"
_KmlTour_CONFKEY_BEGIN_TILT = "begintilt"
_KmlTour_CONFKEY_BEGIN_RANGE = "beginrange"
_KmlTour_CONFKEY_WAIT = "wait"
_KmlTour_CONFKEY_HEADING = "heading"
_KmlTour_CONFKEY_FLYTIME = "flytime"
_KmlTour_CONFKEY_TILT = "tilt"
_KmlTour_CONFKEY_RANGE = "range"
_KmlTour_CONFKEY_END_HEADING = "endheading"
_KmlTour_CONFKEY_END_FLYTIME = "endflytime"
_KmlTour_CONFKEY_END_TILT = "endtilt"
_KmlTour_CONFKEY_END_RANGE = "endrange"



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
        'GTK': True,
    }

    def init(self, state, widget_container):
        if not state.options.has_key(_KmlTour_CONFKEY):
            state.options[_KmlTour_CONFKEY] = dict()
        self.name = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_KMLTOUR_NAME, _KmlTour_NAME)
        description = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_KMLTOUR_DESC, _KmlTour_DESC)
        mp3list = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_KMLTOUR_MUSIC, [])
        mix = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX, _KmlTour_KMLTOUR_MUSIC_MIX)
        begin_wait = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_BEGIN_WAIT, _KmlTour_BEGIN_WAIT)
        begin_heading = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_BEGIN_HEADING, _KmlTour_BEGIN_HEADING)
        begin_flytime = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_BEGIN_FLYTIME, _KmlTour_BEGIN_FLYTIME)
        begin_tilt = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_BEGIN_TILT, _KmlTour_BEGIN_TILT)
        begin_range = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_BEGIN_RANGE, _KmlTour_BEGIN_RANGE)
        wait = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_WAIT, _KmlTour_WAIT)
        heading = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_HEADING, _KmlTour_HEADING)
        flytime = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_FLYTIME, _KmlTour_FLYTIME)
        tilt = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_TILT, _KmlTour_TILT)
        range = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_RANGE, _KmlTour_RANGE)
        end_heading = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_END_HEADING, _KmlTour_END_HEADING)
        end_flytime = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_END_FLYTIME, _KmlTour_END_FLYTIME)
        end_tilt = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_END_TILT, _KmlTour_END_TILT)
        end_range = state.options[_KmlTour_CONFKEY].setdefault(
            _KmlTour_CONFKEY_END_RANGE, _KmlTour_END_RANGE)
        self.state = state
        self.geophotos = None
        self.ready = 1


    @DRegister("MakeKML:ini")
    def process_ini(self, *args, **kwargs):
        if not self.ready or not self.state.outputkml:
            return
        self.name = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_KMLTOUR_NAME]
        description = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_KMLTOUR_DESC]
        mp3s = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_KMLTOUR_MUSIC]
        mix = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX]
        begin_wait = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_BEGIN_WAIT]
        begin_heading = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_BEGIN_HEADING]
        begin_flytime = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_BEGIN_FLYTIME]
        begin_tilt = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_BEGIN_TILT]
        begin_range = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_BEGIN_RANGE]
        wait = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_WAIT]
        heading = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_HEADING]
        flytime = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_FLYTIME]
        tilt = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_TILT]
        range = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_RANGE]
        end_heading = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_END_HEADING]
        end_flytime = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_END_FLYTIME]
        end_tilt = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_END_TILT]
        end_range = self.state.options[_KmlTour_CONFKEY][_KmlTour_CONFKEY_END_RANGE]
        try:
            mp3mix = bool(int(mix))
        except:
            mp3mix = _KmlTour_KMLTOUR_MUSIC_MIX
        mp3list = []
        try:
            for mp3 in mp3s.split(_KmlTour_SPLIT_CHAR):
                if os.path.isfile(mp3):
                    mp3list.append(mp3)
        except:
            pass
        utczoneminutes = self.state['utczoneminutes']
        self.str_tzdiff = '-'
        if utczoneminutes < 0:
            utczoneminutes = -utczoneminutes
            self.str_tzdiff = '+'
        hours, remainder = divmod(utczoneminutes, 60)
        minutes, seconds = divmod(remainder, 60)
        self.str_tzdiff = self.str_tzdiff + "%.2d:%.2d" % (hours, minutes)
        self.gxtour = gxTour(mp3list, mp3mix, tilt, wait, range, flytime, heading)
        self.gxtour.set_begin_options(begin_flytime, begin_heading,
            begin_tilt, begin_range, begin_wait)
        self.gxtour.set_end_options(end_flytime, end_heading, end_tilt, end_range)
        self.gxtour.ini(self.name, description)
        self.geophotos = []



    @DRegister("MakeKML:run")
    def process_geophoto(self, geophoto, mode, *args, **kwargs):
        if mode != 1 or not self.ready or not self.state.outputkml:
            return
        self.geophotos.append(geophoto)


    @DRegister("MakeKML:end")
    def process_end(self, num_photos, *args, **kwargs):
        if not self.ready or not self.state.outputkml:
            return
        self.firstitem = (0, 0, 0)
        self.lastitem = (0, 0, 0)
        previous = self.firstitem
        wait_time = 4.0
        range = 0.5
        tilt = 20

        position = 0
        for geophoto in self.geophotos:
            lat = geophoto.lat
            lon = geophoto.lon
            ele = geophoto.ele
            name = geophoto.name
            strtime = geophoto.time.strftime("%Y-%m-%dT%H:%M:%S") + self.str_tzdiff
            if position > 0:
                bearing = gpx.bearingCoord(previous[0], previous[1], lat, lon)
                if range < 1:
                    distance = gpx.distanceCoord(previous[0], previous[1], lat, lon)
                    distance = distance * range
                else:
                    distance = range
            else:
                bearing = 0
                distance = 100

            previous = (lat, lon, ele)

            self.gxtour.do_flyto(lon, lat, ele, strtime, bearing, tilt, distance)
            self.gxtour.do_balloon(name)
            self.gxtour.do_wait(wait_time)
            self.gxtour.do_balloon(name, False)
            self.gxtour.music()
        self.geophotos = None


    @DRegister("MakeKML:finish")
    def generate(self, *args, **kwargs):
        if not self.ready or not self.state.gpxdata or not self.state.outputkml:
            return
        self.outputfile = None
        self.outputdir = None
        self.outputuri = None
        try:
            self.outputfile = os.path.basename(self.state.outputkml)
            if self.state.tmpdir:
                # it is a KMZ, only one kml is allowed ...
                # so we change the extension
                self.outputfile += ".xml"
            outputdir = os.path.split(self.state.outputdir)
            self.outputdir = os.path.join(outputdir[0], outputdir[1])
            self.outputdir += _KmlTour_DIR_APPEND
            state_photouri = self.state['photouri']
            photouri = urlparse.urlsplit(state_photouri)
            scheme = photouri.scheme 
            if os.path.splitdrive(state_photouri)[0]:
                 scheme = ''
            if scheme:
                # URL
                if '%(' in state_photouri:
                    data = {'PhotoPlace.PhotoNAME': self.outputfile}
                    self.outputuri = state_photouri % data
                elif '%s' in state_photouri:
                    self.outputuri = state_photouri % self.outputfile
                else:
                    self.outputuri = state_photouri + self.outputfile
            else:
                self.outputuri = os.path.basename(self.outputdir) + '/' + self.outputfile
            if not os.path.isdir(self.outputdir):
                os.mkdir(self.outputdir)
            self.outputfile = os.path.join(self.outputdir, self.outputfile)
        except Exception as exception:
            self.logger.error(_("Cannot set outputfile: %s.") % str(exception))
            return
        self.logger.debug(_("gx TOUR ... "))
        #self.kmldata.close(self.rootdata)
        # set up a reference to file in main kml dom
        doc = self.state.kmldata.getKml()
        networkLink = doc.createElement("NetworkLink")
        name = doc.createElement("name")
        nameid = doc.createTextNode(str(self.name))
        name.appendChild(nameid)
        networkLink.appendChild(name)
        link = doc.createElement("Link")
        networkLink.appendChild(link)
        href = doc.createElement("href")
        uri = doc.createTextNode(str(self.outputuri))
        href.appendChild(uri)
        link.appendChild(href)
        document = doc.getElementsByTagName("Document")[0]
        document.appendChild(networkLink)


    @DRegister("SaveFiles:startgo")
    def save(self, *args, **kwargs):
        if not self.ready:
            return
        dgettext = dict()
        dgettext['outputfile'] = self.outputfile
        try:
            #return open(source, 'wb')
            fd = codecs.open(self.outputfile, "wb", encoding="utf-8")
        except Exception as exception:
            dgettext['error'] = str(exception)
            msg = _("Cannot open '%(outputfile)s' for writing: %(error)s.")
            self.logger.error(msg % dgettext)
            raise
        else:
            msg = _("Generating output file in '%(outputfile)s' ...")
            self.logger.debug(msg % dgettext)
            try:
                kmldom = self.gxtour.get_kml()
                kmldom.writexml(fd, "", "   ","\n", "utf-8")
            except Exception as exception:
                dgettext['error'] = str(exception)
                msg = _("Cannot write to file '%(outputfile)s': %(error)s.")
                self.logger.error(msg % dgettext)
            finally:
                fd.close()


    def end(self, state):
        self.ready = 0
        self.state = None
        self.name = None
        self.gxtour = None
        self.geophotos = None
        self.outputfile = None
        self.outputdir = None
        self.outputuri = None



class gxTour(object):

    def __init__(self,
        soundlist = [],
        sounds_mix = False,
        tilt = _KmlTour_TILT,
        wait = _KmlTour_WAIT,
        range = _KmlTour_RANGE,
        flytime = _KmlTour_FLYTIME,
        heading = _KmlTour_HEADING):

        object.__init__(self)
        self.begin_wait = _KmlTour_BEGIN_WAIT
        self.begin_heading = _KmlTour_BEGIN_HEADING
        self.begin_flytime = _KmlTour_BEGIN_FLYTIME
        self.begin_tilt = _KmlTour_BEGIN_TILT
        self.begin_range = _KmlTour_BEGIN_RANGE
        #
        self.tilt = tilt
        self.wait = wait
        self.range = range
        self.flytime = flytime
        self.heading = heading
        #
        self.end_flytime = _KmlTour_END_FLYTIME
        self.end_heading = _KmlTour_END_HEADING
        self.end_tilt = _KmlTour_END_TILT
        self.end_range = _KmlTour_END_RANGE
        #
        self.kmldoc = None
        self.playlist = None
        self.tour = None
        self.sounds_mix = False
        self.sounds_index = 0
        self.music_time = 0
        self.total_time = 0
        self.sounds = []
        if soundlist:
            self.set_music(soundlist, sounds_mix)


    def set_begin_options(self,
        begin_flytime = _KmlTour_BEGIN_FLYTIME,
        begin_heading = _KmlTour_BEGIN_HEADING,
        begin_tilt = _KmlTour_BEGIN_TILT,
        begin_range = _KmlTour_BEGIN_RANGE,
        begin_wait = _KmlTour_BEGIN_WAIT ):
        self.begin_wait = begin_wait
        self.begin_heading = begin_heading
        self.begin_flytime = begin_flytime
        self.begin_tilt = begin_tilt
        self.begin_range = begin_range


    def set_end_options(self,
        end_flytime = _KmlTour_END_FLYTIME,
        end_heading = _KmlTour_END_HEADING,
        end_tilt = _KmlTour_END_TILT,
        end_range = _KmlTour_END_RANGE ):
        self.end_flytime = end_flytime
        self.end_heading = end_heading
        self.end_tilt = end_tilt
        self.end_range = end_range


    def set_music(self, mp3list, mix=False):
        for mp3 in mp3list:
            try:
                id3v2 = MP3Info.ID3v2(mp3)
                if id3v2.valid:
                    mpeg = MP3Info.MPEG(mp3, seekstart=id3v2.header_size+10)
                else:
                    mpeg = MP3Info.MPEG(mp3)
                time = mpeg.total_time
                self.sounds.append((mp3, time))
            except Exception as exception:
                print "EXCEPTION", str(exception)
        self.sounds_mix = mix


    def get_kml(self):
        return self.kmldoc


    def ini(self, name, description):
        self.kmldoc = xml.dom.minidom.Document()
        kml = self.kmldoc.createElementNS("http://www.opengis.net/kml/2.2", 'kml')
        kml.setAttribute("xmlns", "http://www.opengis.net/kml/2.2")
        kml.setAttribute("xmlns:gx", "http://www.google.com/kml/ext/2.2")
        self.kmldoc.appendChild(kml)
        document = self.kmldoc.createElement("Document")
        kml.appendChild(document)
        self.tour = self.kmldoc.createElement("gx:Tour")
        name_node = self.kmldoc.createElement("name")
        self.tour.appendChild(name_node)
        description_node = self.kmldoc.createElement("description")
        self.tour.appendChild(description_node)
        name_node.appendChild(self.kmldoc.createTextNode(str(name)))
        description_node.appendChild(self.kmldoc.createTextNode(str(description)))
        self.playlist = self.kmldoc.createElement("gx:Playlist")
        self.tour.appendChild(self.playlist)
        document.appendChild(self.tour)
        self.music()


    def begin(self, name, lon, lat, ele, time):
        self.do_flyto(lon, lat, ele, time,
            self.begin_heading, self.begin_tilt, self.begin_range,
            self.begin_flytime, "bounce")
        self.do_balloon(name)
        self.do_wait(self.begin_wait)
        self.do_balloon(name, False)
        self.music()


    def music(self, mix=None):
        if self.total_time >= self.music_time:
            if mix == None:
                tmp_mix = self.sounds_mix
            else:
                tmp_mix = mix
            if tmp_mix:
                music_time = 0
                for mp3, time in self.sounds:
                    self.do_soundclue(mp3)
                    if time > music_time:
                        music_time = time
                self.music_time += music_time
            elif len(self.sounds) > self.sounds_index:
                mp3, time = self.sounds[self.sounds_index]
                self.do_soundclue(mp3)
                self.music_time += time
                self.sounds_index += 1
            if self.sounds_index >= len(self.sounds):
                self.sounds_index = 0


    def do_soundclue(self, path):
        soundcue = self.kmldoc.createElement("gx:SoundCue")
        href = self.kmldoc.createElement("href")
        href.appendChild(self.kmldoc.createTextNode(path))
        soundcue.appendChild(href)
        self.playlist.appendChild(soundcue)


    def do_wait(self, duration=1.0):
        wait = self.kmldoc.createElement("gx:Wait")
        duration_node = self.kmldoc.createElement("gx:duration")
        duration_node.appendChild(self.kmldoc.createTextNode(str(duration)))
        wait.appendChild(duration_node)
        self.playlist.appendChild(wait)
        self.total_time += duration


    def do_flyto(self, lon, lat, ele, time,
            heading = _KmlTour_HEADING,
            tilt = _KmlTour_TILT,
            rng = _KmlTour_RANGE,
            fly_time = _KmlTour_FLYTIME,
            fly_mode = _KmlTour_FLYMODE,
            altitudemode = _KmlTour_ALTMODE):
        flyto = self.kmldoc.createElement("gx:FlyTo")
        duration = self.kmldoc.createElement("gx:duration")
        duration.appendChild(self.kmldoc.createTextNode(str(fly_time)))
        flyto.appendChild(duration)
        flytomode = self.kmldoc.createElement("gx:flyToMode")
        flytomode.appendChild(self.kmldoc.createTextNode(fly_mode))
        flyto.appendChild(flytomode)
        #timestamp = self.kmldoc.createElement("gx:TimeStamp")
        #when = self.kmldoc.createElement("when")
        #when.appendChild(self.kmldoc.createTextNode(str(time)))
        #timestamp.appendChild(when)
        #flyto.appendChild(timestamp)
        lookat = self.kmldoc.createElement("LookAt")
        longitude_node = self.kmldoc.createElement("longitude")
        longitude_node.appendChild(self.kmldoc.createTextNode(str(lon)))
        lookat.appendChild(longitude_node)
        latitude_node = self.kmldoc.createElement("latitude")
        latitude_node.appendChild(self.kmldoc.createTextNode(str(lat)))
        lookat.appendChild(latitude_node)
        altitude_node = self.kmldoc.createElement("altitude")
        altitude_node.appendChild(self.kmldoc.createTextNode(str(ele)))
        lookat.appendChild(altitude_node)
        heading_node = self.kmldoc.createElement("heading")
        heading_node.appendChild(self.kmldoc.createTextNode(str(heading)))
        lookat.appendChild(heading_node)
        tilt_node = self.kmldoc.createElement("tilt")
        tilt_node.appendChild(self.kmldoc.createTextNode(str(tilt)))
        lookat.appendChild(tilt_node)
        range_node = self.kmldoc.createElement("range")
        range_node.appendChild(self.kmldoc.createTextNode(str(rng)))
        lookat.appendChild(range_node)
        altitudemode_node = self.kmldoc.createElement("gx:altitudeMode")
        altitudemode_node.appendChild(self.kmldoc.createTextNode(altitudemode))
        lookat.appendChild(altitudemode_node)
        flyto.appendChild(lookat)
        self.playlist.appendChild(flyto)
        self.total_time += fly_time

    def do_balloon(self, name, visibility=True):
        animatedupdate = self.kmldoc.createElement("gx:AnimatedUpdate")
        update = self.kmldoc.createElement("Update")
        animatedupdate.appendChild(update)
        targetHref = self.kmldoc.createElement("targetHref")
        update.appendChild(targetHref)
        change = self.kmldoc.createElement("Change")
        update.appendChild(change)
        placemark = self.kmldoc.createElement("Placemark")
        placemark.setAttribute("targetId", name)
        change.appendChild(placemark)
        balloonvisibility = self.kmldoc.createElement("gx:balloonVisibility")
        balloonvisibility.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
        placemark.appendChild(balloonvisibility)
        self.playlist.appendChild(animatedupdate)


    def end(self, name, lon, lat, ele, time, loop=True):
        self.do_flyto(lon, lat, ele, time,
            self.end_heading, self.end_tilt, self.end_range, self.end_flytime)
        self.do_balloon(name)
        if loop:
            heading = self.end_heading
            while self.music_time >= self.total_time:
                heading += 90.0
                heading = math.fmod(heading, 360)
                self.do_flyto(lon, lat, ele, time, heading,
                    self.end_tilt, self.end_range, self.end_flytime)



# EOF
