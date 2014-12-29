#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       doTemplatesAction.py
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
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import os.path
import time
import locale

import Interface
from PhotoPlace.DataTypes import kmlData
from PhotoPlace.Facade import Error
from PhotoPlace.definitions import *



class DoTemplates(Interface.Action):

    def __init__(self, state, options):
        Interface.Action.__init__(self, state, [state.lock_kmldata])
        self.templates = dict()
        self.kmltemplate = state["kmltemplate"]
        self.dgettext['kmltemplate'] = self.kmltemplate.encode(PLATFORMENCODING)
        self.resourcedir = state.resourcedir
        self.userresourcedir = state.resourcedir_user
        self.key = 'templates'
        self.options = options
        self.kmldata = None


    def ini(self, *args, **kwargs):
        errors = []
        for lpos, filename in self.options[self.key].iteritems():
            template = self.state.get_template(filename)
            if template != None and os.path.isfile(template):
                self.templates[lpos] = template
            else:
                msg = _("Template file '%s' does not exist!.") % filename.encode(PLATFORMENCODING)
                self.logger.error(msg)
                errors.append(filename.encode(PLATFORMENCODING))
        if errors:
            msg = _("Those templates do not exist! : %s.") % errors
            tip = _("Check file path and permissions of templates "
                "defined in the configuration file")
            raise Error(msg, tip, "ValueError")
        self._notify_ini(self.options, self.templates)
        xmlinfo = " XML generated with %s on %s" % (PhotoPlace_name, time.asctime())
        try:
            self.kmldata = kmlData.KmlData(
                self.kmltemplate, PhotoPlace_Cfg_KmlTemplatePhoto_Path, xmlinfo,
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
        self.dgettext['templates'] = ''.join(i.encode(PLATFORMENCODING) + ' ' for i in self.templates)
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
        for variable in self.state.kmldata.photo_variables:
            if not variable in self.state.photovariables:
                self.state.photovariables.append(variable)
        return self.kmldata


# EOF
