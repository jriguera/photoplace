#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   photoplace.py
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
It is a multiplatform program (tested on Linux and Windows platforms) 
developed with python 2.x (>= 2.6) to easily geotag your photos. 

Also, with a track log from a GPS device, it can generate a *Google Earth*
/*Maps* layer with your photos. Moreover, the program can be easily adapted 
by editing templates and its functionality can be complemented with plugins, 
for example there is a plugin to generate a music tour that can be used 
to present your photo collection. 
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"

import os
import shutil
import sys
import imp
import optparse
import ConfigParser
import gettext
import locale

# do imports
try:
    import Image
except ImportError:
    print("Sorry, you don't have the Image (PIL) module installed, and this")
    print("program relies on it. Please install Image (PIL) module to continue.")
    sys.exit(1)
try:
    import pyexiv2
    version_pyexiv2 = pyexiv2.__version__
except:
    print("Sorry, you don't have the pyexiv2 >= 0.2 module installed, and this")
    print("program relies on it. Please install pyexiv2 >= 0.2v module and ")
    print("Exiv2 library.")
    sys.exit(1)


__PROGRAM__ = 'photoplace'
__PROGRAM_PATH__ = None
__GETTEXT_DOMAIN__ = __PROGRAM__
__RESOURCES_PATH__ = 'share'
__LOCALE_PATH__ = 'locale'
__LIB_PATH__ = 'lib'
__RESOURCES_CONF_PATH__ = 'conf'

__SHARE_DIR__ = os.path.join('share', 'photoplace')


# hasattr(sys, "frozen") -> new py2exe
# hasattr(sys, "importers") -> old py2exe
# imp.is_frozen("__main__") -> tools/freeze
if hasattr(sys, "frozen") or \
    hasattr(sys, "importers") or \
    imp.is_frozen("__main__"):
    __PROGRAM_PATH__ = os.path.dirname(sys.executable)
else:
    __PROGRAM_PATH__ = os.path.dirname(sys.argv[0])

lib_path = os.path.join(__PROGRAM_PATH__, __LIB_PATH__)
if os.path.isdir(lib_path):
    __LIB_PATH__ = lib_path
    sys.path.append(__LIB_PATH__)
else:
    __LIB_PATH__ = None

resources_path = os.path.join(__PROGRAM_PATH__, __RESOURCES_PATH__)
if not os.path.isdir(resources_path):
    # installed
    __RESOURCES_PATH__ = os.path.realpath(
        os.path.join('..', __RESOURCES_PATH__, __PROGRAM__))
else:
    __RESOURCES_PATH__ = resources_path

# Gettext
locale_path = os.path.join(__PROGRAM_PATH__, __LOCALE_PATH__)
if not os.path.isdir(locale_path):
    # installed
    locale_path = os.path.realpath(
        os.path.join('..', __SHARE_DIR__, __LOCALE_PATH__))
    if not os.path.isdir(locale_path):
        __LOCALE_PATH__ = None
    else:
        __LOCALE_PATH__ = locale_path
else:
    __LOCALE_PATH__ = locale_path
try:
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
except Exception as e:
    _ = lambda s: s
    print("Error setting up the translations: %s" % (e))



from PhotoPlace.definitions import *
import PhotoPlace.userFacade as userFacade


def program(args=sys.argv):
    configfile = None
    dgettext = dict()
    dgettext['defaultconfigfile'] = PhotoPlace_Cfg_file
    dgettext['defaultconfigdir'] = PhotoPlace_Cfg_dir
    dgettext['program'] = PhotoPlace_name
    dgettext['version'] = PhotoPlace_version
    dgettext['url'] = PhotoPlace_url
    dgettext['date'] = PhotoPlace_date
    options_usage = _("usage: %prog [options] <photodir> <file.gpx> "
        "[<output.kml>|<output.kmz>]")
    description = _("This is a python program to geolocate photos from a GPX "
        "data. Besides, it can generate a KMZ layer for Google Earth with "
        "all geolocated photos. By default, it tries to launch a graphical UI, "
        "if that is not possible, all options must be supplied by command line.")
    options_description = description
    options_version = "%prog " + PhotoPlace_version
    epilog1 = _("By default, the program searchs the configuration file "
        "'%(defaultconfigfile)s' in current directory, then in user home "
        "directory under '%(defaultconfigdir)s'.  ") % dgettext
    epilog2 = _("This program is able to create a virtual flux capacitor "
        "and, with the right settings, it can be used to time travels ... ")
    epilog3 = "%(program)s v%(version)s. %(url)s " % dgettext
    epilog4 = "(c) Jose Riguera, %(date)s <jriguera@gmail.com>" % dgettext
    options_epilog = epilog1 + epilog2 + epilog3 + epilog4
    options_parser = optparse.OptionParser(
        usage = options_usage,
        version = options_version,
        description = options_description,
        epilog = options_epilog)
    options_parser.add_option("-c", "--config-file",
        dest = "configfile", metavar="<configfile.cfg>",
        help = _("Read the configuration from <configfile.cfg>"))
    options_parser.add_option("-g", "--only-geolocate",
        action = "store_true", dest="onlygeolocate", default=False,
        help = _("Only do geolocating the photos of input directory, not "
            "generating any output file"))
    options_parser.add_option("-o", "--options",
        action="append", type="string", dest="options", metavar="SECTION:KEY=VALUE",
        help = _("Other options like they are defined in the config file. This "
            "argument can be supplied as many times as it was necessary for "
            "all options. The format is '-o \"section:key=value\"'"))
    options_parser.add_option("-b", "--batch",
        action = "store_true", dest="batch", default=False,
        help=_("Launch the batch mode, with command line args."))
    options_parser.add_option("--fluzo", help=optparse.SUPPRESS_HELP)
    (options, oargs) = options_parser.parse_args()
    if options.configfile :
        configfile = os.path.expandvars(os.path.expanduser(options.configfile))
    else:
        configfile = PhotoPlace_Cfg_file
        if not os.path.isfile(configfile):
            configfile = os.path.join(PhotoPlace_Cfg_dir, configfile)
        if not os.path.isfile(configfile):
            if not os.path.exists(PhotoPlace_Cfg_dir):
                try:
                    os.makedirs(PhotoPlace_Cfg_dir)
                except Exception as e:
                    sys.stderr.write(_("Cannot create files in '%s'.\n") % PhotoPlace_Cfg_dir)
            orig_cfg = os.path.join(__RESOURCES_PATH__, __RESOURCES_CONF_PATH__)
            try:
                shutil.copy(os.path.join(orig_cfg, PhotoPlace_Cfg_file), PhotoPlace_Cfg_dir)
            except Exception as e:
                sys.stderr.write(_("Cannot create default configfile in '%s'.\n") % PhotoPlace_Cfg_dir)
    if not os.path.isfile(configfile):
        sys.stderr.write(_("Cannot find configuration file '%s'.\n") % configfile)
        configfile = os.path.join(__RESOURCES_PATH__, __RESOURCES_CONF_PATH__, PhotoPlace_Cfg_file)
        if os.path.isfile(configfile):
            sys.stderr.write(_("Reading default config file '%s'.\n") % configfile)
        else:
            sys.stderr.write(_("Default config file '%s' not found.\n") % configfile)
            sys.stderr.write(_("Using internal settings ...\n"))
            configfile = None
    if configfile != None:
        configuration = ConfigParser.ConfigParser()
        try:
            # Try to read the configuration file
            configuration.read(configfile)
        except:
            msg = _("Cannot understand the format of config file '%s'. Ignoring it!.")
            sys.stderr.write(msg % configfile)
            configfile = None
        finally:
            configuration = None
    userfacade = userFacade.UserFacade(__RESOURCES_PATH__, configfile, args, options, oargs)
    if not options.batch:
        try:
            import PhotoPlace.UserInterface.GTKUI as GUI
            gui = GUI.PhotoPlaceGUI(__RESOURCES_PATH__)
            gui.init(userfacade)
            gui.loadPlugins()
            gui.start(True)
        except KeyboardInterrupt:
            userfacade.end()
        except Exception as e:
            msg = _("Error: Cannot launch GUI: %s.\nTrying batch mode ...\n")
            sys.stderr.write(msg  % str(e))
            options.batch = True
    if options.batch:
        try:
            import PhotoPlace.UserInterface.commandUI as COM
            command = COM.PhotoPlaceCOM(__RESOURCES_PATH__)
            command.init(userfacade)
            command.loadPlugins()
            command.start(True)
        except Exception as e:
            msg = _("Fatal error: Cannot launch program: %s.\n")
            sys.stderr.write(msg % str(e))
            sys.exit(1)
        finally:
            userfacade.end()


if __name__ == "__main__":
    # Main program
    program(sys.argv)
    sys.exit(0)


#EOF
