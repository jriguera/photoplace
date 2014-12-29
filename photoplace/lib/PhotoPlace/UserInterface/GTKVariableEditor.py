#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKPhotoInfo.py
#
#   Copyright 2010-2015 Jose Riguera Lopez <jriguera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
A GTK+ implementation for a user interface. Variable Editor
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import os.path
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

from PhotoPlace.definitions import *
from GTKUIdefinitions import *
from GTKTemplateEditor import *


# ###########################
# Window Editor for Variables
# ###########################

class VariableEditorGUI(gobject.GObject):
    """
    GTK Variable Editor Window
    """
    _instance = None

    __gsignals__ = {
        'load'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'save'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'close' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'remove': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VariableEditorGUI, cls).__new__(cls)
        return cls._instance


    def __init__(self, resourcedir=None, parentwindow=None):
        if resourcedir:
            gobject.GObject.__init__(self)
            guifile = os.path.join(resourcedir, GTKUI_RESOURCE_VariableEditorGUIXML)
            self.builder = gtk.Builder()
            self.builder.set_translation_domain(GTKUI_GETTEXT_DOMAIN)
            self.builder.add_from_file(guifile)
            self.window = self.builder.get_object("window")
            self.window.set_transient_for(parentwindow)
            self.window.set_destroy_with_parent(True)
            self["treeviewcolumn-variables-name"].set_title(_("Name"))
            self["treeviewcolumn-variables-value"].set_title(_("Value"))
            #self.variables = gtk.TreeStore(str, str, bool)
            #self["treeview-variables"].set_model(self.variables)
            self["treeview-variables"].set_rules_hint(True)
            self.ready = False


    def __getitem__(self, key):
        return self.builder.get_object(key)


    def __setitem__(self, key, value):
        raise ValueError("Cannot set key!")


    def init(self, userfacade):
        self.variables_iterator = None
        self.userfacade = userfacade
        self.variables = self["treeview-variables"].get_model()
        self.signals = {
            "on_window_delete_event": self.close,
            "on_toolbutton-exit_clicked": self.close,
            "on_button-variables-add_clicked": self._add_variable,
            "on_button-variables-del_clicked": self._del_variable,
            "on_cellrenderertext-variables-value_edited": self._edit_cell_variable,
        }
        self.builder.connect_signals(self.signals)
        self._signals = {
            'load'  : [],
            'save'  : [],
            'close' : [],
            'remove': [],
        }
        self.ready = True


    def connect(self, name, *args):
        if self.ready:
            retval = None
            if name.startswith('_'):
                retval = gobject.GObject.connect(self, name, *args)
            else:
                retval = gobject.GObject.connect(self, name, *args)
                self._signals[name].append(retval)
                return retval


    def disconnect(self, identifier=None):
        if self.ready:
            if identifier:
                for signal in self._signals:
                    if identifier in self._signals[signal]:
                        self._signals[signal].remove(identifier)
                gobject.GObject.disconnect(self, identifier)
            else:
                for signal in self._signals:
                    for i in self._signals[signal]:
                        gobject.GObject.disconnect(self, i)
                        self._signals[signal].remove(i)
                    self._signals[signal] = list()


    def show(self):
        if not self.ready:
            return False
        self.load()
        self.window.show_all()
        return True


    def load(self):
        self.variables.clear()
        self.variables_iterator = self.variables.append(None, [_("Main Parameters"), None, False])
        iterator_other = self.variables.append(None, [_("Other Parameters"), None, False])
        for k, v in self.userfacade.options[VARIABLES_KEY].iteritems():
            if not isinstance(k, unicode):
                try:
                    k = unicode(k, PLATFORMENCODING)
                except:
                    pass
            if k in VARIABLES_OTHER:
                self.variables.append(iterator_other, [k, v, True])
            else:
                self.variables.append(self.variables_iterator, [k, v, True])
        self["treeview-variables"].expand_to_path((0))
        self.emit('load')
        return True


    def _add_variable(self, widget, key=None, value='_'):
        if key != None:
            lkey = key
        else:
            lkey = self['entry-variables-add'].get_text().strip()
            if not isinstance(lkey, unicode):
                try:
                    lkey = unicode(lkey, 'UTF-8')
                except:
                    pass
        if lkey and not self.userfacade.options[VARIABLES_KEY].has_key(lkey):
            iterator = self.variables.append(self.variables_iterator, [lkey, value, True])
            self.userfacade.options[VARIABLES_KEY][lkey] = unicode(value, 'UTF-8')
            self['entry-variables-add'].set_text('')
            path = self.variables.get_path(iterator)
            self["treeview-variables"].scroll_to_cell(path)
            treeselection = self["treeview-variables"].get_selection()
            treeselection.select_path(path)
            self.emit('save', lkey, self.userfacade.options[VARIABLES_KEY][lkey])


    def _del_variable(self, widget):
        selection = self["treeview-variables"].get_selection()
        model, ite = selection.get_selected()
        if ite != None and self.variables.get_value(ite, VARIABLES_COLUMN_EDITABLE):
            key = self.variables.get_value(ite, VARIABLES_COLUMN_KEY)
            if not isinstance(key, unicode):
                try:
                    key = unicode(key, 'UTF-8')
                except:
                    pass
            self.variables.remove(ite)
            try:
                del self.userfacade.options[VARIABLES_KEY][key]
                self.emit('remove', key)
            except:
                pass


    def _edit_cell_variable(self, cell, path_string, new_text):
        treestore_iter = self.variables.get_iter_from_string(path_string)
        key = self.variables.get_value(treestore_iter, VARIABLES_COLUMN_KEY)
        if not isinstance(key, unicode):
            try:
                key = unicode(key, 'UTF-8')
            except:
                pass
        if not isinstance(new_text, unicode):
            try:
                new_text = unicode(new_text, 'UTF-8')
            except:
                pass
        if self.variables.get_value(treestore_iter, VARIABLES_COLUMN_EDITABLE):
            self.userfacade.options[VARIABLES_KEY][key] = new_text
            self.variables.set(treestore_iter, VARIABLES_COLUMN_VALUE, new_text)
            self.emit('save', key, new_text)


    def close(self, widget=None, data=None):
        self.window.hide()
        self.emit('close')
        self.disconnect()
        return True


# EOF
