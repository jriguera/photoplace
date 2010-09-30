#! /usr/bin/env python
"""
"""
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.0"
__date__ = "March 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, March 2010"


import os
import sys
import imp
import optparse
import ConfigParser
import gettext
import locale



__GETTEXT_DOMAIN__ = 'photoplace'
__MODULES_PATH__ = 'modules'
__RESOURCES_PATH__ = 'share'
__LOCALE_PATH__ = 'locale'
__LIB_PATH__ = 'lib'
__GTK_CAPABLE__ = True
__PROGRAM_PATH__ = None
__RESOURCES_CONF_PATH__ = 'conf'
__RESOURCES_GTK_PATH__ = 'gtkui'
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
modules_path = os.path.join(__PROGRAM_PATH__, __MODULES_PATH__)
if not os.path.isdir(modules_path):
    # installed
    __MODULES_PATH__ = os.path.realpath(
        os.path.join('..', __SHARE_DIR__, __MODULES_PATH__))
else:
    __MODULES_PATH__ = modules_path
sys.path.append(__MODULES_PATH__)
lib_path = os.path.join(__PROGRAM_PATH__, __LIB_PATH__)
if not os.path.isdir(lib_path):
    # installed
    __LIB_PATH__ = os.path.realpath(
        os.path.join('..', __SHARE_DIR__, __LIB_PATH__))
else:
    __LIB_PATH__ = lib_path
sys.path.append(__LIB_PATH__)
if not os.path.isdir(__RESOURCES_PATH__):
    # installed
    __RESOURCES_PATH__ = os.path.realpath(
        os.path.join('..', __SHARE_DIR__, __RESOURCES_PATH__))
# Gettext
locale_path = os.path.join(__PROGRAM_PATH__, __LOCALE_PATH__)
if not os.path.isdir(locale_path):
    # installed
    __LOCALE_PATH__ = os.path.realpath(
        os.path.join('..', __SHARE_DIR__, __LOCALE_PATH__))
else:
    __LOCALE_PATH__ = locale_path
try:
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_PATH__)
except Exception as e:
    _ = lambda s: s
    print "Error setting up the translations: %s" % (e)


# do imports
try:
    import Image
except ImportError:
    print "Sorry, you don't have the Image (PIL) module installed, and this"
    print "program relies on it. Please install Image (PIL) module to continue."
    sys.exit(1)
try:
    import pyexiv2
    version_pyexiv2 = pyexiv2.__version__
except ImportError:
    print "Sorry, you don't have the pyexiv2 >= 0.2 module installed, and this"
    print "program relies on it. Please install pyexiv2 >= 0.2v module and "
    print "Exiv2 library."
    sys.exit(1)

if sys.platform.startswith("win"):
    # Fetchs gtk2 path from registry
    import _winreg
    import msvcrt
    try:
        k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\GTK\\2.0")
    except EnvironmentError:
        print "You must install the Gtk+ 2.2 Runtime Environment to run this program"
        while not msvcrt.kbhit():
            pass
        __GTK_CAPABLE__ = False
    else:
        gtkdir = _winreg.QueryValueEx(k, "Path")
        os.environ['PATH'] += ";%s/lib;%s/bin" % (gtkdir[0], gtkdir[0])
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gobject
except Exception as e:
    print "Warning: %s" % str(e)
    print "You don't have the PyGTK 2.0 module installed. "
    print "The GTK UI will not be launched."
    __GTK_CAPABLE__ = False


from definitions import *
import userFacade
from UserInterface.GTKUI import *



