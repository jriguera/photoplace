#!/usr/bin/python
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
__date__ = "March 2011"
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
__RESOURCES_PATH__ = u'share'
__LOCALE_PATH__ = u'locale'
__LIB_PATH__ = u'lib'
__RESOURCES_CONF_PATH__ = u'conf'
__SHARE_DIR__ = os.path.join(u'share', u'photoplace')


# hasattr(sys, "frozen") -> new py2exe
# hasattr(sys, "importers") -> old py2exe
# imp.is_frozen("__main__") -> tools/freeze
if hasattr(sys, "frozen") or \
    hasattr(sys, "importers") or \
    imp.is_frozen("__main__"):
    __PROGRAM_PATH__ = os.path.dirname(unicode(sys.executable, locale.getpreferredencoding()))
else:
    __PROGRAM_PATH__ = os.path.dirname(unicode(os.path.realpath(__file__), locale.getpreferredencoding()))

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
        os.path.join(__PROGRAM_PATH__, u'..', __RESOURCES_PATH__, __PROGRAM__))
else:
    new_resources_path = os.path.join(resources_path, __PROGRAM__)
    if not os.path.isdir(new_resources_path):
        __RESOURCES_PATH__ = resources_path
    else:
        # windows install
        __RESOURCES_PATH__ = new_resources_path

# Gettext paths
locale_path = os.path.join(__PROGRAM_PATH__, __LOCALE_PATH__)
if not os.path.isdir(locale_path):
    # installed
    locale_path = os.path.realpath(
        os.path.join(u'..', __SHARE_DIR__, __LOCALE_PATH__))
    if not os.path.isdir(locale_path):
        __LOCALE_PATH__ = None
    else:
        __LOCALE_PATH__ = locale_path
else:
    __LOCALE_PATH__ = locale_path

# hack for I18N in windows. Idea and code was taken from: 
# https://launchpad.net/gettext-py-windows by Alexander Belchenko.
if sys.platform.startswith('win'):
    if not os.environ.get('LANGUAGE'):
        language = None
        try:
            import ctypes
        except ImportError:
            language = [locale.getdefaultlocale()[0]]
        else:
            # get all locales using windows API
            lcid_user = ctypes.windll.kernel32.GetUserDefaultLCID()
            lcid_system = ctypes.windll.kernel32.GetSystemDefaultLCID()
            if lcid_user != lcid_system:
                lcids = [lcid_user, lcid_system]
            else:
                lcids = [lcid_user]
            language = filter(None, [locale.windows_locale.get(i) for i in lcids]) or None
        # Set up environment variable
        os.environ['LANGUAGE'] = ':'.join(language)
try:
    locale.setlocale(locale.LC_ALL,'')
    #locale.bindtextdomain(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
    gettext.bindtextdomain(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
    gettext.textdomain(__GETTEXT_DOMAIN__)
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
    if sys.platform.startswith('win'):
        try: 
            import ctypes
            libintl = ctypes.cdll.LoadLibrary("intl.dll") 
            libintl.bindtextdomain(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
        except: 
            print("Error Loading translations into gtk.builder files")
except Exception as e:
    #locale.setlocale(locale.LC_ALL, 'C') 
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
    #_ = lambda s: s
    print("Error setting up the translations: %s" % (e))



from PhotoPlace.definitions import *
import PhotoPlace.userFacade as userFacade


def program(args=sys.argv):
    configfile = None
    dgettext = dict()
    dgettext['defaultconfigfile'] = PhotoPlace_Cfg_file.encode(PLATFORMENCODING)
    dgettext['defaultconfigdir'] = PhotoPlace_Cfg_dir.encode(PLATFORMENCODING)
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
    # Parse command line
    if options.configfile :
        configfile = os.path.expandvars(os.path.expanduser(options.configfile))
        try:
            configfile = unicode(configfile, PLATFORMENCODING)
        except:
            pass
    else:
        configfile = PhotoPlace_Cfg_file
        if not os.path.isfile(configfile):
            configfile = os.path.join(PhotoPlace_Cfg_dir, configfile)
    cfg_dir = os.path.dirname(os.path.realpath(configfile))
    if not os.path.exists(cfg_dir):
        try:
            os.makedirs(cfg_dir)
        except:
            cfg_dir = u'.'
    # redirect standard I/O to files
    if hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__"):
        sys.stdout = open(os.path.join(cfg_dir, u"stdout.log"), 'w+')
        sys.stderr = open(os.path.join(cfg_dir, u"stderr.log"), 'w+')
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
