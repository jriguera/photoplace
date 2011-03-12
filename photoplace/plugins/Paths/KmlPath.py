#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       KmlPath.py
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
KML Implementation.
"""
__program__ = "photoplace.paths"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.2.0"
__date__ = "December 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import xml.dom.minidom


class KmlPath(object):

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
            name_node.appendChild(self.kmldoc.createTextNode(str(name)))
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
                description_node.appendChild(self.kmldoc.createTextNode(str(description)))
                folder.appendChild(description_node)
        self.styles = list()


    def new_style(self, styleid, color, width=3):
        if not styleid in self.styles:
            self.styles.append(str(styleid))
            style_node = self.kmldoc.createElement("Style")
            style_node.setAttribute("id", str(styleid))
            line = self.kmldoc.createElement("LineStyle")
            color_node = self.kmldoc.createElement("color")
            color_node.appendChild(self.kmldoc.createTextNode(str(color)))
            width_node = self.kmldoc.createElement("width")
            width_node.appendChild(self.kmldoc.createTextNode(str(width)))
            line.appendChild(color_node)
            line.appendChild(width_node)
            style_node.appendChild(line)
            self.rootdoc.appendChild(style_node)


    def new_track(self, track, name, description, styleid, 
        snippet=None, snippetlines=2, altitudemode='clampToGround', tessellate=1):
        
        placemark = self.kmldoc.createElement("Placemark")
        placemark.setAttribute("id", name)
        name_node = self.kmldoc.createElement("name")
        name_node.appendChild(self.kmldoc.createTextNode(str(name)))
        placemark.appendChild(name_node)
        description_node = self.kmldoc.createElement("description")
        description_node.appendChild(self.kmldoc.createCDATASection(str(description)))
        placemark.appendChild(description_node)
        style_node = self.kmldoc.createElement("styleUrl")
        style_node.appendChild(self.kmldoc.createTextNode(str(styleid)))
        placemark.appendChild(style_node)
        if snippet != None and len(snippet) > 0:
            snippet_node = self.kmldoc.createElement("Snippet")
            snippet_node.setAttribute("maxLines", str(snippetlines))
            snippet_node.appendChild(self.kmldoc.createTextNode(str(snippet)))
            placemark.appendChild(snippet_node)
        linestring_node = self.kmldoc.createElement("LineString")
        placemark.appendChild(linestring_node)
        tessellate_node = self.kmldoc.createElement("tessellate")
        tessellate_node.appendChild(self.kmldoc.createTextNode(str(tessellate)))
        linestring_node.appendChild(tessellate_node)
        altitudemode_node = self.kmldoc.createElement("altitudeMode")
        altitudemode_node.appendChild(self.kmldoc.createTextNode(str(altitudemode)))
        linestring_node.appendChild(altitudemode_node)
        coordinates = ''
        for point in track:
            coordinates += "%.8f,%.8f,%.8f " % (point)
        coordinates_node = self.kmldoc.createElement("coordinates")
        coordinates_node.appendChild(self.kmldoc.createTextNode(coordinates))
        linestring_node.appendChild(coordinates_node)
        self.document.appendChild(placemark)


#EOF