def program(args=sys.argv):
    configfile = None
    dgettext = dict()
    dgettext['defaultconfigfile'] = PhotoPlace_Cfg_file
    dgettext['defaultconfigdir'] = PhotoPlace_Cfg_dir
    dgettext['program'] = PhotoPlace_name
    dgettext['version'] = PhotoPlace_version
    dgettext['url'] = PhotoPlace_url
    dgettext['date'] = PhotoPlace_date
    options_usage = _("usage: %prog [options] <photo_dir> <input_file.gpx> "
        "[<output_file.kml> | <output_file.kmz>]")
    description = _("This is a python program to geolocate photos from a GPX "
        "data. Besides, it can generate a KMZ layer for Google Earth with "
        "all geolocated photos. By default, it tries to launch a graphical UI, "
        "if that is not possible, all options must be supplied by command line.")
    options_description = description
    options_version = "%prog " + PhotoPlace_version
    epilog1 = _("By default, the program searchs the configuration file "
        "'%(defaultconfigfile)s' in current directory, then in user home "
        "directory under '%(defaultconfigdir)s'.") % dgettext
    epilog2 = _("This program is able to create a virtual flux capacitor "
        "and, with the right settings, it can be used to time travels ...")
    epilog3 = "%(program)s v%(version)s. %(url)s" % dgettext
    epilog4 = "(c) Jose Riguera, %(date)s <jriguera@gmail.com>" % dgettext
    options_epilog = epilog1 + epilog2 + epilog3 + epilog4
    options_parser = optparse.OptionParser(
        usage = options_usage,
        version = options_version,
        description = options_description,
        epilog = options_epilog)
    options_parser.add_option("-c", "--config-file",
        dest = "configfile", metavar = "<configfile.cfg>",
        help = _("Read the configuration from <configfile.cfg>"))
    options_parser.add_option("-g", "--only-geolocate",
        action = "store_true", dest = "onlygeolocate", default = False,
        help = _("Only do geolocating the photos of input directory, not "
            "generating any output file."))
    options_parser.add_option("-o", "--options",
        action="append", type="string", dest="options", metavar="SECTION:KEY=VALUE",
        help = _("Other options like they are defined in the config file. This "
            "argument can be supplied as many times as it was necessary for "
            "all options. The format is '-o \"section:key=value\".'"))
    options_parser.add_option("-u", "--gui",
        action = "store_false", dest = "mode", default = True,
        help=_("Launch the Graphical User Interface, even if all necessary "
            "options are supplied."))
    options_parser.add_option("--fluzo", help=optparse.SUPPRESS_HELP)
    (options, oargs) = options_parser.parse_args()
    if options.configfile :
        configfile = os.path.expandvars(os.path.expanduser(options.configfile))
    else:
        configfile = PhotoPlace_Cfg_file
        if not os.path.isfile(configfile):
            configfile = os.path.join(PhotoPlace_Cfg_dir, configfile)
    if not os.path.isfile(configfile):
        sys.stderr.write(_("Cannot find configuration file '%s'.\n") % configfile)
        configfile = os.path.join(
            __RESOURCES_PATH__, __RESOURCES_CONF_PATH__, PhotoPlace_Cfg_file)
        if os.path.isfile(configfile):
            sys.stderr.write(_("Reading default config file '%s'.\n") % configfile)
        else:
            sys.stderr.write(_("Default config file '%s' not found.\n") % configfile)
            sys.stderr.write(_("Using internal settings ...\n"))
            configfile = None
    if configfile:
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
    if options.mode and __GTK_CAPABLE__:
        gtkui_path = os.path.join(__RESOURCES_PATH__, __RESOURCES_GTK_PATH__)
        try:
            gui = PhotoPlaceGUI(gtkui_path)
            gui.init(userfacade)
            gui.loadPlugins()
            gui.load()
            gui.loop()
        except KeyboardInterrupt:
            userfacade.end()
        except Exception as e:
            msg = _("[PhotoPlace] Fatal error! Cannot launch GUI: %s.\n")
            sys.stderr.write(msg  % str(e))
            sys.exit(1)
    else:
        try:
            raise
        except Exception as e:
            msg = _("[PhotoPlace] Fatal error! Cannot launch program: %s.\n")
            sys.stderr.write(msg  % str(e))
            sys.exit(1)


if __name__ == "__main__":
    # Main program
    program(sys.argv)
    sys.exit(0)


#EOF
