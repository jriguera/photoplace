#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       definitions.py
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
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import re
import zipfile
import Image
import logging
import os.path
import logging
import logging.handlers



PhotoPlace_name = "PhotoPlace"
PhotoPlace_version = "0.5.0"
PhotoPlace_url = "http://code.google.com/p/photoplace"
PhotoPlace_date = "Sep 2010"

# Variables on templates
PhotoPlace_PhotoNAME = 'PhotoPlace.PhotoNAME'
PhotoPlace_PhotoDATE = 'PhotoPlace.PhotoDATE'
PhotoPlace_PhotoTZDATE = 'PhotoPlace.PhotoTZDATE'
PhotoPlace_PhotoURI = 'PhotoPlace.PhotoURI'
PhotoPlace_PhotoLAT = 'PhotoPlace.PhotoLAT'
PhotoPlace_PhotoLON = 'PhotoPlace.PhotoLON'
PhotoPlace_PhotoELE = 'PhotoPlace.PhotoELE'
PhotoPlace_PhotoWIDTH = 'PhotoPlace.PhotoWIDTH'
PhotoPlace_PhotoHEIGHT = 'PhotoPlace.PhotoHEIGHT'
PhotoPlace_PhotoZOOM = 'PhotoPlace_PhotoZOOM'
PhotoPlace_URI = 'PhotoPlace.URI'

# Default values
PhotoPlace_Cfg_main_exifmode = 0
PhotoPlace_Cfg_main_jpgsize = (0, 0)
PhotoPlace_Cfg_main_jpgzoom = 0.5
PhotoPlace_Cfg_main_quality = 1
PhotoPlace_Cfg_main_maxdeltaseconds = 300
PhotoPlace_Cfg_main_photouri = ""
PhotoPlace_Cfg_main_copyonlygeolocated = True
PhotoPlace_Cfg_main_kmltemplate = os.path.join("templates", "layout.template.kml")
PhotoPlace_Cfg_main_templateseparatorkey = '|'
PhotoPlace_Cfg_main_templatedefaultvalue = " "
PhotoPlace_Cfg_main_templateseparatornodes = '.'
PhotoPlace_Cfg_main_templatedeltag = ""



# #######################################
# Interal Configuration. Do not touch !!!
# #######################################

Photoplace_Cfg_mode_command = 0
Photoplace_Cfg_mode_gui = 1
PhotoPlace_Cfg_dir = os.path.join(os.path.expanduser("~"), ".photoplace")
PhotoPlace_Cfg_file = "photoplace.cfg"
PhotoPlace_Cfg_optionsep = "="
PhotoPlace_Cfg_sectionsep = ":"
PhotoPlace_Cfg_PhotoRegExp = re.compile(r"\.jpg$", re.I)
PhotoPlace_Cfg_GeneratedTrackName =  _("GeoPhotos")
PhotoPlace_Cfg_GeneratedTrackDescription = _("Track from geolocated photos")
PhotoPlace_Cfg_KmlTemplatePhotoPath = ['kml.Document.Folder.Placemark']
PhotoPlace_Cfg_DirMode = 0750
PhotoPlace_Cfg_ExifModes = {
    0 : _('write'),
    1 : _('overwrite'),
    -1: _('nowrite') }
PhotoPlace_Cfg_LogModes = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR }
PhotoPlace_Cfg_default = {
    'main' : {},
    'templates' : {},
    'defaults' : {},
    'plugins' : {} }
PhotoPlace_Cfg_loglevel = logging.DEBUG
PhotoPlace_Cfg_logformat = '%(asctime)s: %(levelname)-7s - %(name)-11s - %(message)s'
PhotoPlace_Cfg_logtextviewformat = '%(asctime)s: %(levelname)-7s - %(name)-11s - %(message)s'
PhotoPlace_Cfg_consoleloglevel = logging.INFO
PhotoPlace_Cfg_consolelogformat = '* %(message)s'
PhotoPlace_Cfg_quality = [
    {'img': Image.NEAREST, 'zip': zipfile.ZIP_DEFLATED },
    {'img': Image.BILINEAR, 'zip': zipfile.ZIP_DEFLATED },
    {'img': Image.BICUBIC, 'zip': zipfile.ZIP_STORED },
    {'img': Image.ANTIALIAS, 'zip': zipfile.ZIP_STORED } ]

# GTKUI Configuration
PhotoPlace_Cfg_TreeViewColorGeo = "#8AE234"
PhotoPlace_Cfg_TreeViewColorNormal = "#4634E3"
PhotoPlace_Cfg_TreeViewColorChanged = "#D134E3"
PhotoPlace_Cfg_TreeViewPhotoSize = (80, 60)
(
    TREEVIEWPHOTOS_COL_STATUS,
    TREEVIEWPHOTOS_COL_NAME,
    TREEVIEWPHOTOS_COL_PATH,
    TREEVIEWPHOTOS_COL_DATE,
    TREEVIEWPHOTOS_COL_ACTIVE,
    TREEVIEWPHOTOS_COL_PIXBUF,
) = range(6)
(
    TREEVIEWPHOTOINFO_COL_DEL,
    TREEVIEWPHOTOINFO_COL_EDIT,
    TREEVIEWPHOTOINFO_COL_KEY,
    TREEVIEWPHOTOINFO_COL_VALUE,
    TREEVIEWPHOTOINFO_COL_BGCOLOR,
) = range(5)
TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR = "red"
TREEVIEWPHOTOINFO_GEOPHOTOATTR_COLOR = "green"
TREEVIEWPHOTOINFO_GEOPHOTOEXIF_COLOR = "blue"


# EOF
