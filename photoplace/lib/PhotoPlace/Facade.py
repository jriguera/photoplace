#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Facade.py
#
#       Copyright 2013 Jose Riguera Lopez <jriguera@gmail.com>
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
Public functions and methods of PhotoPlace
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "January 2013"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import os
import threading
import locale
import ConfigParser
import logging
import logging.handlers
import loggingHandler
import time
import datetime

from observerHandler import DObserver



# #######################################
# Main class for Exceptions in Photoplace
# #######################################

class Error(Exception):
    """
    Base class for exceptions
    """
    def __init__(self, msg, tip='', type='Exception', title='Error'):
        self.msg = msg
        self.title = title
        self.tip = tip
        self.type = type

    def __repr__(self):
        return "%s (%s): %s (%s)" % \
            (self.title, str(self.type), self.msg, self.tip)

    def __str__(self):
        return "* %s (%s):\n * %s\n-> %s" % \
            (self.title, str(self.type), self.msg, self.tip)


# #######################################
# Parse string to datetime object
# #######################################

def parse_str_datetime(time_str):
    """Return (<scope>, <datetime.datetime() instance>) for the given
    datetime string.
    
    >>> _datetime_from_str("2009")
    ('year', datetime.datetime(2009, 1, 1, 0, 0))
    >>> _datetime_from_str("2009-12")
    ('month', datetime.datetime(2009, 12, 1, 0, 0))
    >>> _datetime_from_str("2009-12-25")
    ('day', datetime.datetime(2009, 12, 25, 0, 0))
    >>> _datetime_from_str("2009-12-25 13")
    ('hour', datetime.datetime(2009, 12, 25, 13, 0))
    >>> _datetime_from_str("2009-12-25 13:05")
    ('minute', datetime.datetime(2009, 12, 25, 13, 5))
    >>> _datetime_from_str("2009-12-25 13:05:14")
    ('second', datetime.datetime(2009, 12, 25, 13, 5, 14))
    >>> _datetime_from_str("2009-12-25 13:05:14.453728")
    ('microsecond', datetime.datetime(2009, 12, 25, 13, 5, 14, 453728))
    """
    formats = [
        # <scope>, <pattern>, <format>
        ("year", "YYYY", "%Y"),
        ("month", "YYYY-MM", "%Y-%m"),
        ("day", "YYYY-MM-DD", "%Y-%m-%d"),
        ("hour", "YYYY-MM-DD HH", "%Y-%m-%d %H"),
        ("minute", "YYYY-MM-DD HH:MM", "%Y-%m-%d %H:%M"),
        ("second", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
        # ".<microsecond>" at end is manually handled below
        ("microsecond", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
    ]
    for scope, pattern, format in formats:
        if scope == "microsecond":
            # Special handling for microsecond part. AFAIK there isn't a
            # strftime code for this.
            if time_str.count('.') != 1:
                continue
            time_str, microseconds_str = time_str.split('.')
            try:
                microsecond = int((microseconds_str + '000000')[:6])
            except ValueError:
                continue
        try:
            t = datetime.datetime.strptime(time_str, format)
        except ValueError:
            pass
        else:
            if scope == "microsecond":
                t = t.replace(microsecond=microsecond)
            return scope, t
    else:
        raise ValueError



import DataTypes
import Plugins
import Actions
import stateHandler
from definitions import *



# ##############################
# Dictionary Template Definition
# ##############################

class TemplateDict(dict):

    """
    Class for string templates with dictionaries objects and operator %

    This class inherits all attributes, methods, ... from dict and redefines "__getitem__"
    in order to return a default value when an element is not found. The format
    "key<separator>defaultvalue" indicates that if "key" is not found, then "defaultvalue"
    will be returned. It is like an OR: returns value or "defaultvalue".
    It is possible to define a global default value for all keys.
    """
    _SEPARATORKEYTEMPLATE_ = '|'
    _DEFAULTVALUETEMPLATE_ = " "

    def __getitem__(self, key):
        try:
            k, default = key.split(self._SEPARATORKEYTEMPLATE_, 1)
        except ValueError:
            k = key.split(self._SEPARATORKEYTEMPLATE_, 1)[0]
            default = self._DEFAULTVALUETEMPLATE_
        return self.get(k, default)


# ################################
# PhotoPlace Facade Interface
# ################################

class Facade(object):

    def __init__(self, resources, configfile, args, cfgopt, fargs):
        object.__init__(self)
        # Overwrite default values with command line args
        self.argfiles = []
        self.args = args
        self.resourcedir = resources
        self.configfile = configfile
        self.options = dict(PhotoPlace_Cfg_default)
        self.logfile = self.options['main'].setdefault('logfile')
        self.loglevel = self.options['main'].setdefault('loglevel','')
        self.finalize = False
        self.state = None
        self.observers = {}
        self.addons = self.options["addons"]
        # add the handler to the root logger
        self.logger = logging.getLogger()
        self.mainloghandler = loggingHandler.LogRedirectHandler()
        self.mainloghandler.setLevel(logging.DEBUG)
        consoleformatter = logging.Formatter(PhotoPlace_Cfg_consolelogformat)
        self.mainloghandler.setFormatter(consoleformatter)
        self.logger.addHandler(self.mainloghandler)
        self.logger.setLevel(PhotoPlace_Cfg_loglevel)
        self.pluginmanager = Plugins.pluginManager.PluginManager()
        self.logger.debug("# " + PhotoPlace_name)


    def load_config(self, defaults):
        pass
    
    
    def save_config(self, nosections=PhotoPlace_CONFIG_NOCLONE):
        pass
    
    
    def recover_config(self, directory=PhotoPlace_Cfg_altdir):
        pass
    
    
    def init(self, defaults=False):
        if defaults:
            self.options = PhotoPlace_Cfg_default
        self.state = stateHandler.State(self.resourcedir, self.options['main'],)


    def end(self):
        self.Clear()
        try:
            self.unload_plugins()
        except Exception as exception:
            self.logger.error(str(exception))


    def get_geophoto_attr(self, geophoto, options, key, default=None, estimated=None):
        value = options[key]
        try:
            gvalue = geophoto.attr[key]
            if isinstance(gvalue, str):
                gvalue = gvalue.strip()
                if gvalue == PhotoPlace_estimated:
                    value = estimated
                elif gvalue == PhotoPlace_default:
                    value = default
                else:
                    value = gvalue
            else:
                value = gvalue
        except:
            dgettext = dict()
            dgettext['attr'] = key
            msg_warning = _("Warning processing geophoto string attribute '%(attr)s': type not valid!")
            self.logger.debug(msg_warning % dgettext)
        return value


    def get_geophoto_attr_bool(self, geophoto, options, key, default=None, estimated=None):
        value = options[key]
        try:
            gvalue = geophoto.attr[key]
            if isinstance(gvalue, bool):
                value = gvalue
            elif isinstance(gvalue, str):
                gvalue = gvalue.strip()
                if len(gvalue) < 1:
                    pass
                elif gvalue == PhotoPlace_estimated:
                    value = estimated
                elif gvalue == PhotoPlace_default:
                    value = default
                else:
                    value = gvalue.lower() in ["yes", "true", "on", "si", "1"]
            else:
                raise TypeError
        except:
            dgettext = dict()
            dgettext['attr'] = key
            msg_warning = _("Warning processing geophoto bool attribute '%(attr)s': type not valid!")
            self.logger.debug(msg_warning % dgettext)
        return value


    def get_geophoto_attr_number(self, geophoto, options, key, default=None, estimated=None):
        value = options[key]
        try:
            gvalue = geophoto.attr[key]
            if isinstance(gvalue, bool):
                value = float(gvalue)
            elif isinstance(gvalue, float):
                value = gvalue
            elif isinstance(gvalue, int):
                value = float(gvalue)
            elif isinstance(gvalue, str):
                gvalue = gvalue.strip()
                if gvalue == PhotoPlace_estimated:
                    value = estimated
                elif gvalue == PhotoPlace_default:
                    value = default
                else:
                    value = float(gvalue)
            else:
                raise TypeError
        except:
            dgettext = dict()
            dgettext['attr'] = key
            msg_warning = _("Warning processing geophoto number attribute '%(attr)s': type not valid!")
            self.logger.debug(msg_warning % dgettext)
        return value


    # ####################
    # Log Obsevers Section
    # ####################

    def addlogObserver(self, observer, loglevel=[logging.INFO], *args):
        if loglevel:
            observer.filters = [ lambda rec, l: rec.levelno in l ]
        else:
            observer.filters = [ lambda record, thing : True  ]
        self.mainloghandler.addObserver(observer, loglevel, *args)


    def dellogObserver(self, observer):
        self.mainloghandler.delObserver(observer)


    # ###############################
    # Notifiers and observers Section
    # ###############################

    def _setObservers(self, action):
        events = [
            action.__class__.action_ini_event(),
            action.__class__.action_run_event(),
            action.__class__.action_end_event(),
            action.__class__.action_start_event(),
            action.__class__.action_startgo_event(),
            action.__class__.action_finishgo_event(),
            action.__class__.action_finish_event(),
        ]
        for event in self.observers.keys():
            pattern = re.compile(event)
            for action_event in events:
                if pattern.match(action_event):
                    for (observer, args) in self.observers[event]:
                        if action.hasObserver(observer):
                            action.addObserver(observer, action_event, *args)
                        else:
                            action.addObserver(observer, [action_event], *args)
        for event in events:
            action.addObserver(
                self.pluginmanager.trigger, event, self.pluginmanager, event)


    def addNotifier(self, observer, eventlist=['.*'], *args):
        if callable(observer):
            for event in eventlist:
                if not self.observers.has_key(event):
                    self.observers[event] = []
                self.observers[event].append((observer, args))
        else:
            raise TypeError('Object is not callable!')


    def delEvent(self, event):
        if event in self.observers.keys():
            del self.observers[event]
            return True
        return False


    def delNotifier(self, observer, event=None):
        for e in self.observers.keys():
            if not event:
                event = e
            if e == event:
                positions = []
                postion = 0
                for (ob, args) in self.observers[e]:
                    if ob == observer:
                        positions.append(position)
                    position += 1
                for position in positions:
                    self.observers[e].pop(position)


    # #########################
    # Plugin Management Section
    # #########################

    def load_plugins(self):
        errors = {}
        for plugin, path in self.addons.iteritems():
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            path = os.path.normpath(path)
            if not isinstance(path, unicode):
                try:
                    path = unicode(path, PLATFORMENCODING)
                except:
                    pass
            if not os.path.isdir(path):
                new_path = os.path.join(self.state.resourcedir_user, path)
                if not os.path.isdir(new_path):
                    path = os.path.join(self.state.resourcedir, path)
                else:
                    path = new_path
            try:
                self.pluginmanager.load(plugin, path)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check if addon syntax is correct ... ")
                errors[plugin] = Error(msg, tip, "PluginManagerError")
            except ValueError as valueerror:
                msg = str(valueerror)
                self.logger.error(msg)
        return errors


    def activate_plugins(self, capability='*', *args):
        errors = {}
        plugins = self.list_plugins(capability)
        for plg in plugins:
            try:
                self.pluginmanager.activate(plugins[plg], self, self.args, self.argfiles, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check addon base class ... ")
                errors[plg] = Error(msg, tip, "PluginManagerError")
        return errors


    def activate_plugin(self, plugin, *args):
        plugins = self.list_plugins(plugin=plugin)
        if plugin in plugins:
            try:
                self.pluginmanager.activate(plugins[plugin], self, self.args, self.argfiles, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check addon base class ... ")
                return Error(msg, tip, "PluginManagerError")
        return None


    def unload_plugins(self, capability='*', plugin=None):
        self.end_plugin(plugin, capability)
        plugins = self.list_plugins(capability, plugin)
        for plg in plugins:
            self.pluginmanager.deactivate(plugins[plg])


    def list_plugins(self, capability='*', plugin=None):
        plugins = {}
        cap = None
        if not capability == '*':
            cap = capability
        for plg in self.pluginmanager.get_plugins(cap):
            if plugin != None:
                if plg.__module__ == plugin:
                    plugins[plg.__module__] = plg
            else:
                plugins[plg.__module__] = plg
        return plugins


    def init_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot initiate addon while some operations are pending ...")
            self.logger.error(msg)
            tip = _("Wait a moment ... ")
            raise Error(msg, tip, "Error")
        plugins = self.list_plugins(capability, plugin)
        value = None
        for plg in plugins.keys():
            try:
                value = self.pluginmanager.init(plugins[plg], self.options, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check 'Plugin.init' method ... ")
                raise Error(msg, tip, "PluginManagerError")
        return value


    def reset_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot reset addon while some operations are pending ...")
            self.logger.error(msg)
            tip = _("Wait a moment ... ")
            raise Error(msg, tip, "Error")
        plugins = self.list_plugins(capability, plugin)
        value = None
        for plg in plugins.keys():
            try:
                value = self.pluginmanager.reset(plugins[plg], *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check 'Plugin.reset' method ... ")
                raise Error(msg, tip, "PluginManagerError")
        return value


    def end_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot finish addon while some operations are pending ...")
            self.logger.error(msg)
            tip = _("Wait a moment ... ")
            raise Error(msg, tip, "Error")
        plugins = self.list_plugins(capability, plugin)
        value = None
        for plg in plugins.keys():
            try:
                value = self.pluginmanager.end(plugins[plg], self.options, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check 'Plugin.end' method ... ")
                raise Error(msg, tip, "PluginManagerError")
        return value



    # ####################
    # User Actions Section
    # ####################

    def Clear(self):
        if self.finalize:
            msg = _("Cannot clear state while some operations are pending ...")
            self.logger.error(msg)
            tip = _("Wait a moment ... ")
            raise Error(msg, tip, "Error")
        else:
            if self.state:
                self.state.clear()
        return None


    def DoTemplates(self):
        if self.finalize:
            return None
        dotemplates = Actions.doTemplatesAction.DoTemplates(self.state, self.options)
        self._setObservers(dotemplates)
        return dotemplates


    def LoadPhotos(self, directory=u''):
        if self.finalize:
            return None
        if directory != self.state['photoinputdir']:
            self.state['photoinputdir'] = directory
            loadphotos = Actions.loadPhotosAction.LoadPhotos(self.state)
            self._setObservers(loadphotos)
            return loadphotos
        return None


    def ReadGPX(self, filename=u''):
        if filename != self.state['gpxinputfile']:
            self.state['gpxinputfile'] = filename
            readgpx = Actions.readGPXAction.ReadGPX(self.state)
            self._setObservers(readgpx)
            return readgpx
        return None


    def Geolocate(self):
        if self.finalize:
            return None
        geolocate = Actions.geolocateAction.Geolocate(self.state)
        self._setObservers(geolocate)
        return geolocate


    def MakeKML(self):
        if self.finalize:
            return None
        makekml = Actions.makeKMLAction.MakeKML(self.state, self.options['defaults'])
        self._setObservers(makekml)
        return makekml


    def WriteExif(self):
        if self.finalize:
            return None
        writeexif = Actions.writeExifAction.WriteExif(self.state)
        self._setObservers(writeexif)
        return writeexif


    def CopyFiles(self):
        if self.finalize:
            return None
        copy = Actions.copyFilesAction.CopyFiles(self.state)
        self._setObservers(copy)
        return copy


    def SaveFiles(self):
        if self.finalize:
            return None
        savefiles = Actions.saveFilesAction.SaveFiles(self.state)
        self._setObservers(savefiles)
        return savefiles


    def WriteCopySave(self):
        if self.finalize:
            return None
        writefiles = threading.Thread(target=self._WriteCopySave)
        return writefiles


    def _WriteCopySave(self):
        if self.finalize:
            return False
        self.finalize = True
        if self.state['exifmode'] != -1:
            write = Actions.writeExifAction.WriteExif(self.state)
            self._setObservers(write)
            write.run()
        copy = Actions.copyFilesAction.CopyFiles(self.state)
        self._setObservers(copy)
        copy.run()
        save = Actions.saveFilesAction.SaveFiles(self.state)
        self._setObservers(save)
        save.run()
        self.finalize = False
        return True


    def goprocess(self, wait=False):
        if self.finalize:
            msg = _("Some operations are pending ...")
            self.logger.error(msg)
            tip = _("Wait a moment ... ")
            raise Error(msg, tip, "Error")
        if self.state.outputdir:
            try:
                os.makedirs(self.state.outputdir)
            except OSError as exception:
                # dir exists !?
                pass
            except Exception as exception:
                dgettext = dict()
                dgettext['error'] = str(exception)
                dgettext['outputkml'] = self.state.outputdir.encode(PLATFORMENCODING)
                msg = _("Cannot make dir '%(outputkml)s': %(error)s.") % dgettext
                self.logger.error(msg)
                tip = _("Check if that directory exists or is writable.")
                raise Error(msg, tip, e.__class__.__name__)
        if wait:
            self.MakeKML().run()
            self.WriteCopySave().run()
        else:
            self.MakeKML().start()
            self.WriteCopySave().start()


# EOF

