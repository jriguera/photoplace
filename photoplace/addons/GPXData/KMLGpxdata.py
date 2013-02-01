#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       KMLGpxdata.py
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


import xml.dom.minidom
import os.path
import gettext
import locale


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



class KMLGPXData(object):

    def __init__(self, name=None, description=None, kmldoc=None, folderopen=True, visibility=True):
        object.__init__(self)
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
        self.rootdoc = self.document
        if name != None and len(name) > 0:
            folder = self.kmldoc.createElement("Folder")
            self.document.appendChild(folder)
            name_node = self.kmldoc.createElement("name")
            name_node.appendChild(self.kmldoc.createTextNode(name))
            folder.appendChild(name_node)
            open_node = self.kmldoc.createElement("open")
            open_node.appendChild(self.kmldoc.createTextNode(str(int(folderopen))))
            folder.appendChild(open_node)
            visibility_node = self.kmldoc.createElement("visibility")
            visibility_node.appendChild(self.kmldoc.createTextNode(str(int(visibility))))
            folder.appendChild(visibility_node)
            self.document = folder
            if description != None and len(description) > 0:
                description_node = self.kmldoc.createElement("description")
                description_node.appendChild(self.kmldoc.createTextNode(description))
                folder.appendChild(description_node)
        self.styles = list()


    def new_track_style(self, styleid, color, width='3'):
        if not styleid in self.styles:
            self.styles.append(styleid)
            style_node = self.kmldoc.createElement("Style")
            style_node.setAttribute("id", styleid)
            line = self.kmldoc.createElement("LineStyle")
            color_node = self.kmldoc.createElement("color")
            color_node.appendChild(self.kmldoc.createTextNode(color))
            width_node = self.kmldoc.createElement("width")
            width_node.appendChild(self.kmldoc.createTextNode(width))
            line.appendChild(color_node)
            line.appendChild(width_node)
            style_node.appendChild(line)
            self.rootdoc.appendChild(style_node)


    def new_placemark_style(self, styleid, icon, scale=None):
        if not styleid in self.styles:
            self.styles.append(styleid)
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
            self.rootdoc.appendChild(style_node)


    def new_track(self, track, name, description, styleid, 
        snippet=None, snippetlines=2, altitudemode='clampToGround', tessellate=1):
        
        placemark = self.kmldoc.createElement("Placemark")
        placemark.setAttribute("id", name)
        name_node = self.kmldoc.createElement("name")
        name_node.appendChild(self.kmldoc.createTextNode(name))
        placemark.appendChild(name_node)
        description_node = self.kmldoc.createElement("description")
        description_node.appendChild(self.kmldoc.createCDATASection(description))
        placemark.appendChild(description_node)
        style_node = self.kmldoc.createElement("styleUrl")
        style_node.appendChild(self.kmldoc.createTextNode(styleid))
        placemark.appendChild(style_node)
        if snippet != None and len(snippet) > 0:
            snippet_node = self.kmldoc.createElement("Snippet")
            try:
                snippet_node.setAttribute("maxLines", str(int(snippetlines)))
                snippet_node.appendChild(self.kmldoc.createTextNode(snippet))
                placemark.appendChild(snippet_node)
            except:
                pass
        linestring_node = self.kmldoc.createElement("LineString")
        placemark.appendChild(linestring_node)
        try:
            tessellate_node = self.kmldoc.createElement("tessellate")
            tessellate_node.appendChild(self.kmldoc.createTextNode(str(int(tessellate))))
        except:
            pass
        linestring_node.appendChild(tessellate_node)
        altitudemode_node = self.kmldoc.createElement("altitudeMode")
        altitudemode_node.appendChild(self.kmldoc.createTextNode(altitudemode))
        linestring_node.appendChild(altitudemode_node)
        coordinates = ''
        for point in track:
            coordinates += "%.8f,%.8f,%.8f " % (point)
        coordinates_node = self.kmldoc.createElement("coordinates")
        coordinates_node.appendChild(self.kmldoc.createTextNode(coordinates))
        linestring_node.appendChild(coordinates_node)
        self.document.appendChild(placemark)


    def new_placemark(self, lon, lat, ele, name, placemarkid=None,
        description=None, visibility=None, style=None, altitudemode="absolute", snippet=None):
        
        placemark = self.kmldoc.createElement("Placemark")
        if placemarkid != None and len(placemarkid) > 0:
            placemark.setAttribute("id", str(placemarkid))
        name_node = self.kmldoc.createElement("name")
        name_node.appendChild(self.kmldoc.createTextNode(name))
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


#EOF
