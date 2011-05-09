#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       userFacade.py
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
Public functions and methods of PhotoPlace
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import os
import sys
import threading
import locale
import ConfigParser
import logging
import logging.handlers
import loggingHandler

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
# PhotoPlace UserFacade Definition
# ################################

class UserFacade(object):

    def __init__(self, resources, configfile, args, cfgopt, fargs):
        object.__init__(self)
        # Overwrite default values with command line args
        self.argfiles = []
        self.args = args
        self.resourcedir = resources
        defaultconfig = dict(PhotoPlace_Cfg_default)
        if cfgopt.options:
            for opt in cfgopt.options:
                try:
                    val = opt.split(PhotoPlace_Cfg_optionsep)
                    section = val[0].split(PhotoPlace_Cfg_sectionsep)
                    sec = section[0].strip().lower()
                    key = section[1].strip().lower()
                    value = val[1].strip().lower()
                except:
                    continue
                if not defaultconfig.has_key(sec):
                    defaultconfig[sec] = dict()
                defaultconfig[sec][key] = value
        for argfile in fargs:
            inputext = os.path.splitext(argfile)[1].lower()
            if os.path.isdir(argfile):
                defaultconfig['main']['photoinputdir'] = argfile
            elif inputext == '.kml':
                defaultconfig['main']['outputfile'] = argfile
            elif inputext == '.kmz':
                defaultconfig['main']['outputfile'] = argfile
            elif os.path.isfile(argfile):
                if inputext == '.gpx':
                    defaultconfig['main']['gpxinputfile'] = argfile
                else:
                    self.argfiles.append(argfile)
            else:
                pass
        self.configfile = configfile
        self.options = defaultconfig
        if configfile != None:
            dgettext = dict()
            dgettext['configfile'] = configfile
            try:
                self.options = self.load_config(configfile, defaultconfig)
            except NameError as nameerror:
                dgettext['section'] = str(nameerror)
                msg = _("Configuration file '%(configfile)s' is incomplete: "
                    "cannot find section '[%(section)s]'. Ignoring it!\n")
                sys.stderr.write(msg % dgettext)
            except ValueError as valueerror:
                dgettext['error'] = str(valueerror)
                msg = _("Cannot parse the configuration file '%(configfile)s': "
                    "%(error)s. Ignoring it!\n") % dgettext
                sys.stderr.write(msg)
        else:
            # Make configuration file
            pass
        self.logfile = self.options['main'].setdefault('logfile')
        self.loglevel = self.options['main'].setdefault('loglevel','')
        self.finalize = False
        self.state = None
        self.observers = {}
        # add the handler to the root logger
        self.logger = logging.getLogger()
        self.mainloghandler = loggingHandler.LogRedirectHandler()
        self.mainloghandler.setLevel(logging.DEBUG)
        consoleformatter = logging.Formatter(PhotoPlace_Cfg_consolelogformat)
        self.mainloghandler.setFormatter(consoleformatter)
        self.logger.addHandler(self.mainloghandler)
        if self.logfile != None:
            l = PhotoPlace_Cfg_loglevel
            try:
                level = self.loglevel.lower()
                l = PhotoPlace_Cfg_LogModes[level]
            except:
                pass
            try:
                loghandler = logging.handlers.RotatingFileHandler(
                    self.logfile, maxBytes=2097152, backupCount=5, delay=True)
                loghandler.setLevel(l)
                logformatter = logging.Formatter(PhotoPlace_Cfg_logformat)
                loghandler.setFormatter(logformatter)
                self.logger.addHandler(loghandler)
                self.logger.debug("# ---")
            except Exception as e:
                msg = _("Cannot set logfile '%s'.") % str(e)
                self.logger.error(msg)
        self.logger.setLevel(PhotoPlace_Cfg_loglevel)
        self.pluginmanager = Plugins.pluginManager.PluginManager()
        self.logger.debug("# " + PhotoPlace_name)
        self.logger.debug(
            "# Launched with command line args %s, files: %s" %
            (self.args, self.argfiles))
        self.logger.debug(_("# with configuration file '%s'.") % self.configfile)
        self.logger.debug(_("# main options: %s") % self.options['main'])


    def load_config(self, configfile, defaults):
        try:
            configuration = ConfigParser.ConfigParser()
            configuration.read(configfile)
        except ConfigParser.Error as configerror:
            raise ValueError(str(configerror))
        rconfig = dict()
        current = dict()
        for item in configuration.sections():
            current[item] = dict()
        current.update(PhotoPlace_Cfg_default)
        for section in current.keys():
            dictionary = dict()
            if not configuration.has_section(section):
                raise NameError(section)
            else:
                options = configuration.options(section)
                for option in options:
                    try:
                        dictionary[option] = configuration.get(section, option)
                    except:
                        dictionary[option] = None
            if defaults.has_key(section):
                for key, value in defaults[section].items():
                    dictionary[key] = value
            for key, value in current[section].items():
                if value:
                    dictionary[key] = value
                else:
                    value = dictionary.get(key, None)
                    dictionary[key] = value
            rconfig[section] = dictionary
        return rconfig


    def get_filepath(self, filepath, subdir=TEMPLATES_KEY):
        filename = os.path.expandvars(filepath)
        if not os.path.isfile(filename):
            orig = filename
            filename = os.path.join(self.state.resourcedir_user, filename)
            if not os.path.isfile(filename):
                language = locale.getdefaultlocale()[0]
                filename = os.path.join(self.state.resourcedir, subdir, language, orig)
                if not os.path.isfile(filename):
                    language = language.split('_')[0]
                    filename = os.path.join(self.state.resourcedir, subdir, language, orig)
                    if not os.path.isfile(filename):
                        filename = os.path.join(self.state.resourcedir, subdir, orig)
                if not os.path.isfile(filename):
                    return None
        return filename


    def init(self, defaults=False):
        if defaults:
            self.options = PhotoPlace_Cfg_default
        if self.configfile != None:
            resourcedir_user = os.path.dirname(self.configfile)
        self.state = stateHandler.State(self.resourcedir, self.options['main'], resourcedir_user)


    def end(self):
        #self.end_plugin()
        self.Clear()
        try:
            self.unload_plugins()
        except Exception as exception:
            self.logger.error(str(exception))
        self.logger.debug('# The end! vai vai!')


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
        for plugin, path in self.options["plugins"].iteritems():
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            path = os.path.normpath(path)
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
                tip = _("Check if plugin syntax is correct ... ")
                errors[plugin] = Error(msg, tip, "PluginManagerError")
            except ValueError as valueerror:
                msg = str(valueerror)
                self.logger.error(msg)
                tip = _("Check if plugin path is correct ... ")
                errors[plugin] = Error(msg, tip, "ValueError")
        return errors


    def activate_plugins(self, capability='*', *args):
        errors = {}
        plugins = self.list_plugins(capability)
        for plg in plugins:
            try:
                self.pluginmanager.activate(plugins[plg], self.state, self.args, self.argfiles, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check Plugin base class ... ")
                errors[plg] = Error(msg, tip, "PluginManagerError")
        return errors


    def activate_plugin(self, plugin, *args):
        plugins = self.list_plugins(plugin=plugin)
        if plugin in plugins:
            try:
                self.pluginmanager.activate(plugins[plugin], self.state, self.args, self.argfiles, *args)
            except Plugins.pluginManager.PluginManagerError as pluginerror:
                msg = str(pluginerror)
                self.logger.error(msg)
                tip = _("Check Plugin base class ... ")
                return Error(msg, tip, "PluginManagerError")
        return None


    def unload_plugins(self, capability='*', plugin=None):
        #self.end_plugin(plugin, capability)
        plugins = self.list_plugins(capability, plugin)
        for plg in plugins:
            self.pluginmanager.deactivate(plugins[plg])


    def list_plugins(self, capability='*', plugin=None):
        plugins = {}
        cap = None
        if not capability == '*':
            cap = capability
        for plg in self.pluginmanager.get_plugins(cap):
            if plugin:
                if plg.__module__ == plugin:
                    plugins[plg.__module__] = plg
            else:
                plugins[plg.__module__] = plg
        return plugins


    def init_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot initiate plugin while some operations are pending ...")
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
                tip = _("Check Plugin init method ... ")
                raise Error(msg, tip, "PluginManagerError")
        return value


    def reset_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot reset plugin while some operations are pending ...")
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
                tip = _("Check Plugin reset method ... ")
                raise Error(msg, tip, "PluginManagerError")
        return value


    def end_plugin(self, plugin=None, capability='*', *args):
        if self.finalize:
            msg = _("Cannot finish plugin while some operations are pending ...")
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
                tip = _("Check Plugin end method ... ")
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
            self.state.clear()
        return None


    def DoTemplates(self):
        if self.finalize:
            return None
        dotemplates = Actions.doTemplatesAction.DoTemplates(self.state, self.options)
        self._setObservers(dotemplates)
        return dotemplates


    def LoadPhotos(self, directory=''):
        if self.finalize:
            return None
        if directory != self.state['photoinputdir']:
            self.state['photoinputdir'] = directory
            loadphotos = Actions.loadPhotosAction.LoadPhotos(self.state)
            self._setObservers(loadphotos)
            return loadphotos
        return None


    def ReadGPX(self, filename=''):
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
                dgettext['outputkml'] = self.state.outputdir
                msg = _("Cannot make dir '%(outputkml)s': %(error)s.") % dgettext
                self.logger.error(msg)
                tip = _("Check if dir '%s' exists or is writable.") % self.state.outputdir
                raise Error(msg, tip, e.__class__.__name__)
        if wait:
            self.MakeKML().run()
            self.WriteCopySave().run()
        else:
            self.MakeKML().start()
            self.WriteCopySave().start()


# EOF
