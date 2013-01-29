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
Interface definitions for plugins: Class and Register method.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import sys

import pluginManager



__PLUGIN_IVERSION__ = 0.1
__PLUGIN_ICLASS__ = "Plugin"
__PLUGIN_PNAME__ = "PhotoPlace"
__PLUGIN_PVERSION__ = "0.5.0"
(
    PLUGIN_GUI_NO,
    PLUGIN_GUI_GTK,
    PLUGIN_GUI_OTHER,
) = range(3)



class Plugin(object):
    """
    The base class from which all plugins are derived.  It is used by the
    plugin loading functions to find all the installed plugins.
    """
    description = "A plugin to ..."
    version = "0.1.0"
    author = "Unknown developer"
    email = "<user@earth.milk>"
    url = "http://code.google.com/p/photoplace/"
    copyright = "(c) Unknown"
    date = "-"
    license = "GPLv3"
    capabilities = {
        'GUI' : PLUGIN_GUI_NO,
        'NeedGUI' : False,
    }

    def __init__(self, logger, userfacade, args, argfiles=[], gtkbuilder=None):
        object.__init__(self)
        self.logger = logger
        self.state = userfacade.state
        self.userfacade = userfacade
        self.argfiles = argfiles
        self.args = args
        self.gtkbuilder = gtkbuilder
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
