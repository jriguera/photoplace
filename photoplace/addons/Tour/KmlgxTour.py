#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       KmlgxTour.py
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
__date__ = "August 2011"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import xml.dom.minidom
import os.path

import MP3Info
from tour import *


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



class gxTour(object):

    def __init__(self,
        sound_list = [],
        sound_mix = False,
        sound_uri = KmlTour_MUSIC_URI,
        tilt = KmlTour_TILT,
        wait = KmlTour_WAIT,
        crange = KmlTour_RANGE,
        flytime = KmlTour_FLYTIME,
        heading = KmlTour_HEADING):

        object.__init__(self)
        self.tilt = tilt
        self.wait = wait
        self.range = crange
        self.flytime = flytime
        self.heading = heading
        #
        self.kmldoc = None
        self.playlist = None
        self.document = None
        self.tour = None
        self.sound_mix = False
        self.sound_index = 0
        self.sound_uri = ''
        self.music_time = 0
        self.total_time = 0
        self.sounds = []
        if sound_list:
            self.set_music(sound_list, sound_mix, sound_uri)


    def set_music(self, mp3list, mix=False, uri=None):
        self.sound_mix = mix
        for mp3 in mp3list:
            fd = None
            try:
                fd = open(mp3, 'rb')
                id3v2 = MP3Info.ID3v2(fd)
                if id3v2.valid:
                    mpeg = MP3Info.MPEG(fd, seekstart=id3v2.header_size+10)
                else:
                    mpeg = MP3Info.MPEG(fd)
                time = mpeg.total_time
                try:
                    mp3uri = uri % os.path.basename(mp3)
                except:
                    if uri != None and len(uri) > 0:
                        mp3uri = uri + os.path.basename(mp3)
                    else:
                        mp3uri = os.path.basename(mp3)
                self.sounds.append((mp3, time, mp3uri))
            except Exception as exception:
                dgettext = dict(error=str(exception))
                dgettext['mp3file'] = mp3
                raise ValueError(_("Cannot process '%(mp3file)s': %(error)s.") % dgettext)
            finally:
                if fd:
                    fd.close()


    def get_kml(self):
        return self.kmldoc


    def ini(self, name, description, timespan_begin, timespan_end,
        kmldoc=None, foldername=None, folderopen=True, visibility=True):
        
        if not kmldoc:
            self.kmldoc = xml.dom.minidom.Document()
            kml = self.kmldoc.createElementNS("http://www.opengis.net/kml/2.2", 'kml')
            kml.setAttribute("xmlns", "http://www.opengis.net/kml/2.2")
            kml.setAttribute("xmlns:gx", "http://www.google.com/kml/ext/2.2")
            self.document = self.kmldoc.createElement("Document")
            kml.appendChild(self.document)
            self.kmldoc.appendChild(kml)
        else:
            self.document = kmldoc.getElementsByTagName("Document")[0]
            if not self.document:
                return ValueError(_("KML not correct. Cannot found 'Document' tag!"))
            self.kmldoc = kmldoc
        if foldername != None and len(foldername) > 0:
            folder = self.kmldoc.createElement("Folder")
            self.document.appendChild(folder)
            name_node = self.kmldoc.createElement("name")
            name_node.appendChild(self.kmldoc.createTextNode(foldername))
            folder.appendChild(name_node)
            open_node = self.kmldoc.createElement("open")
            open_node.appendChild(self.kmldoc.createTextNode(str(int(folderopen))))
            folder.appendChild(open_node)
            visibility_node = self.kmldoc.createElement("visibility")
            visibility_node.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
            folder.appendChild(visibility_node)
            timespan_node = self.kmldoc.createElement("TimeSpan")
            begintimespan_node = self.kmldoc.createElement("begin")
            begintimespan_node.appendChild(self.kmldoc.createTextNode(str(timespan_begin)))
            timespan_node.appendChild(begintimespan_node)
            endtimespan_node = self.kmldoc.createElement("end")
            endtimespan_node.appendChild(self.kmldoc.createTextNode(str(timespan_end)))
            timespan_node.appendChild(endtimespan_node)
            folder.appendChild(timespan_node)
            self.document = folder
        self.tour = self.kmldoc.createElement("gx:Tour")
        name_node = self.kmldoc.createElement("name")
        self.tour.appendChild(name_node)
        snippet_node = self.kmldoc.createElement("Snippet")
        self.tour.appendChild(snippet_node)
        description_node = self.kmldoc.createElement("description")
        self.tour.appendChild(description_node)
        name_node.appendChild(self.kmldoc.createTextNode(name))
        description_node.appendChild(self.kmldoc.createCDATASection(description))
        self.playlist = self.kmldoc.createElement("gx:Playlist")
        self.tour.appendChild(self.playlist)
        self.document.appendChild(self.tour)
        self.music()


    def begin(self, lon, lat, ele, time, name, description, style,
        wait=KmlTour_BEGIN_WAIT, heading=KmlTour_BEGIN_FLYTIME, tilt=KmlTour_BEGIN_HEADING, 
        crange=KmlTour_BEGIN_RANGE, flytime=KmlTour_BEGIN_FLYTIME, flymode="bounce", 
        altitudemode='clampToGround'):
        
        placemarckid = datetime.datetime.now().strftime("%Y%j%I%M" + "start")
        self.do_placemark(lon, lat, ele, name, placemarckid, description, 1, style, altitudemode)
        self.do_flyto(lon, lat, ele, time, heading, tilt, crange, flytime, flymode, altitudemode)
        if name != None and len(name) > 0:
            self.do_balloon(placemarckid)
        self.do_wait(wait)
        if name != None and len(name) > 0:
            self.do_balloon(placemarckid, False)
        self.music()


    def music(self, mix=None, uri=None):
        if self.total_time >= self.music_time:
            if mix == None:
                tmp_mix = self.sound_mix
            else:
                tmp_mix = mix
            if tmp_mix:
                music_time = 0
                for mp3, time, mp3uri in self.sounds:
                    if uri != None and len(uri) > 0:
                        try:
                            mp3uri = uri % os.path.basename(mp3)
                        except:
                            mp3uri = uri + os.path.basename(mp3)
                    self.do_soundclue(mp3uri)
                    if time > music_time:
                        music_time = time
                self.music_time += music_time
            elif len(self.sounds) > self.sound_index:
                mp3, time, mp3uri = self.sounds[self.sound_index]
                if uri != None and len(uri) > 0:
                    try:
                        mp3uri = uri % os.path.basename(mp3)
                    except:
                        mp3uri = uri + os.path.basename(mp3)
                self.do_soundclue(mp3uri)
                self.music_time += time
                self.sound_index += 1
            if self.sound_index >= len(self.sounds):
                self.sound_index = 0


    def do_placemark_style(self, styleid, icon, scale=None):
        style_node = self.kmldoc.createElement("Style")
        style_node.setAttribute("id", styleid)
        icon_style = self.kmldoc.createElement("IconStyle")
        icon_node = self.kmldoc.createElement("Icon")
        href_node = self.kmldoc.createElement("href")
        href_node.appendChild(self.kmldoc.createTextNode(icon))
        icon_node.appendChild(href_node)
        try:
            fscale = float(scale)
            scale_node = self.kmldoc.createElement("scale")
            scale_node.appendChild(self.kmldoc.createTextNode(str(fscale)))
            icon_style.appendChild(scale_node)
            label_style = self.kmldoc.createElement("LabelStyle")
            scale_node = self.kmldoc.createElement("scale")
            scale_node.appendChild(self.kmldoc.createTextNode(str(fscale)))
            label_style.appendChild(scale_node)
            style_node.appendChild(label_style)
        except:
            pass
        icon_style.appendChild(icon_node)
        style_node.appendChild(icon_style)
        self.document.appendChild(style_node)


    def do_placemark(self, lon, lat, ele, name, placemarkid=None,
        description=None, visibility=None, style=None, altitudemode=KmlTour_ALTMODE, snippet=None):
        
        placemark = self.kmldoc.createElement("Placemark")
        if placemarkid != None and len(placemarkid) > 0:
            placemark.setAttribute("id", str(placemarkid))
        name_node = self.kmldoc.createElement("name")
        name_node.appendChild(self.kmldoc.createTextNode(str(name)))
        placemark.appendChild(name_node)
        try:
            visibility_node = self.kmldoc.createElement("visibility")
            visibility_node.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
            placemark.appendChild(visibility_node)
        except:
            pass
        if description != None and len(description) > 0:
            description_node = self.kmldoc.createElement("description")
            description_node.appendChild(self.kmldoc.createCDATASection(description))
            placemark.appendChild(description_node)
        if style != None and len(style) > 0:
            style_node = self.kmldoc.createElement("styleUrl")
            style_node.appendChild(self.kmldoc.createTextNode(style))
            placemark.appendChild(style_node)
        snippet_node = self.kmldoc.createElement("Snippet")
        if snippet != None and len(snippet) > 0:
            snippet_node.appendChild(self.kmldoc.createTextNode(snippet))
        placemark.appendChild(snippet_node)
        point = self.kmldoc.createElement("Point")
        placemark.appendChild(point)
        altit_node = self.kmldoc.createElement("altitudeMode")
        altit_node.appendChild(self.kmldoc.createTextNode(altitudemode))
        point.appendChild(altit_node)
        coord_node = self.kmldoc.createElement("coordinates")
        coord_node.appendChild(self.kmldoc.createTextNode("%.8f,%.8f,%.3f" % (lon, lat, ele)))
        point.appendChild(coord_node)
        self.document.appendChild(placemark)


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
            heading=KmlTour_HEADING, tilt=KmlTour_TILT, rng=KmlTour_RANGE,
            fly_time=KmlTour_FLYTIME, fly_mode=KmlTour_FLYMODE, altitudemode=KmlTour_ALTMODE):
        
        flyto = self.kmldoc.createElement("gx:FlyTo")
        duration = self.kmldoc.createElement("gx:duration")
        duration.appendChild(self.kmldoc.createTextNode(str(fly_time)))
        flyto.appendChild(duration)
        flytomode = self.kmldoc.createElement("gx:flyToMode")
        flytomode.appendChild(self.kmldoc.createTextNode(fly_mode))
        flyto.appendChild(flytomode)
        timestamp = self.kmldoc.createElement("gx:TimeStamp")
        when = self.kmldoc.createElement("when")
        when.appendChild(self.kmldoc.createTextNode(str(time)))
        timestamp.appendChild(when)
        #flyto.appendChild(timestamp)
        lookat = self.kmldoc.createElement("LookAt")
        longitude_node = self.kmldoc.createElement("longitude")
        longitude_node.appendChild(self.kmldoc.createTextNode("%.8f" % lon))
        lookat.appendChild(longitude_node)
        latitude_node = self.kmldoc.createElement("latitude")
        latitude_node.appendChild(self.kmldoc.createTextNode("%.8f" % lat))
        lookat.appendChild(latitude_node)
        altitude_node = self.kmldoc.createElement("altitude")
        altitude_node.appendChild(self.kmldoc.createTextNode("%.3f" % ele))
        lookat.appendChild(altitude_node)
        if heading != None:
            heading_node = self.kmldoc.createElement("heading")
            heading_node.appendChild(self.kmldoc.createTextNode(str(heading)))
            lookat.appendChild(heading_node)
        if tilt != None:
            tilt_node = self.kmldoc.createElement("tilt")
            tilt_node.appendChild(self.kmldoc.createTextNode(str(tilt)))
            lookat.appendChild(tilt_node)
        if rng != None:
            range_node = self.kmldoc.createElement("range")
            range_node.appendChild(self.kmldoc.createTextNode("%.3f" % rng))
            lookat.appendChild(range_node)
            altitudemode_node = self.kmldoc.createElement("altitudeMode")
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


    def end(self, lon, lat, ele, time, name, description, style,
           heading=KmlTour_END_FLYTIME, tilt=KmlTour_END_HEADING, crange=KmlTour_END_RANGE, 
           flytime=KmlTour_END_FLYTIME, flymode=KmlTour_FLYMODE, altitudemode='clampToGround'):
        
        placemarckid = datetime.datetime.now().strftime("%Y%j%I%M" + "end")
        self.do_placemark(lon, lat, ele, name, placemarckid, description, 1, style, altitudemode)
        self.do_flyto(lon, lat, ele, time, heading, tilt, crange, flytime, flymode, altitudemode)
        if name != None and len(name) > 0:
            self.do_balloon(placemarckid)


# EOF
