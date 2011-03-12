#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright © 2010 Jose Riguera Lopez <jriguera@gmail.com>
#
"""
A XML GPX parser based on minidom.
"""

import xml.dom.minidom
import time
import datetime

import os.path
import gettext
import locale

__GETTEXT_DOMAIN__ = "pygpx"
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)


import exceptions
import gpxdata



# ########################
# GPXParser implementation
# ########################

class GPXParser:
    """
    Base class for GPX parser
    """
    
    
    def __init__(self, fd, name, timedelta=datetime.timedelta()):
        """
        GPXParser class constructor
        
        :Parameters:
            -`fd`: file description with GPX data.
            -`name`: identification for file descriptor.
            -`timedelta`: timedelta to add to each waypoint time.
        """
        if not isinstance(timedelta, datetime.timedelta):
            dgettext = dict() 
            dgettext['type_expected'] = datetime.timedelta.__name__
            dgettext['type_got'] = timedelta.__class__.__name__
            msg = _("Time delta type excepted '%(type_expected)s', got '%(type_got)s' instead")
            raise TypeError(msg % dgettext)
        self.timedelta = timedelta
        self.name = name
        self.gpx = None
        self.fd = fd
        self.parse()


    def _parseTime(self, node):
        msg = _("Cannot parse <time> node: ")
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            if node.childNodes \
            and node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                time = node.firstChild.data
                try:
                    yr = int(time[0:4])
                    mn = int(time[5:7])
                    da = int(time[8:10])
                    hr = int(time[11:13])
                    mi = int(time[14:16])
                    se = int(time[17:19])
                    if time[20:]: 
                        tz = time[20:]
                    else: 
                        tz = None
                    dt = datetime.datetime(yr, mn, da, hr, mi, se, 0, None)
                    dt = dt + self.timedelta
                except Exception as e:
                    msg = msg + "[ %s : %s ]" % (e, node.firstChild.data)
                    raise exceptions.GPXErrorParse(msg)
                return dt
            else:
                msg = msg + "[!TEXT_NODE]"
        else:
            msg = msg + "[!ELEMENT_NODE]"
        raise exceptions.GPXErrorParse(msg)


    def _parseLink(self, node):
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            text = ''
            ltype = ''
            lnk = node.getAttribute('href')
            for lnode in node.childNodes:
                if lnode.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                    continue
                if lnode.tagName == "text":
                    if lnode.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                        text = lnode.firstChild.data
                elif lnode.tagName == "type":
                    if lnode.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                        ltype = lnode.firstChild.data
            return (lnk, text, ltype)
        return None


    def _parseAuthor(self, node):
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            name = ''
            email = ''
            link = ('','','')
            for anode in node.childNodes:
                if anode.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                    continue
                if anode.tagName == "name":
                    if anode.childNodes:
                        if anode.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                        or anode.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
                            name = anode.firstChild.data
                elif anode.tagName == "email":
                    emailid = anode.getAttribute('id')
                    emaildomain = anode.getAttribute('domain')
                    email = "%s@%s" % (emailid, emaildomain)
                elif anode.tagName == "link":
                    link = self._parseLink(anode)
                    if link == None:
                        link = ('','','')
            return (name, email, link)
        else:
            return None


    def _parseCopyright(self, node):
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            year = ''
            license = ''
            author =  node.getAttribute('author')
            for cnode in node.childNodes:
                if cnode.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                    continue
                if cnode.tagName == "year":
                    if cnode.childNodes \
                    and cnode.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                            year = cnode.firstChild.data
                elif cnode.tagName == "license":
                    if cnode.childNodes:
                        if cnode.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                        or cnode.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
                            license = cnode.firstChild.data
            return (author, year, license)
        return None


    def _parseWpt(self, wpt):
        msg = _("Cannot parse <wpt> node: ")
        if wpt.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
            msg = msg + "[!ELEMENT_NODE]"
            raise exceptions.GPXErrorParse(msg)
        ele = 0.0
        attr = {}
        lat = 0.0
        lon = 0.0
        string_tags = ["name", "type", "desc", "cmt", "src", "sym"]
        string_tags += ["fix", "magvar", "geoidheight" ]
        string_tags += ["sat", "hdop", "vdop", "pdop", "ageofdgpsdata", "dgpsid" ]
        dt = datetime.datetime.utcnow()
        try:
            lat = float(wpt.getAttribute('lat'))
            lon = float(wpt.getAttribute('lon'))
        except ValueError as valerror:
            msg = msg + "<lat='%s' lon='%s'> [%s]" % (lat, lon, valerror)
            raise exceptions.GPXErrorParse(msg)
        try:
            for node in wpt.childNodes:
                if node.nodeType != xml.dom.minidom.Node.ELEMENT_NODE: 
                    continue
                if node.tagName == "ele": 
                    try:
                        if node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                            ele = float(node.firstChild.data)
                    except:
                        pass
                elif node.tagName == "time":
                    dt = self._parseTime(node)
                elif node.tagName == "link":
                    if not 'link' in attr: 
                        attr['link'] = []
                    try:
                        attr["link"].append(self._parseLink(node))
                    except:
                        pass
                else:
                    if node.childNodes and node.tagName in string_tags:
                        if node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                        or node.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
                            attr[node.tagName] = node.firstChild.data
        except exceptions.GPXErrorParse as gpxerror:
            msg = msg + "<lat='%s' lon='%s'> %s" % (lat, lon, gpxerror)
            raise exceptions.GPXErrorParse(msg)
        except Exception as exception:
            msg = msg + str(exception)
            raise exceptions.GPXErrorParse(msg)
        wpt = gpxdata.GPXPoint(lat, lon, ele, dt, attr)
        return wpt


    def _parseMetadata(self, gpx, meta={}):
        output = meta
        for metadata in gpx.getElementsByTagName('metadata'):
            for node in metadata.childNodes:
                if node.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                    continue
                if node.tagName == "name" or \
                    node.tagName == "desc" or \
                    node.tagName == 'keywords':
                    if node.childNodes \
                    and (node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                    or node.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE):
                        output[node.tagName] = node.firstChild.data
                    else:
                        output[node.tagName] = ""
                elif node.tagName == "time":
                    dt = self._parseTime(node)
                    output['time'] = dt
                elif node.tagName == "bounds":
                    minlat = node.getAttribute("minlat")
                    maxlat = node.getAttribute("maxlat")
                    minlon = node.getAttribute("minlon")
                    maxlon = node.getAttribute("maxlon")
                    output['bounds'] = (minlat, maxlat, minlon, maxlon)
                elif node.tagName == "link":
                    try:
                        if not 'link' in output: 
                            output['link'] = []
                        output['link'].append(self._parseLink(node))
                    except:
                        pass
                elif node.tagName == "author":
                    try:
                        output['author'] = self._parseAuthor(node)
                    except:
                        pass
                elif node.tagName == "copyright":
                    try:
                        output['copyright'] = self._parseCopyright(node)
                    except:
                        pass
        return output


    def parse(self, parsemetadata=True, append=False):
        try:
            dom = xml.dom.minidom.parse(self.fd)
            dom.normalize()
        except Exception as e:
            raise exceptions.GPXErrorParse(str(e))
        attr = dict()
        metadata = dict()
        gpxdom = dom.documentElement
        if gpxdom.hasAttributes():
            for attribute in gpxdom.attributes.keys():
                attr[attribute] = gpxdom.getAttribute(attribute)
        if parsemetadata:
            metadata = self._parseMetadata(gpxdom)
            name = metadata.setdefault('name', self.name)
            time = metadata.setdefault('time', datetime.datetime.utcnow())
            metadata.setdefault('desc', '')
            metadata.setdefault('author', '')
            metadata.setdefault('copyright', '')
        if not append or not self.gpx:
            # create a GPX object
            self.gpx = gpxdata.GPX(name, time, metadata)
        # Waypoints
        for waypoint in gpxdom.getElementsByTagName('wpt'):
            wpt = self._parseWpt(waypoint)
            self.gpx.waypoints.append(wpt)
        # Tracks
        traknumber = 0
        string_tags = ["name", "desc", "type", "src", "cmt", "number"]
        for trk in gpxdom.getElementsByTagName("trk"):
            attr = {}
            traknumber += 1
            for node in trk.childNodes:
                if node.nodeType != node.ELEMENT_NODE:
                    continue
                if node.tagName == "link":
                    if not 'link' in attr: 
                        attr['link'] = []
                    attr["link"].append(self._parseLink(node))
                else:
                    if node.childNodes and node.tagName in string_tags:
                        if node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                        or node.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
                            attr[node.tagName] = node.firstChild.data
            attr.setdefault('number', traknumber)
            if not 'name' in attr.keys(): 
                dgettext = {'track_number': traknumber, 'number': attr["number"]}
                attr["name"] = _("Track number %(track_number)s (%(number)s)") % (dgettext)
            if not 'desc' in attr.keys(): 
                attr.setdefault('type', '')
                attr.setdefault('src', '')
                attr.setdefault('link', '')
                attr["desc"] =  _("Track %(number)s %(type)s. %(src)s. %(link)s.") % (attr)
            gpxtrk = gpxdata.GPXTrack(attr["name"], attr["desc"], attr)
            # TrackSegs
            trksegcounter = 0
            for trkseg in trk.getElementsByTagName("trkseg"):
                trksegcounter = trksegcounter + 1
                gpxtrkseg = gpxdata.GPXSegment(str(trksegcounter))
                trkpts = trkseg.getElementsByTagName("trkpt")
                for trkpt in trkpts:
                    point = self._parseWpt(trkpt)
                    gpxtrkseg.addPoint(point)
                gpxtrk.addSegment(gpxtrkseg)
            self.gpx.tracks.append(gpxtrk)
        # Route. Non time ordered waypoints
        routenumber = 0
        string_tags = ["name", "desc", "type", "src", "cmt", "number"]
        for rte in gpxdom.getElementsByTagName("rte"):
            attr = dict()
            routenumber += 1
            pointlist = []
            for node in rte.childNodes:
                if node.nodeType != node.ELEMENT_NODE:
                    continue
                if node.tagName == "rtept":
                    point = self._parseWpt(node)
                    pointlist.append(point)
                elif node.tagName == "link":
                    if not 'link' in attr: 
                        attr['link'] = []
                    attr["link"].append(self._parseLink(node))
                else:
                    if node.childNodes and node.tagName in string_tags:
                        if node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                        or node.firstChild.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
                            attr[node.tagName] = node.firstChild.data
            attr.setdefault('number', routenumber)
            if not 'name' in attr.keys(): 
                dgettext = {'route_number': routenumber, 'number': attr["number"]}
                attr["name"] = _("Route number %(route_number)s (of %(number)s)") % (dgettext)
            if not 'desc' in attr.keys(): 
                attr.setdefault('type', '')
                attr.setdefault('src', '')
                attr.setdefault('link', '')
                attr["desc"] = _("Route %(number)s %(type)s. %(src)s. %(link)s.") % (attr)
            gpxrte = gpxdata.GPXSegment(attr["name"], attr, pointlist)
            self.gpx.routes.append(gpxrte)


# EOF
