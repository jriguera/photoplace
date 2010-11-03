#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       commandUI.py
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


import os
import sys

from definitions import *
from observerHandler import *
from stateHandler import *
from userFacade import *
from Plugins.Interface import *
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
        self.num_photos_process = 0
        # Make a new state
        try:
            self.userfacade.init()
        except Error as e:
            print(e)
            self.userfacade.init(True)

    def loadPlugins(self):
        try:
            errors = self.userfacade.load_plugins('*', None)
        except Error as e:
            print(e)
        else:
            for e in errors:
                print(e)

    def unloadPlugins(self):
        pass


    def activate_plugins(self):
        for plg, plgobj in self.userfacade.list_plugins().iteritems():
            if plg in self.plugins:
                continue
            if not plgobj.capabilities['NeedGUI']:
                # Active all plugins
                try:
                    self.userfacade.init_plugin(plg,'*', None)
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
                else:
                    self.action_makegpx()
                
                try:
                    self.userfacade.goprocess()
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


    def action_makegpx(self):
        try:
            makegpx = self.userfacade.MakeGPX()
            if makegpx:
                makegpx.run()
            else:
                return False
        except Error as e:
            print(e)
            return False
        return True


# EOF

