#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       loadPhotosAction.py
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
A module for manage KML templates and generate KML files
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"

import os
import os.path
import xml.dom.minidom
import urllib
import codecs

import sxmltemplate



# #############################
# Exceptions for KmlData module
# #############################

class KmlDataError(Exception):
    """
    Base class for exceptions in KmlData module.
    """
    def __init__(self, msg='KmlDataError!'):
        self.value = msg

    def __str__(self):
        return self.value



# ######################
# KmlData implementation
# ######################

_KmlData_SEPARATOR_XMLNODES = '.'
_KmlData_TEMPLATE_DEFAULT_VALUE = " "
_KmlData_TEMPLATE_SEP_KEY = '|'
_KmlData_TEMPLATE_DEL_TAG = ""

_KmlData_SUBTEMPLATE_ROOT = "div"
_KmlData_SUBTEMPLATE_MODE = "mode"
_KmlData_SUBTEMPLATE_MODE_CDATA = "cdata"
_KmlData_SUBTEMPLATE_MODE_XML = "xml"
_KmlData_SUBTEMPLATE_MODE_TEXT = "text"



class KmlData(object):
    """
    Base class for KML generator module.

    It can mix several template files to complete a global KML layout.
    The position of template files is specified by a path, composed with
    a separator ('.') and the tag name of nodes where template will be
    placed. It is based on sxmltemplate.SXMLTemplate package.
    """

    def __init__(self, layout_file, photo_path = [], xmlinfo = '',
        sep_xmlnodes = _KmlData_SEPARATOR_XMLNODES,
        default_value = _KmlData_TEMPLATE_DEFAULT_VALUE,
        separator_key = _KmlData_TEMPLATE_SEP_KEY,
        delete_tag = _KmlData_TEMPLATE_DEL_TAG):
        """
        KmlData class constructor. It is based on sxmltemplate.SXMLTemplate package.

        :Parameters:
            -`layout_file`: kml global layout file.
            -`photo_path`: list of paths of the nodes that will be completed with
                data, that is, the "repeateable" nodes of "sxmltemplate.SXMLTemplate" class.
            -`sep_xmlnodes`: separator of string node path.
            -`default_value`: default value in data (see "sxmltemplate.SXMLTemplate".
            -`separator_key`: separator for default values in templates.
            -`delete_tag`: tag to delete an empty node.
        """
        object.__init__(self)
        self.templates = {}
        self.phototemplates = {}
        self.othertemplates = {}
        self.xmlinfo = xmlinfo
        self.kml = None
        self.photo_path = photo_path
        self.delete_tag = delete_tag
        self.separator_key = separator_key
        self.default_value = default_value
        self.sep_xmlnodes = sep_xmlnodes
        self.layout_file = layout_file
        self.layout = None
        self.layout = self._opentemplate(self.layout_file)
        self.__setkml()


    def __setkml(self):
        try:
            sxmltemplate.SXMLTemplate.deletetag = self.delete_tag
            sxmltemplate.SXMLTemplate.separatorKey = self.separator_key
            sxmltemplate.SXMLTemplate.defaultValue = self.default_value
            sxmltemplate.SXMLTemplate.separatorXml = self.sep_xmlnodes
            self.kml = sxmltemplate.SXMLTemplate(self.layout.toxml())
        except sxmltemplate.SXMLTemplateError as xmlterror:
            dgettext = dict(layout_file = self.layout_file)
            dgettext['error'] = str(xmlterror)
            msg = _("Cannot set up main KML template from file '%(layout_file)s' "
                "due to: %(error)s.") 
            raise KmlDataError(msg % dgettext)


    def _opentemplate(self, filename):
        dgettext = dict(filename=filename)
        template = None
        fd = None
        try:
            try:
                fd = urllib.urlopen(filename)
            except (IOError, OSError):
                # try to open with native open function (if source is pathname)
                fd = codecs.open(filename, "r", encoding="utf-8")
            template = xml.dom.minidom.parse(fd)
            template.normalize()
        except IOError as (errno, strerror):
            dgettext['errno'] = errno
            dgettext['strerror'] = strerror
            msg = _("Cannot read XML template file '%(filename)s': (%(errno)s) %(strerror)s.") 
            raise KmlDataError(msg % dgettext)
        except ValueError as valueerror:
            dgettext['error'] = str(valueerror)
            msg = _("XML file '%(filename)s' not in UTF-8 format: %(error)s.")
            raise KmlDataError(msg % dgettext)
        except Exception as exception:
            dgettext['error'] = str(exception)
            msg = _("Cannot parse XML template file '%(filename)s': %(error)s.")
            raise KmlDataError(msg % dgettext)
        finally:
            if fd:
                fd.close()
        return template


    def setTemplates(self, templates={}):
        dgettext = dict()
        for lpos, filename in templates.iteritems():
            filename = os.path.expandvars(filename)
            dgettext['template_file'] = filename
            templatedom = self._opentemplate(filename)
            # Check root div
            div_element = templatedom.documentElement.nodeName
            dgettext['key'] = lpos
            if not (div_element and div_element == _KmlData_SUBTEMPLATE_ROOT):
                msg = _("Template '%(template_file)s' for key '%(key)s' "
                    "without root <div> element.")
                raise KmlDataError(msg % dgettext)
            if not templatedom.documentElement.getAttribute(
                _KmlData_SUBTEMPLATE_MODE).lower():
                msg = _("Cannot find root <div mode=[cdata|text|xml]> in template "
                    "'%(template_file)s'.")
                raise KmlDataError(msg % dgettext)
            self.templates[lpos] = templatedom
        # Search lpos of templates in "kml.Document.Folder.Placemark", which
        # become repeteable templates
        for item in self.photo_path:
            for lpos in self.templates.keys():
                lpos_items = lpos.split(self.sep_xmlnodes)
                counter = 0
                for subitem in item.split(self.sep_xmlnodes):
                    if subitem.lower() != lpos_items[counter]:
                        self.othertemplates[lpos] = self.templates[lpos]
                        break
                    counter += 1
                else:
                    self.phototemplates[lpos] = self.templates[lpos]
        # Merge the rest of templates
        for lpos in self.templates.keys():
            lpos_items = lpos.split(self.sep_xmlnodes)
            lpos_items.reverse()
            for node in self.layout.getElementsByTagName(lpos_items[0]):
                # test if this is the correct node
                parent = node.parentNode
                for xmlelement in lpos_items[1:]:
                    if parent.nodeName.lower() != xmlelement:
                        # element does not exists!!
                        break
                    parent = parent.parentNode
                else:
                    # element exists, replace the node with template
                    div_element = self.templates[lpos].documentElement
                    div_mode = div_element.getAttribute(_KmlData_SUBTEMPLATE_MODE).lower()
                    #parent.removeChild(node)
                    if div_mode == _KmlData_SUBTEMPLATE_MODE_CDATA \
                        or div_mode == _KmlData_SUBTEMPLATE_MODE_TEXT :
                        new_node_data = ""
                        if lpos in self.phototemplates.keys():
                            new_node_data = " %%(%s|)s " % lpos
                        else:
                            div_element = self.templates[lpos].documentElement
                            for child in div_element.childNodes:
                                new_node_data += child.toxml()
                        if div_mode == _KmlData_SUBTEMPLATE_MODE_CDATA:
                            newnode = self.layout.createCDATASection(new_node_data)
                        else:
                            newnode = self.layout.createTextNode(new_node_data)
                        node.appendChild(newnode)
                    elif div_mode == _KmlData_SUBTEMPLATE_MODE_XML:
                        for child in div_element.childNodes:
                            node.appendChild(child.cloneNode(True))
                    break
            else:
                # Cannot find key in main template file. Ignoring it.
                pass
        self.__setkml()
        self.kml.setTemplates(self.photo_path)


    def setData(self, data):
        sxmltemplate.SXMLTemplate.deletetag = self.delete_tag
        sxmltemplate.SXMLTemplate.separatorKey = self.separator_key
        sxmltemplate.SXMLTemplate.defaultValue = self.default_value
        sxmltemplate.SXMLTemplate.separatorXml = self.sep_xmlnodes
        photodata = dict(data)
        for phototemkey, phototemdom in self.phototemplates.iteritems():
            pdestemplate = sxmltemplate.SXMLTemplate(phototemdom.toxml())
            pdestemplate.setRootInfo(photodata)
            node_data = ''
            div_element = pdestemplate.getDom().documentElement
            for child in div_element.childNodes:
                node_data += child.toxml()
            photodata[phototemkey] = node_data
        # data to template.
        self.kml.setData(photodata)


    def close(self, data={}):
        self.kml.setRootInfo(data)
        kmldom = self.kml.getDom()
        kmldom.appendChild(kmldom.createComment(self.xmlinfo))


    def getKml(self):
        kmldom = self.kml.getDom()
        return kmldom


# EOF
