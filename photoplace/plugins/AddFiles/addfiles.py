#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       addfiles.py
#
#       Copyright 2011 Jose Riguera Lopez <jriguera@gmail.com>
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
A plugin for PhotoPlace to add files to kmz
"""
__program__ = "photoplace.addfiles"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.0"
__date__ = "May 2011"
__license__ = "GPL v3"
__copyright__ ="(c) Jose Riguera"


import shutil
import os.path
import codecs
import string
import gettext
import locale


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.dirname(__file__)
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
except Exception as e:
    _ = lambda s: s
    print("Error setting up the translations: %s" % (e))


from PhotoPlace.Plugins.Interface import *
from PhotoPlace.definitions import *


# Configuration keys
AddFiles_CONFKEY = "addfiles"
AddFiles_VARIABLES = 'defaults'

# Default values
AddFiles_PREFIX_NAME = "Add"
AddFiles_PREFIX_FILE = "File."



class KmlPaths(Plugin):

    description = _(
        "A plugin to add files to kmz"
    )
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://code.google.com/p/photoplace/"
    version = __version__
    copyright = __copyright__
    date = __date__
    license = __license__
    capabilities = {
        'GUI' : PLUGIN_GUI_GTK,
        'NeedGUI' : False,
    }


    def __init__(self, logger, state, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, state, args, argfiles, gtkbuilder)
        self.options = dict()
        # GTK widgets
        self.gui = None
        if gtkbuilder:
            import GTKAddFiles
            self.gui = GTKAddFiles.GTKAddFiles(gtkbuilder, state, logger)
        self.ready = -1


    def init(self, options, widget):
        if not options.has_key(AddFiles_CONFKEY):
            options[AddFiles_CONFKEY] = dict()
        opt = options[AddFiles_CONFKEY]
        self.newfiles = None
        self.options = None
        self.process_variables(options, opt)
        if self.gui:
            if self.ready == -1:
                # 1st time
                self.gui.show(widget, self.options, self.newfiles)
            else:
                self.gui.show(None, self.options, self.newfiles)
        self.ready = 1
        self.logger.debug(_("Starting plugin ..."))


    def process_variables(self, options, opt):
        index = 0
        self.newfiles = dict()
        safechars = "/\_-." + string.digits + string.ascii_letters
        for key, value in opt.iteritems():
            filename = os.path.normpath(os.path.expandvars(os.path.expanduser(value)))
            destination = os.path.normpath(key)
            destination = ''.join(c for c in destination if c in safechars)
            filekey = destination.replace('..','')
            if os.path.isfile(filename) and len(filekey) >= 3:
                index += 1
                variable = AddFiles_PREFIX_NAME + AddFiles_PREFIX_FILE + str(index)
                self.newfiles[variable] = (filekey, filename)
                # add varible to state
                options[AddFiles_VARIABLES][variable] = filekey
        self.options = options


    @DRegister("SaveFiles:ini")
    def addfiles(self, fd, outputkml, outputkmz, photouri, outputdir, quality):
        if self.state.outputdir == None:
            return
        counter = 0
        outdir = os.path.dirname(outputkml)
        for variable in self.newfiles:
            dest, orig = self.newfiles[variable]
            try:
                output = os.path.join(outdir, dest)
                dirs = os.path.dirname(output)
                if not os.path.exists(dirs):
                    os.makedirs(dirs)
                shutil.copy(orig, output)
                counter += 1
            except Exception as e:
                dgettext = dict()
                dgettext['error'] = str(e)
                dgettext['file'] = orig
                msg = _("Cannot copy '%(file)s': %(error)s") % dgettext
                self.logger.error(msg)
        self.logger.info(_("%d files copied by 'addfiles'.") % counter)


    def end(self, options):
        self.ready = 0
        for variable in self.newfiles:
            del self.options[AddFiles_VARIABLES][variable]
        self.newfiles = None
        if self.gui:
            self.gui.hide(True)
        self.logger.debug(_("Ending plugin ..."))


# EOF
