#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Interface.py
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
UI Interface definition
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "May 2010"
__license__ = "GPL (v3 or later)"
__copyright__ ="(c) Jose Riguera, May 2010"


import os
import sys


class InterfaceUI(object):
    """
    Interface for PhotoPlace UI's
    """

    def __init__(self, resourcedir=None):
        object.__init__(self)
        self.userfacade = None
        self.resourcedir = resourcedir
        if os.name == "nt" or sys.platform.startswith('win'):
            try:
                import win32api
                win32api.SetConsoleCtrlHandler(self.end, True)
            except:
                pass
        else:
            import signal
            signal.signal(signal.SIGTERM, self.end)
            signal.signal(signal.SIGINT, self.end)

    def init(self, userfacade):
        self.userfacade = userfacade
        self.userfacade.init()

    def start(self, load_files=True):
        pass

    def loadPlugins(self):
        pass
    
    def unloadPlugins(self):
        pass

    def end(self):
        self.userfacade.end()


# EOF
