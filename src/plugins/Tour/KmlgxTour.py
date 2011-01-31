#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       KmlgxTour.py
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


import xml.dom.minidom
import os.path

import MP3Info
from tour import *



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
                    if uri != None:
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


    def ini(self, name, description, 
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
        if foldername != None:
            folder = self.kmldoc.createElement("Folder")
            self.document.appendChild(folder)
            name_node = self.kmldoc.createElement("name")
            name_node.appendChild(self.kmldoc.createTextNode(str(foldername)))
            folder.appendChild(name_node)
            open_node = self.kmldoc.createElement("open")
            open_node.appendChild(self.kmldoc.createTextNode(str(int(folderopen))))
            folder.appendChild(open_node)
            visibility_node = self.kmldoc.createElement("visibility")
            visibility_node.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
            folder.appendChild(visibility_node)
            self.document = folder
        self.tour = self.kmldoc.createElement("gx:Tour")
        name_node = self.kmldoc.createElement("name")
        self.tour.appendChild(name_node)
        snippet_node = self.kmldoc.createElement("Snippet")
        self.tour.appendChild(snippet_node)
        description_node = self.kmldoc.createElement("description")
        self.tour.appendChild(description_node)
        name_node.appendChild(self.kmldoc.createTextNode(str(name)))
        description_node.appendChild(self.kmldoc.createTextNode(str(description)))
        self.playlist = self.kmldoc.createElement("gx:Playlist")
        self.tour.appendChild(self.playlist)
        self.document.appendChild(self.tour)
        self.music()


    def begin(self, lon, lat, ele, time, name, description, style,
        wait=KmlTour_BEGIN_WAIT,
        heading=KmlTour_BEGIN_FLYTIME, 
        tilt=KmlTour_BEGIN_HEADING, 
        crange=KmlTour_BEGIN_RANGE, 
        flytime=KmlTour_BEGIN_FLYTIME, 
        flymode="bounce", 
        altitudemode='clampToGround'):
        
        placemarckid = datetime.datetime.now().strftime("%Y%j%I%M" + "start")
        self.do_placemark(lon, lat, ele, name, placemarckid, description, 1, style, altitudemode)
        self.do_flyto(lon, lat, ele, time, heading, tilt, crange, flytime, flymode, altitudemode)
        if name != None:
            self.do_balloon(placemarckid)
        self.do_wait(wait)
        if name !=None:
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
                    if uri != None:
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
                if uri != None:
                    try:
                        mp3uri = uri % os.path.basename(mp3)
                    except:
                        mp3uri = uri + os.path.basename(mp3)
                self.do_soundclue(mp3uri)
                self.music_time += time
                self.sound_index += 1
            if self.sound_index >= len(self.sounds):
                self.sound_index = 0


    def do_placemark(self, lon, lat, ele, name, placemarkid=None,
        description=None, visibility=None, style=None, altitudemode=None, snippet=None):
        
        placemark = self.kmldoc.createElement("Placemark")
        if placemarkid != None:
            placemark.setAttribute("id", str(placemarkid))
        self.document.appendChild(placemark)
        name_node = self.kmldoc.createElement("name")
        name_node.appendChild(self.kmldoc.createTextNode(str(name)))
        placemark.appendChild(name_node)
        if visibility != None:
            visibility_node = self.kmldoc.createElement("visibility")
            visibility_node.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
            placemark.appendChild(visibility_node)
        if description != None:
            description_node = self.kmldoc.createElement("description")
            description_node.appendChild(self.kmldoc.createCDATASection(str(description)))
            placemark.appendChild(description_node)
        if style != None:
            style_node = self.kmldoc.createElement("styleUrl")
            style_node.appendChild(self.kmldoc.createTextNode(str(style)))
            placemark.appendChild(style_node)
        snippet_node = self.kmldoc.createElement("Snippet")
        if snippet != None:
            snippet_node.appendChild(self.kmldoc.createTextNode(str(snippet)))
        placemark.appendChild(snippet_node)
        point = self.kmldoc.createElement("Point")
        placemark.appendChild(point)
        altit_node = self.kmldoc.createElement("altitudeMode")
        if altitudemode == None:
            altit_node.appendChild(self.kmldoc.createTextNode("absolute"))
        else:
            altit_node.appendChild(self.kmldoc.createTextNode(str(altitudemode)))
        point.appendChild(altit_node)
        coord_node = self.kmldoc.createElement("coordinates")
        coord_node.appendChild(self.kmldoc.createTextNode("%.8f,%.8f,%.3f" % (lon, lat, ele)))
        point.appendChild(coord_node)


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
            heading = KmlTour_HEADING,
            tilt = KmlTour_TILT,
            rng = KmlTour_RANGE,
            fly_time = KmlTour_FLYTIME,
            fly_mode = KmlTour_FLYMODE,
            altitudemode = KmlTour_ALTMODE):
        
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
           heading=KmlTour_END_FLYTIME, 
           tilt=KmlTour_END_HEADING, 
           crange=KmlTour_END_RANGE, 
           flytime=KmlTour_END_FLYTIME, 
           flymode=KmlTour_FLYMODE, 
           altitudemode='clampToGround'):
        
        placemarckid = datetime.datetime.now().strftime("%Y%j%I%M" + "end")
        self.do_placemark(lon, lat, ele, name, placemarckid, description, 1, style, altitudemode)
        self.do_flyto(lon, lat, ele, time, heading, tilt, crange, flytime, flymode, altitudemode)
        if name != None:
            self.do_balloon(placemarckid)


# EOF
