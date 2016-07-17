#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       definitions.py
#
#   Copyright 2010-2016 Jose Riguera Lopez <jriguera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.2"
__date__ = "Jul 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import re
import zipfile
import logging
import os.path
import locale
import logging
import logging.handlers
from PIL import Image

PLATFORMENCODING = locale.getpreferredencoding()

PhotoPlace_name = "PhotoPlace"
PhotoPlace_version = "0.6.2"
PhotoPlace_url = "PhotoPlace/definitions.py"
PhotoPlace_date = "Jul 2016"
PhotoPlace_onlinehelp = "https://github.com/jriguera/photoplace/wiki"
PhotoPlace_estimated = _("<estimated>")
PhotoPlace_default = _("<default>")

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
PhotoPlace_Cfg_main_photouri = ""
PhotoPlace_Cfg_main_copymode = 2
PhotoPlace_Cfg_main_kmltemplate = "layout.template.kml"
PhotoPlace_Cfg_main_templateseparatorkey = '|'
PhotoPlace_Cfg_main_templatedefaultvalue = " "
PhotoPlace_Cfg_main_templateseparatornodes = '.'
PhotoPlace_Cfg_main_templatedeltag = ""

PhotoPlace_Cfg_default_inialt = 700.0
PhotoPlace_Cfg_default_inirange = 0.0
PhotoPlace_Cfg_default_initilt = 10.0
PhotoPlace_Cfg_default_heading =  0.0


# #######################################
# Interal Configuration. Do not touch !!!
# #######################################

PhotoPlace_Cfg_version = 6200
Photoplace_Cfg_mode_command = 0
Photoplace_Cfg_mode_gui = 1
PhotoPlace_Cfg_dir = os.path.join(
    unicode(os.path.expanduser("~"), PLATFORMENCODING, 'ignore'), ".photoplace")
PhotoPlace_Cfg_file = "photoplace.cfg"
PhotoPlace_Cfg_fileextold = ".old"
PhotoPlace_Cfg_altdir = "conf"
PhotoPlace_Cfg_optionsep = "="
PhotoPlace_Cfg_sectionsep = ":"
PhotoPlace_Cfg_PhotoRegExp = re.compile(r"\.jpg$", re.I)
PhotoPlace_Cfg_KmlTemplatePhoto_Path = ['kml.Document.Folder.Placemark']
PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path = "kml.document.folder.placemark.description"
PhotoPlace_Cfg_TemplateDescriptionPhoto_File = "PhotoDescription.xhtml"
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
    'addons'   : {}
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
PhotoPlace_FILE_DEF_EXTENSION = ".jpg"

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
    'addons'   : [],
}

TEMPLATES_KEY = "templates"
VARIABLES_KEY = "defaults"
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
