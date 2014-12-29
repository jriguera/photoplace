#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Interface.py
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
UI Interface definition
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


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
