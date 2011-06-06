#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKAddFiles.py
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
A plugin for PhotoPlace to add files to kmz. GTK User Interface.
"""
__program__ = "photoplace.addfiles"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.0"
__date__ = "May 2011"
__license__ = "GPL v3"
__copyright__ ="(c) Jose Riguera"


import os.path
import string
import sys
import codecs
import warnings

warnings.filterwarnings('ignore', module='gtk')
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gobject
except Exception as e:
    warnings.resetwarnings()
    print("Warning: %s" % str(e))
    print("You don't have the PyGTK 2.0 module installed")
    raise
warnings.resetwarnings()


from addfiles import *


# columns
(
    _GTKAddFiles_COLUMN_VAR,
    _GTKAddFiles_COLUMN_KEY,
    _GTKAddFiles_COLUMN_VALUE,
    _GTKAddFiles_COLUMN_INFO
) = range(4)

GTKAddFiles_COLUMN_TOOLTIP = _("Type %%(%s)s to get value of destination variable")



class GTKAddFiles(object):

    def __init__(self, gtkbuilder, state, logger):
        object.__init__(self)
        self.plugin = gtk.VBox(False)
        self.logger = logger
        self.options = None
        self.state = state
        # 1st line
        label_name = gtk.Label()
        align = gtk.Alignment(0.01, 0.5, 0, 0)
        label_name.set_markup(_("List of additional files to be included into KMZ"))
        align.add(label_name)
        self.plugin.pack_start(align, False, False, 10)
        # Parameters
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create model for parameters
        self.treestore = gtk.TreeStore(str, str, str, str)
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_tooltip_column(_GTKAddFiles_COLUMN_INFO)
        self.treeview.set_rules_hint(True)
        self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        # columns
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Variable"), renderer,
            text=_GTKAddFiles_COLUMN_VAR)
        column.set_resizable(True)
        column.set_min_width(170)
        self.treeview.append_column(column)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._edit_cell)
        column = gtk.TreeViewColumn(_("Value (Destination)"), renderer,
            text=_GTKAddFiles_COLUMN_KEY)
        renderer.set_property('editable', True)
        column.set_resizable(True)
        self.treeview.append_column(column)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Original File"), renderer,
            text=_GTKAddFiles_COLUMN_VALUE)
        column.set_resizable(True)
        self.treeview.append_column(column)
        scroll.add(self.treeview)
        self.plugin.pack_start(scroll, True, True)
        hbox = gtk.HBox(False)
        button_addfile = gtk.Button(_("Add File"), gtk.STOCK_ADD)
        button_addfile.connect('clicked', self._click_add)
        hbox.pack_start(button_addfile, False, False, 5)
        button_del = gtk.Button(_("Delete"), gtk.STOCK_REMOVE)
        button_del.connect('clicked', self._click_del)
        hbox.pack_end(button_del, False, False, 5)
        self.plugin.pack_start(hbox, False, False, 10)
        # Attributes
        self.options = None
        self.counter_file = 0
        self.newfiles = []
        self.window = gtkbuilder.get_object("window")


    def show(self, widget=None, options=None, newfiles=None):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options, newfiles)
        self.plugin.show_all()


    def hide(self, reset=False):
        self.plugin.hide_all()
        if reset:
            self.reset()


    def reset(self):
        ite = self.treestore.get_iter_first()
        deleted = []
        while ite:
            deleted.insert(0, ite)
            ite = self.treestore.iter_next(ite)
        for ite in deleted:
            self.treestore.remove(ite)
        self.counter_file = 0


    def setup(self, options, newfiles):
        self.treestore.clear()
        self.options = options
        for variable in newfiles:
            dest, orig = newfiles[variable]
            info = GTKAddFiles_COLUMN_TOOLTIP % variable
            self.treestore.append(None, [variable, dest, orig, info])
        self.counter_file = len(newfiles)
        self.newfiles = newfiles


    def _edit_cell(self, cell, path_string, new_text):
        ite = self.treestore.get_iter_from_string(path_string)
        safechars = "/\_-." + string.digits + string.ascii_letters
        destination = os.path.normpath(new_text.strip())
        destination = ''.join(c for c in destination if c in safechars)
        filekey = destination.replace('..','')
        if len(filekey) >= 3:
            self.treestore.set(ite, _GTKAddFiles_COLUMN_KEY, filekey)
            variable = self.treestore.get_value(ite, _GTKAddFiles_COLUMN_VAR)
            dest, orig = self.newfiles[variable]
            self.newfiles[variable] = (filekey, orig)
            self.options[AddFiles_VARIABLES][variable] = filekey


    def _click_add(self, widget):
        filename = None
        dialog = gtk.FileChooserDialog(title=_("Select a file ..."),
            parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        if dialog.run() == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename != None:
            self.counter_file += 1
            variable = AddFiles_PREFIX_NAME + AddFiles_PREFIX_FILE + str(self.counter_file)
            value = os.path.basename(filename)
            info = GTKAddFiles_COLUMN_TOOLTIP % variable
            self.treestore.append(None, [variable, value, filename, info])
            self.options[AddFiles_VARIABLES][variable] = value
            self.newfiles[variable] = (value, filename)


    def _click_del(self, widget):
        selection = self.treeview.get_selection()
        model, ite = selection.get_selected()
        if ite != None:
            variable = self.treestore.get_value(ite, _GTKAddFiles_COLUMN_VAR)
            del self.options[AddFiles_VARIABLES][variable]
            del self.newfiles[variable]
            model.remove(ite)


#EOF
