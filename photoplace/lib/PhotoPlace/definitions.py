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
__copyright__ ="(c) Jose Riguera"


import re
import zipfile
import Image
import logging
import os.path
import locale
import logging
import logging.handlers

PLATFORMENCODING = locale.getpreferredencoding()


PhotoPlace_name = "PhotoPlace"
PhotoPlace_version = "0.5.0"
PhotoPlace_url = "http://code.google.com/p/photoplace"
PhotoPlace_date = "Jan 2011"
PhotoPlace_onlinehelp = "http://code.google.com/p/photoplace/wiki/OnlineHelp"

# Variables on templates
PhotoPlace_PhotoNAME = 'Photo.NAME'
PhotoPlace_PhotoDATE = 'Photo.DATE'
PhotoPlace_PhotoUTCDATE = 'Photo.DATE2UTC'
PhotoPlace_PhotoURI = 'Photo.URI'
PhotoPlace_PhotoLAT = 'Photo.LAT'
PhotoPlace_PhotoLON = 'Photo.LON'
PhotoPlace_PhotoELE = 'Photo.ELE'
PhotoPlace_PhotoPTIME = 'Photo.PTIME'
PhotoPlace_PhotoWIDTH = 'Photo.WIDTH'
PhotoPlace_PhotoHEIGHT = 'Photo.HEIGHT'
PhotoPlace_PhotoZOOM = 'Photo.ZOOM'

PhotoPlace_ResourceURI = 'PhotoPlace.ResourceURI'
PhotoPlace_NumPOINTS = 'PhotoPlace.NunPOINTS'
PhotoPlace_NumTRACKS = 'PhotoPlace.NunTRACKS'
PhotoPlace_MinTime = 'PhotoPlace.MinTime'
PhotoPlace_MaxTime = 'PhotoPlace.MaxTime'
PhotoPlace_DiffTime = 'PhotoPlace.DiffTime'
PhotoPlace_MinLAT = 'PhotoPlace.MinLAT'
PhotoPlace_MaxLAT = 'PhotoPlace.MaxLAT'
PhotoPlace_MinLON = 'PhotoPlace.MinLON'
PhotoPlace_MaxLON = 'PhotoPlace.MaxLON'

PhotoPlace_TEMPLATE_VARS = [
    PhotoPlace_PhotoNAME,
    PhotoPlace_PhotoDATE,
    PhotoPlace_PhotoLAT,
    PhotoPlace_PhotoLON,
    PhotoPlace_PhotoELE,
    PhotoPlace_PhotoPTIME,
    PhotoPlace_PhotoWIDTH,
    PhotoPlace_PhotoHEIGHT,
    PhotoPlace_PhotoZOOM,
    PhotoPlace_PhotoUTCDATE,
    PhotoPlace_PhotoURI,
    PhotoPlace_ResourceURI,
    PhotoPlace_NumPOINTS,
    PhotoPlace_NumTRACKS,
    PhotoPlace_MinTime,
    PhotoPlace_MaxTime,
    PhotoPlace_DiffTime,
    PhotoPlace_MinLAT,
    PhotoPlace_MaxLAT,
    PhotoPlace_MinLON,
    PhotoPlace_MaxLON,
]

# Values from default's section
PhotoPlace_MidLAT = 'inilatitute'
PhotoPlace_MidLON = 'inilongitude'
PhotoPlace_IniALT = 'inialtitude'
PhotoPlace_IniRANGE = 'inirange'
PhotoPlace_IniTILT = 'initilt'
PhotoPlace_IniHEADING = 'iniheading'


# Default values
PhotoPlace_Cfg_main_exifmode = 1
PhotoPlace_Cfg_main_jpgsize = (0, 0)
PhotoPlace_Cfg_main_jpgzoom = 0.15
PhotoPlace_Cfg_main_quality = 1
PhotoPlace_Cfg_main_maxdeltaseconds = 300
PhotoPlace_Cfg_main_timeoffsetseconds = 0
PhotoPlace_Cfg_main_photouri = u""
PhotoPlace_Cfg_main_copyonlygeolocated = True
PhotoPlace_Cfg_main_kmltemplate = u"layout.template.kml"
PhotoPlace_Cfg_main_templateseparatorkey = '|'
PhotoPlace_Cfg_main_templatedefaultvalue = " "
PhotoPlace_Cfg_main_templateseparatornodes = '.'
PhotoPlace_Cfg_main_templatedeltag = ""

