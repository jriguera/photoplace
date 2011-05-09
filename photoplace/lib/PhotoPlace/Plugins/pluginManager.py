#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pluginManager.py
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


import sys
import imp
import logging

import Interface
from PhotoPlace.observerHandler import DObserver



# ###################################
# Exceptions for PluginManager module
# ###################################

class PluginManagerError(Exception):
    """
    Base class for exceptions in PluginManager.
    """
    def __init__(self, msg='PluginManagerError!'):
        self.value = msg

    def __str__(self):
        return self.value



# ############################
# PluginManager implementation
# ############################

class PluginManager(object):

    _instance = None
    events = {}
    
    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        object.__init__(self)
        self.instances = {}
        self.modules = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.trigger.filters = [ lambda event, notification: event == notification ]


    def load(self, module, path=None):
        dgettext = dict(path='sys.path')
        if path != None and not path in sys.path:
            sys.path.insert(0, path)
            dgettext['path'] = path
        dgettext['module'] = module
        fd = None
        #__import__(module, None, None, [''])
        try:
            fd, pathname, desc = imp.find_module(module)
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot find module name '%(module)s' at '%(path)s': %(error)s.")
            raise ValueError(msg % dgettext)
        try:
            self.modules[module] = imp.load_module(module, fd, pathname, desc)
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot load module name '%(module)s': %(error)s.")
            raise PluginManagerError(msg % dgettext)
        finally:
            if fd:
                fd.close()

    def activate(self, plugin, *args, **kwargs):
        dgettext = dict(module=plugin.__module__) 
        if not plugin in self.instances:
            try:
                logger = logging.getLogger(plugin.__module__)
                self.instances[plugin] = plugin(logger, *args, **kwargs)
            except Exception as e:
                dgettext['error'] = str(e)
                msg = _("Cannot activate module name '%(module)s': %(error)s.")
                raise PluginManagerError(msg % dgettext)

    def deactivate(self, plugin):
        if plugin in self.instances.keys():
            del self.instances[plugin]

    def active(self, plugin):
        return plugin in self.instances

    def init(self, plugin, *args, **kwargs):
        dgettext = dict(module=plugin.__module__)
        if not plugin in self.instances:
            msg = _("Cannot init module '%(module)s': Not instanced!.")
            raise PluginManagerError(msg % dgettext)
        p = self.instances[plugin]
        try:
            return p.init(*args, **kwargs)
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot init module '%(module)s': %(error)s.")
            raise PluginManagerError(msg % dgettext)

    def reset(self, plugin, *args, **kwargs):
        dgettext = dict(module=plugin.__module__)
        if not plugin in self.instances:
            msg = _("Cannot init module '%(module)s': Not instanced!.")
            raise PluginManagerError(msg % dgettext)
        p = self.instances[plugin]
        try:
            return p.reset(*args, **kwargs)
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot reset module '%(module)s': %(error)s.")
            raise PluginManagerError(msg % dgettext)
            
    def end(self, plugin, *args, **kwargs):
        dgettext = dict(module=plugin.__module__)
        try:
            p = self.instances[plugin]
        except:
            msg = _("Cannot end module '%(module)s': Not instanced!.")
            raise PluginManagerError(msg % dgettext)
        try:
            p.end(*args, **kwargs)
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot end module '%(module)s': %(error)s.")
            raise PluginManagerError(msg % dgettext)

    def get_plugins(self, capability=None):
        result = []
        if not capability:
            for plugin in Interface.Plugin.__subclasses__():
                result.append(plugin)
        else:
            for plugin in Interface.Plugin.__subclasses__():
                if plugin.capabilities[capability]:
                    result.append(plugin)
        return result

    @classmethod
    def set_event(cls, event, funtion):
        if not cls.events.has_key(event):
            cls.events[event] = []
        cls.events[event].append(funtion)

    @DObserver
    def trigger(self, event, *args, **kwargs):
        """ 
        Call this function to trigger an event. It will run any plugins that
        have registered themselves to the event. Any additional arguments or
        keyword arguments you pass in will be passed to the plugins.
        """
        errors = {}
        if self.events.has_key(event):
            for plugin in self.events[event]:
                name = plugin.__module__
                klass = None
                for k in self.instances.keys():
                    if k.__module__ == name:
                        klass = k
                if klass:
                    try:
                        plugin(self.instances[klass], *args, **kwargs)
                    except Exception as exception:
                        dgettext = dict(module=name)
                        dgettext['error'] = str(exception)
                        msg = _("Exception in plugin '%(module)s' : %(error)s.")
                        self.logger.error(msg % dgettext)
                        errors[name] = exception
        return errors

# EOF

