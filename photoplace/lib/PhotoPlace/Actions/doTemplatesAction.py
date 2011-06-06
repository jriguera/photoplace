#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       doTemplatesAction.py
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


import os.path
import time
import locale

import Interface
from PhotoPlace.DataTypes import kmlData
from PhotoPlace.userFacade import Error
from PhotoPlace.definitions import *



class DoTemplates(Interface.Action):

    def __init__(self, state, options):
        Interface.Action.__init__(self, state, [state.lock_kmldata])
        self.templates = {}
        self.kmltemplate = state["kmltemplate"]
        self.dgettext['kmltemplate'] = self.kmltemplate
        self.resourcedir = state.resourcedir
        self.userresourcedir = state.resourcedir_user
        self.options = options
        self.kmldata = None


    def ini(self, *args, **kwargs):
        errors = []
        templates_key = 'templates'
        for lpos, filename in self.options[templates_key].iteritems():
            filename = os.path.expandvars(filename)
            file_exist = True
            if not os.path.isfile(filename):
                orig_filename = filename
                filename = os.path.join(self.userresourcedir, filename)
                if not os.path.isfile(filename):
                    language = locale.getdefaultlocale()[0]
                    filename = os.path.join(self.resourcedir, templates_key, language, orig_filename)
                    if not os.path.isfile(filename):
                        language = language.split('_')[0]
                        filename = os.path.join(self.resourcedir, templates_key, language, orig_filename)
                        if not os.path.isfile(filename):
                            filename = os.path.join(self.resourcedir, templates_key, orig_filename)
                    if not os.path.isfile(filename):
                        msg = _("Template file '%s' does not exist!.") % filename
                        self.logger.error(msg)
                        file_exist = False
            if file_exist:
                self.templates[lpos] = filename
            else:
                errors.append(filename)
        if errors:
            msg = _("Those templates do not exist! : %s.") % errors
            tip = _("Check file path and permissions of templates "
                "defined in the configuration file")
            raise Error(msg, tip, "ValueError")
        self._notify_ini(self.options, self.templates)
        xmlinfo = " XML generated with %s on %s" % (PhotoPlace_name, time.asctime())
        try:
            self.kmldata = kmlData.KmlData(
                self.kmltemplate, PhotoPlace_Cfg_KmlTemplatePhotoPath, xmlinfo,
                self.state._templateseparatornodes,
                self.state._templatedefaultvalue,
                self.state._templateseparatorkey,
                self.state._templatedeltag)
        except kmlData.KmlDataError as kmldataerror:
            msg = str(kmldataerror)
            self.logger.error(msg)
            tip = _("Check file path and permissions of 'KmlTemplate' value "
                "defined in the configuration file")
            raise Error(msg, tip, "KmlDataError")
        self.dgettext['templates'] = str(self.templates)
        msg = _("Setting up main template '%(kmltemplate)s'")
        self.logger.info(msg % self.dgettext)
        try:
            self.kmldata.setTemplates(self.templates)
        except kmlData.KmlDataError as kmldataerror:
            msg = str(kmldataerror)
            self.logger.error(msg)
            tip = _("Check paths, permissions and format of the templates "
                "defined into the configuration file.")
            raise Error(msg, tip, "KmlDataError")
        return self.kmldata


    def go(self, rini):
        self._notify_run(self.templates)
        self.state.kmldata = self.kmldata
        return self.kmldata


# EOF