PhotoPlace_Cfg_default_inirange = 0.0
PhotoPlace_Cfg_default_initilt = 10.0
PhotoPlace_Cfg_default_heading =  0.0


# #######################################
# Interal Configuration. Do not touch !!!
# #######################################

PhotoPlace_Cfg_version = 05003
Photoplace_Cfg_mode_command = 0
Photoplace_Cfg_mode_gui = 1
PhotoPlace_Cfg_dir = os.path.join(
    unicode(os.path.expanduser("~"), PLATFORMENCODING, 'ignore'), u".photoplace")
PhotoPlace_Cfg_file = u"photoplace.cfg"
PhotoPlace_Cfg_fileextold = u".old"
PhotoPlace_Cfg_altdir = u"conf"
PhotoPlace_Cfg_optionsep = "="
PhotoPlace_Cfg_sectionsep = ":"
PhotoPlace_Cfg_PhotoRegExp = re.compile(r"\.jpg$", re.I)
PhotoPlace_Cfg_KmlTemplatePhoto_Path = ['kml.Document.Folder.Placemark']
PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path = "kml.document.folder.placemark.description"
PhotoPlace_Cfg_TemplateDescriptionPhoto_File = u"PhotoDescription.xhtml"
PhotoPlace_Cfg_DirMode = 0750
PhotoPlace_Cfg_ExifModes = {
    0 : _('write'),
    1 : _('overwrite'),
   -1 : _('nowrite') 
}
PhotoPlace_Cfg_LogModes = {
    "info"   : logging.INFO,
    "debug"  : logging.DEBUG,
    "warning": logging.WARNING,
    "error"  : logging.ERROR 
}
PhotoPlace_Cfg_default = {
    'main'      : {},
    'templates' : {
        PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path :
            PhotoPlace_Cfg_TemplateDescriptionPhoto_File,
    },
    'defaults'  : {
        'name'        : '',
        'photofolder' : _("Photos"),
        'defaultvalue': "-",
    },
    'plugins'   : {} 
}
PhotoPlace_Cfg_timeformat = _("%A %d. %B %Y")
PhotoPlace_Cfg_loglevel = logging.DEBUG
PhotoPlace_Cfg_logformat = '%(asctime)s: %(levelname)-7s - %(name)-11s - %(message)s'
PhotoPlace_Cfg_logtextviewformat = '%(asctime)s: %(levelname)-7s - %(name)-11s - %(message)s'
PhotoPlace_Cfg_consoleloglevel = logging.INFO
PhotoPlace_Cfg_consolelogformat = '* %(message)s'
PhotoPlace_Cfg_quality = [
    {'img': Image.NEAREST, 'zip': zipfile.ZIP_DEFLATED },
    {'img': Image.BILINEAR, 'zip': zipfile.ZIP_DEFLATED },
    {'img': Image.BICUBIC, 'zip': zipfile.ZIP_STORED },
    {'img': Image.ANTIALIAS, 'zip': zipfile.ZIP_STORED } 
]

# This settings wont be saved with configuration (by default)
PhotoPlace_CONFIG_NOCLONE = {
    'main'      : [
        'version',
        'photoinputdir', 
        'gpxinputfile', 
        'outputfile', 
        'kmltemplate', 
        'utczoneminutes', 
        'photouri',
        ],
    'defaults'  : [
        'name', 
        'date', 
        'inilatitute',
        'inilongitude',
        'inialtitude',
        'inirange',
        'initilt',
        'iniheading',
    ],
    'templates' : [],
    'plugins'   : [],
}


VARIABLES_OTHER = [
    'normalplacemark',
    'normalplacemarkscale',
    'normalplacemarkcolor',
    'normalplacemarklabelscale',
    'normalplacemarklabelcolor',
    'highlightplacemark',
    'highlightplacemarkscale',
    'highlightplacemarkcolor',
    'highlightplacemarklabelscale',
    'highlightplacemarklabelcolor',
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
