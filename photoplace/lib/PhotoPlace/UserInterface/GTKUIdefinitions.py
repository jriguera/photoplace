#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKUIdefinitions.py
#
#   Copyright 2010-2015 Jose Riguera Lopez <jriguera@gmail.com>
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
"""
GTKUI Configuration and default values.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import os.path



GTKUI_RESOURCES_PATH = "gtkui"
GTKUI_RESOURCE_GUIXML = os.path.join(GTKUI_RESOURCES_PATH, "photoplace.ui")
GTKUI_RESOURCE_GUIICON = os.path.join(GTKUI_RESOURCES_PATH, "photoplace.png")
GTKUI_RESOURCE_TemplateEditorGUIXML = os.path.join(GTKUI_RESOURCES_PATH, "templateeditor.ui")
GTKUI_RESOURCE_VariableEditorGUIXML = os.path.join(GTKUI_RESOURCES_PATH, "variableeditor.ui")
GTKUI_RESOURCE_PhotoInfoGUIXML = os.path.join(GTKUI_RESOURCES_PATH, "photoinfo.ui")
GTKUI_GETTEXT_DOMAIN = "photoplace"


TEXVIEWCOMPLETER_SIZE = (400,100)

TREEVIEWPHOTO_GEOLOCATED_COLOR = "#8AE234"
TREEVIEWPHOTO_NORMAL_COLOR = "#4634E3"
TREEVIEWPHOTO_CHANGED_COLOR = "#D134E3"
TREEVIEWPHOTO_PHOTOSIZE = (80, 60)

PIXBUFSIZE_GEOPHOTOINFO = (1136, 852) # (568,426)
TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR = "black"
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
    TREEVIEWPHOTOINFO_COL_VKEY,
    TREEVIEWPHOTOINFO_COL_VALUE,
    TREEVIEWPHOTOINFO_COL_BGCOLOR,
    TREEVIEWPHOTOINFO_COL_TYPE,
    TREEVIEWPHOTOINFO_COL_KEY,
) = range(7)
(
    VARIABLES_COLUMN_KEY,
    VARIABLES_COLUMN_VALUE,
    VARIABLES_COLUMN_EDITABLE,
) = range(3)


# EOF
