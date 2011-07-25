#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKUIdefinitions.py
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
GTKUI Configuration and default values.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"

import os.path



GTKUI_RESOURCES_PATH = u"gtkui"
GTKUI_RESOURCE_GUIXML = os.path.join(GTKUI_RESOURCES_PATH, u"photoplace.ui")
GTKUI_RESOURCE_GUIICON = os.path.join(GTKUI_RESOURCES_PATH, u"photoplace.png")
GTKUI_GETTEXT_DOMAIN = "photoplace"


TEXVIEWCOMPLETER_SIZE = (400,100)

TREEVIEWPHOTO_GEOLOCATED_COLOR = "#8AE234"
TREEVIEWPHOTO_NORMAL_COLOR = "#4634E3"
TREEVIEWPHOTO_CHANGED_COLOR = "#D134E3"
TREEVIEWPHOTO_PHOTOSIZE = (80, 60)

PIXBUFSIZE_GEOPHOTOINFO = (568,426)
TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR = "red"
TREEVIEWPHOTOINFO_GEOPHOTOATTR_COLOR = "green"
TREEVIEWPHOTOINFO_GEOPHOTOEXIF_COLOR = "blue"
(
    TREEVIEWPHOTOS_COL_STATUS,
    TREEVIEWPHOTOS_COL_NAME,
    TREEVIEWPHOTOS_COL_PATH,
    TREEVIEWPHOTOS_COL_DATE,
    TREEVIEWPHOTOS_COL_ACTIVE,
    TREEVIEWPHOTOS_COL_PIXBUF,
    TREEVIEWPHOTOS_COL_MAIN_INFO,
    TREEVIEWPHOTOS_COL_DATA,
    TREEVIEWPHOTOS_COL_VALUE,
    TREEVIEWPHOTOS_COL_BGCOLOR,
    TREEVIEWPHOTOS_COL_PARENT,
    TREEVIEWPHOTOS_COL_DATAEDIT,
    TREEVIEWPHOTOS_COL_INFO,
) = range(13)
(
    TREEVIEWPHOTOINFO_COL_DEL,
    TREEVIEWPHOTOINFO_COL_EDIT,
    TREEVIEWPHOTOINFO_COL_KEY,
    TREEVIEWPHOTOINFO_COL_VALUE,
    TREEVIEWPHOTOINFO_COL_BGCOLOR,
) = range(5)

TEMPLATES_KEY = u"templates"
VARIABLES_KEY = u"defaults"
(
    VARIABLES_COLUMN_KEY,
    VARIABLES_COLUMN_VALUE,
    VARIABLES_COLUMN_EDITABLE,
) = range(3)

VARIABLES_OTHER = [
    'normalplacemark',
    'highlightplacemark',
    'highlightplacemarkballoonbgcolor',
    'highlightplacemarkballoontextcolor',
    'inilatitute',
    'inilongitude',
    'inialtitude',
    'inirange',
    'initilt',
    'iniheading',
]

# EOF
