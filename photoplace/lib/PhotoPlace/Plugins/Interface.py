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
Interface definitions for plugins: Class and Register method.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import sys

import pluginManager



__PLUGIN_IVERSION__ = 0.2
__PLUGIN_ICLASS__ = "Plugin"
__PLUGIN_PNAME__ = "PhotoPlace"
__PLUGIN_PVERSION__ = "0.6.0"
(
    PLUGIN_GUI_NO,
    PLUGIN_GUI_GTK,
    PLUGIN_GUI_WEB,
    PLUGIN_GUI_OTHER,
) = range(4)



class Plugin(object):
    """
    The base class from which all plugins are derived.  It is used by the
    plugin loading functions to find all the installed plugins.
    """
    description = "A plugin to ..."
    version = "0.1.0"
    author = "Unknown developer"
    email = "<user@earth.milk>"
    url = "https://github.com/jriguera/photoplace"
    copyright = "(c) Unknown"
    date = "-"
    license = "GPLv3"
    capabilities = {
        'GUI' : PLUGIN_GUI_NO,
        'UI' : False,
    }

    def __init__(self, logger, userfacade, args, argfiles=[], gui=None):
        object.__init__(self)
        self.logger = logger
        self.state = userfacade.state
        self.userfacade = userfacade
        self.argfiles = argfiles
        self.args = args
        self.gui = gui
        self.ready = -1

    def init(self, options, widget_container):
        self.logger.debug("init")
        self.ready = 1
        pass

    def reset(self):
        self.logger.debug("reset")
        pass

    def end(self, options):
        self.logger.debug("end")
        self.ready = 0
        pass



def DRegister(*events):
    """
    This decorator is to be used for registering a function as a plugin for
    a specific event or list of events.
    """
    _debug = False

    def registered_plugin(f):
        for event in events:
            pluginManager.PluginManager.set_event(event, f)
            if _debug:
                sys.stderr.write('DRegister(%s) to %s\n' % (f.__name__, event))
        return f
    return registered_plugin



# EOF
