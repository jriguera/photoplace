#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       parameters.py
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
A plugin for PhotoPlace to show/add/modify parameters/variables defined into the
'[defaults]' section of the configuration file
"""
__program__ = "photoplace-parameters"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.1"
__date__ = "December 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import codecs
import getpass
import datetime
import gettext
import locale
import warnings
warnings.filterwarnings('ignore', module='gtk')
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except Exception as e:
    warnings.resetwarnings()
    print("Warning: %s" % str(e))
    print("You don't have the PyGTK 2.0 module installed")
    raise
warnings.resetwarnings()


from Plugins.Interface import *
from definitions import *

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


_Parameters_OPTIONS_KEY = "defaults"
_Parameters_OTHER = [
    'normalplacemark',
    'highlightplacemark',
    'highlightplacemarkballoonbgcolor',
    'highlightplacemarkballoontextcolor',
    'inilatitute',
    'inilongitude',
    'inialtitude',
    'inirange',
    'initilt',
    'iniheading',
]
# columns
(
    _Parameters_COLUMN_KEY,
    _Parameters_COLUMN_VALUE,
    _Parameters_COLUMN_EDITABLE,
) = range(3)


class Parameters(Plugin):

    description = _(
        "A plugin to edit variables/parameters of the "
        "configuration file."
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
        'NeedGUI' : True,
    }
    
    def __init__(self, logger, state, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, state, args, argfiles, gtkbuilder)
        self.options = dict()
        self.plugin = None
        # GTK widgets
        if gtkbuilder:
            self.plugin = gtk.VBox(False)
            label = gtk.Label()
            label.set_markup(_("List of parameters to make KML: "))
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_alignment(0.01, 0.5)
            label.set_line_wrap(True)
            self.plugin.pack_start(label, False, True)
            scroll = gtk.ScrolledWindow()
            scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self.plugin.pack_start(scroll)
            # create model
            self.treestore = gtk.TreeStore(str, str, bool)
            # create tree view
            self.treeview = gtk.TreeView(self.treestore)
            self.treeview.set_rules_hint(True)
            self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
            # columns
            renderer = gtk.CellRendererText()
            column = gtk.TreeViewColumn(_("Name"), renderer, text=_Parameters_COLUMN_KEY)
            column.set_resizable(True)
            column.set_sort_column_id(_Parameters_COLUMN_KEY)
            self.treeview.append_column(column)
            renderer = gtk.CellRendererText()
            renderer.connect('edited', self._edit_cell)
            column = gtk.TreeViewColumn(_("Value"), renderer, 
                text=_Parameters_COLUMN_VALUE, editable=_Parameters_COLUMN_EDITABLE)
            column.set_resizable(True)
            column.set_sort_column_id(_Parameters_COLUMN_VALUE)
            self.treeview.append_column(column)
            scroll.add(self.treeview)
            # some buttons
            hbox = gtk.HBox(False, 10)
            self.entry_key = gtk.Entry(256)
            self.entry_key.set_width_chars(20)
            self.entry_key.set_tooltip_text(
                _("Type the name of new parameter/variable"))
            hbox.pack_start(self.entry_key, False, False)
            button_add = gtk.Button(stock=gtk.STOCK_ADD)
            button_add.set_tooltip_text(_("Add the new parameter"))
            button_add.connect('clicked', self._add_variable)
            hbox.pack_start(button_add, False, False)
            button_del = gtk.Button(stock=gtk.STOCK_REMOVE)
            button_del.set_tooltip_text(
                _("Deletes the current selected parameter"))
            button_del.connect('clicked', self._del_variable)
            hbox.pack_end(button_del, False, False)
            self.plugin.pack_end(hbox, False, False, 5)


    def _add_variable(self, widget, key=None, value='_'):
        if key != None:
            lkey = key
        else:
            lkey = self.entry_key.get_text().strip()
        if lkey and not self.options.has_key(lkey):
            self.treestore.append(self.ite_main, [str(lkey), str(value), True])
            self.options[str(lkey)] = str(value)
            self.entry_key.set_text('')


    def _del_variable(self, widget):
        selection = self.treeview.get_selection()
        model, ite = selection.get_selected()
        if ite != None:
            editable = self.treestore.get_value(ite, _Parameters_COLUMN_EDITABLE)
            if editable:
                key = model.get_value(ite, _Parameters_COLUMN_KEY)
                model.remove(ite)
                try:
                    del self.options[key]
                except:
                    pass


    def _edit_cell(self, cell, path_string, new_text):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _Parameters_COLUMN_KEY)
        editable = self.treestore.get_value(treestore_iter, _Parameters_COLUMN_EDITABLE)
        if editable:
            self.options[key] = str(new_text)
            self.treestore.set(treestore_iter, _Parameters_COLUMN_VALUE, str(new_text))


    def show_variables(self, options, *args, **kwargs):
        self.treestore.clear()
        self.options = options[_Parameters_OPTIONS_KEY]
        self.ite_main = self.treestore.append(None, [str(_("Main Parameters")), None, False])
        self.ite_other = self.treestore.append(None, [str(_("Other Parameters")), None, False])
        for k, v in self.options.iteritems():
            if k in _Parameters_OTHER:
                self.treestore.append(self.ite_other, [str(k), str(v), True])
            else:
                if k == 'author' and not v:
                    v = getpass.getuser()
                    self.options[k] = v 
                elif k == 'date' and not v:
                    v = datetime.date.today().strftime("%A %d. %B %Y")
                    self.options[k] = v
                self.treestore.append(self.ite_main, [str(k), str(v), True])
        #self.treeview.expand_all()
        self.treeview.expand_to_path((0))


    def init(self, options, widget):
        if not self.options:
            # 1st time
            widget.add(self.plugin)
        self.show_variables(options)
        self.plugin.show_all()
        self.logger.debug(_("Starting plugin ..."))


    def end(self, options):
        self.ite_main = None
        self.ite_other = None
        if self.plugin:
            self.plugin.hide_all()
        self.logger.debug(_("Ending plugin ..."))


# EOF
