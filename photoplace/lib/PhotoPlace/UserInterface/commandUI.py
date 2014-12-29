#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       commandUI.py
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
A command line implementation for a user interface.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import os
import sys

from PhotoPlace.definitions import *
from PhotoPlace.observerHandler import *
from PhotoPlace.stateHandler import *
from PhotoPlace.userFacade import *
from PhotoPlace.Plugins.Interface import *
from Interface import InterfaceUI



class PhotoPlaceCOM(InterfaceUI):
    """
    GTK GUI for PhotoPlace
    """
    _instance = None

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PhotoPlaceCOM, cls).__new__(cls)
        return cls._instance

    def __init__(self, resourcedir=None):
        InterfaceUI.__init__(self, resourcedir)


    def init(self, userfacade):
        self.userfacade = userfacade
        self.plugins = dict()
        self.plugins_error = []
        self.num_photos_process = 0
        # Make a new state
        try:
            self.userfacade.init()
        except Error as e:
            print(e)
            self.userfacade.init(True)


    def loadPlugins(self):
        errors = self.userfacade.load_plugins()
        for p, e in errors.iteritems():
            print(e)
        self.plugins_error = []
        for p in self.userfacade.addons :
            if not p in errors:
                try:
                    error = self.userfacade.activate_plugin(p, None)
                except Error as e:
                    self.plugins_error.append(p)
                    print(e)
                else:
                    if error != None:
                        self.plugins_error.append(p)
                        print(error)
            else:
                self.plugins_error.append(p)


    def unloadPlugins(self):
        pass


    def activate_plugins(self):
        for plg, plgobj in self.userfacade.list_plugins().iteritems():
            if plg in self.plugins or plg in self.plugins_error:
                continue
            if not plgobj.capabilities['UI']:
                # Active all plugins
                try:
                    self.userfacade.init_plugin(plg, '*', None)
                except Error as e:
                    print(e)
                self.plugins[plg] = (plgobj)


    def deactivate_plugins(self):
        for plg in self.plugins.keys():
            plgobj = self.plugins[plg]
            try:
                self.userfacade.end_plugin(plg)
            except Error as e:
                print(e)
            del self.plugins[plg]
        self.plugins = dict()


    def start(self, load_files=True):
        self.activate_plugins()
        if self.action_loadtemplates():
            if self.action_loadphotos():
                if self.userfacade.state['gpxinputfile']:
                    if self.action_readgpx():
                        self.action_geolocate()
                try:
                    self.userfacade.goprocess(True)
                except Error as e:
                    print(e)
        self.deactivate_plugins()


    def action_loadtemplates(self):
        try:
            loadtemplates = self.userfacade.DoTemplates()
            if loadtemplates:
                loadtemplates.run()
                return True
            else:
                return False
        except Error as e:
            print(e)
            return False


    def action_loadphotos(self, directory=None):
        try:
            loadphotos = self.userfacade.LoadPhotos(directory)
            if loadphotos:
                loadphotos.run()
                return True
            else:
                return False
        except Error as e:
            print(e)
            return False


    def action_readgpx(self, filename=None):
        try:
            readgpx = self.userfacade.ReadGPX(filename)
            if readgpx:
                readgpx.run()
                return True
            else:
                return False
        except Error as e:
            print(e)
            return False


    def action_geolocate(self):
        try:
            geolocate = self.userfacade.Geolocate()
            if geolocate:
                geolocate.run()
            else:
                return False
        except Error as e:
            print(e)
            return False
        return True


# EOF

