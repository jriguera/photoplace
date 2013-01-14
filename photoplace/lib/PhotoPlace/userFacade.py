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
import shutil
import codecs
import threading
import locale
import ConfigParser
import logging
import logging.handlers
import loggingHandler
import datetime
import getpass

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
        if not isinstance(resources, unicode):
            try:
                self.resourcedir = unicode(resources, PLATFORMENCODING)
            except:
                pass
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
            if not isinstance(argfile, unicode):
                try:
                    argfile = unicode(argfile, PLATFORMENCODING)
                except:
                    pass
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
        if not isinstance(configfile, unicode):
            try:
                self.configfile = unicode(configfile, PLATFORMENCODING)
            except:
                pass
        self.options = defaultconfig
        if not self._load_config(self.configfile, defaultconfig):
            dgettext = dict()
            if self.configfile != None and os.path.exists(self.configfile):
                path = os.path.dirname(self.configfile)
                old_configfile = self.configfile + PhotoPlace_Cfg_fileextold
                try:
                    shutil.copyfile(self.configfile, old_configfile)
                except Exception as exception:
                    dgettext['error'] = str(exception)
                    dgettext['file'] = old_configfile.encode(PLATFORMENCODING)
                    msg = _("Cannot create backup of configfile '%(file)s': %(error)s.\n")
                    sys.stderr.write(msg % dgettext)
            source_path = os.path.join(self.resourcedir, PhotoPlace_Cfg_altdir)
            source_path = os.path.join(source_path, PhotoPlace_Cfg_file)
            dgettext['fromfile'] = source_path.encode(PLATFORMENCODING)
            dgettext['tofile'] = self.configfile.encode(PLATFORMENCODING)
            try:
                shutil.copyfile(source_path, self.configfile)
            except Exception as exception:
                dgettext['error'] = str(exception)
                msg = _("Cannot overwrite '%(tofile)s': %(error)s.\n")
                sys.stderr.write(msg % dgettext)
            else:
                msg = _("Configuration recovered to '%(tofile)s'.\n")
                sys.stderr.write(msg % dgettext)
                # Try again
                self._load_config(self.configfile, defaultconfig)
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
        if self.logfile != None:
            if not isinstance(self.logfile, unicode):
                try:
                    self.logfile = unicode(self.logfile, PLATFORMENCODING)
                except:
                    pass
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
                msg = _("Cannot set up logfile: %s.") % str(e)
                self.logger.error(msg)
        self.logger.setLevel(PhotoPlace_Cfg_loglevel)
        self.pluginmanager = Plugins.pluginManager.PluginManager()
        self.logger.debug("# " + PhotoPlace_name)
        self.logger.debug(
            "# Launched with command line args %s, files: %s" %
            (self.args, self.argfiles))
        self.logger.debug(_("# with configuration file '%s'.") % \
            self.configfile.encode(PLATFORMENCODING))
        self.logger.debug(_("# main options: %s") % self.options['main'])


    def _load_config(self, configfile, defaultconfig):
        if configfile != None:
            dgettext = dict()
            dgettext['configfile'] = configfile.encode(PLATFORMENCODING)
            if not os.path.exists(configfile):
                msg = _("Cannot find config file '%(configfile)s'.\n")
                sys.stderr.write(msg % dgettext)
            else:
                configuration = ConfigParser.ConfigParser()
                try:
                    # Try to read the configuration file
                    configuration.read(configfile)
                except:
                    msg = _("Cannot understand the format of config file '%(configfile)s'.\n")
                    sys.stderr.write(msg % dgettext)
                else:
                    try:
                        self.options = self.load_config(defaultconfig)
                    except NameError as nameerror:
                        dgettext['section'] = str(nameerror)
                        msg = _("Configuration file '%(configfile)s' is incomplete: "
                            "cannot find section '[%(section)s]'. Ignoring it!\n")
                        sys.stderr.write(msg % dgettext)
                    except ValueError as valueerror:
                        dgettext['error'] = str(valueerror)
                        msg = _("Cannot parse the configuration file '%(configfile)s': %(error)s.\n")
                        sys.stderr.write(msg % dgettext)
                    if self.options['main'].has_key('version'):
                        try:
                            version = int(self.options['main']['version'])
                            if version >= PhotoPlace_Cfg_version:
                                return True
                        except:
                            pass
            return False
        else:
            # Make configuration file
            return False


    def load_config(self, defaults):
        try:
            configuration = ConfigParser.ConfigParser()
            configuration.read(self.configfile)
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
                for key, value in defaults[section].iteritems():
                    dictionary[key] = value
            for key, value in current[section].iteritems():
                if value:
                    dictionary[key] = value
                else:
                    value = dictionary.get(key, None)
                    dictionary[key] = value
            rconfig[section] = dictionary
        for k, v in rconfig[VARIABLES_KEY].iteritems():
            if not isinstance(k, unicode):
                try:
                    k = unicode(k, PLATFORMENCODING)
                except:
                    pass
            if k in VARIABLES_OTHER:
                pass
            else:
                if k == 'author' and not v:
                    try:
                        v = unicode(getpass.getuser(), PLATFORMENCODING)
                        rconfig[VARIABLES_KEY][k] = v
                    except:
                        pass
                elif k == 'date' and not v:
                    v = datetime.date.today().strftime(PhotoPlace_Cfg_timeformat)
                    v = unicode(v, PLATFORMENCODING)
                    rconfig[VARIABLES_KEY][k] = v
        return rconfig


    def _get_cfgvalue(self, value):
        if isinstance(value, list):
            pos = 0
            limit_pos = len(value) - 1
            new_current_value = ''
            while pos <= limit_pos: 
                new_current_value += str(value[pos])
                if pos != limit_pos:
                    new_current_value += '; '
                pos = pos + 1
            current_value = new_current_value
        elif isinstance(value, tuple):
            pos = 0
            value_list = list(value)
            limit_pos = len(value_list) - 1
            new_current_value = ''
            while pos <= limit_pos: 
                new_current_value += str(value_list[pos])
                if pos != limit_pos:
                    new_current_value += ','
                pos = pos + 1
            current_value = new_current_value
        else:
            current_value = str(value)
            if current_value == 'None':
                current_value = ''
            elif current_value == 'True':
                current_value = '1'
            elif current_value == 'False':
                current_value = '0'
        return current_value


    def save_config(self, nosections=PhotoPlace_CONFIG_NOCLONE):
        if self.configfile != None:
            dgettext = dict()
            dgettext['file'] = self.configfile.encode(PLATFORMENCODING)
            path = os.path.dirname(self.configfile)
            dgettext['path'] = path.encode(PLATFORMENCODING)
            old_configfile = self.configfile + PhotoPlace_Cfg_fileextold
            try:
                shutil.copyfile(self.configfile, old_configfile)
            except Exception as exception:
                dgettext['error'] = str(exception)
                dgettext['file'] = old_configfile.encode(PLATFORMENCODING)
                msg = _("Cannot create backup of configfile to '%(file)s': %(error)s.")
                msg = msg % dgettext
                self.logger.error(msg)
                tip = _("Check if path '%(path)s' exists or is writable.") % dgettext
                raise Error(msg, tip, exception.__class__.__name__)
            else:
                fd_old = codecs.open(old_configfile, "r", encoding="utf-8")
                try:
                    fd_new = codecs.open(self.configfile, "w", encoding="utf-8")
                except Exception as exception:
                    dgettext['error'] = str(exception)
                    msg = _("Cannot write values in configfile '%(file)s': %(error)s.")
                    msg = msg % dgettext
                    self.logger.error(msg)
                    tip = _("Check if path/file exists or is writable.")
                    raise Error(msg, tip, exception.__class__.__name__)
                section = ''
                section_keys = []
                for line in fd_old:
                    line = line.lstrip()
                    if line.isspace() or len(line) == 0:
                        continue
                    if line.startswith('#'):
                        fd_new.write(line)
                        continue
                    search = re.search(r'\[(\w+)\]\s*', line)
                    if search:
                        # write rest of values of previous section
                        if section and not section in nosections:
                            for item in self.options[section]:
                                if item not in section_keys:
                                    current_value = self.options[section][item]
                                    current_value = self._get_cfgvalue(current_value)
                                    fd_new.write("%s = %s\n" % (item, current_value))
                        fd_new.write("\n")
                        section_keys = []
                        section = search.group(1)
                        fd_new.write(line)
                        continue
                    if section in nosections and len(nosections[section]) == 0:
                        fd_new.write(line)
                        continue
                    search = re.search(r';*\s*([\.\w]+)\s*=\s*([\.\\\/\-\w\$,#@]*)\s*', line)
                    if search:
                        # Maybe a default value
                        item_orig = search.group(1)
                        item = item_orig.lower()
                        old_value = search.group(2)
                        if section in nosections and item in nosections[section]:
                            fd_new.write(line)
                        else:
                            if section == 'main':
                                try:
                                    current_value = self.state[item]
                                except:
                                    current_value = old_value
                            else:
                                try:
                                    current_value = self.options[section][item]
                                except:
                                    current_value = old_value
                            current_value = self._get_cfgvalue(current_value)
                            if line.startswith(';') and current_value == old_value:
                                fd_new.write(line)
                            else:
                                fd_new.write("%s = %s\n" % (item_orig, current_value))
                        section_keys.append(item)
            msg = _("Configuration saved to '%(file)s'.") % dgettext
            self.logger.info(msg)
        else:
            self.logger.debug(_("No configuration file loaded. Nothing to do!"))


    def recover_config(self, directory=PhotoPlace_Cfg_altdir):
        dgettext = dict()
        if self.configfile != None:
            path = os.path.dirname(self.configfile)
            old_configfile = self.configfile + PhotoPlace_Cfg_fileextold
            try:
                shutil.copyfile(self.configfile, old_configfile)
            except Exception as exception:
                dgettext['error'] = str(exception)
                dgettext['file'] = old_configfile.encode(PLATFORMENCODING)
                dgettext['path'] = path.encode(PLATFORMENCODING)
                msg = _("Cannot create backup of configfile '%(file)s': %(error)s.")
                msg = msg % dgettext
                mtype = _("OOps ...")
                tip = _("Check if '%(path)s' exists or is writable.") % dgettext
                self.logger.error(msg)
                raise Error(msg, tip, exception.__class__.__name__)
        source_path = os.path.join(self.state.resourcedir, directory)
        source_path = os.path.join(source_path, PhotoPlace_Cfg_file)
        dest_path = os.path.join(self.state.resourcedir_user, PhotoPlace_Cfg_file)
        dgettext['fromfile'] = source_path.encode(PLATFORMENCODING)
        dgettext['tofile'] = dest_path.encode(PLATFORMENCODING)
        try:
            shutil.copyfile(source_path, dest_path)
        except Exception as exception:
            dgettext['error'] = str(exception)
            msg = _("Cannot copy '%(fromfile)s' to '%(tofile)s': %(error)s.")
            msg = msg % dgettext
            mtype = _("OOps ...")
            tip = _("Check if paths exist or are writable.")
            self.logger.error(msg)
            raise Error(msg, tip, exception.__class__.__name__)
        msg = _("Configuration recovered from '%(fromfile)s' to '%(tofile)s'.")
        msg = msg % dgettext
        self.logger.info(msg)


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
                tip = _("Check if plugin syntax is correct ... ")
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
                tip = _("Check Plugin base class ... ")
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
            if plugin != None:
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
                tip = _("Check if that dir exists or is writable.")
                raise Error(msg, tip, e.__class__.__name__)
        if wait:
            self.MakeKML().run()
            self.WriteCopySave().run()
        else:
            self.MakeKML().start()
            self.WriteCopySave().start()


# EOF
