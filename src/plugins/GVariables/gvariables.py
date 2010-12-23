#! /usr/bin/env python

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
__GETTEXT_DOMAIN__ = "photoplace-gvariables"
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


_GVariables_OPTIONS_KEY = "defaults"
_GVariables_MAIN = [
    'author', 
    'date', 
    'mailto', 
    'description', 
    'shortdescription', 
    'license',
    'photofolder', 
]
# columns
(
    _GVariables_COLUMN_KEY,
    _GVariables_COLUMN_VALUE,
    _GVariables_COLUMN_EDITABLE,
) = range(3)


class GVariables(Plugin):

    description = _("A plugin to edit variables of the configuration file.")
    version = "0.1.0"
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://code.google.com/p/photoplace/"
    copyright = "(c) Jose Riguera"
    date = "Oct 2010"
    license = "GPLv3"
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
            self.plugin = gtk.VBox(False, 5)
            label = gtk.Label()
            label.set_markup(_("List of global KML variables: "))
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
            renderer.set_data('column', _GVariables_COLUMN_KEY)
            column = gtk.TreeViewColumn(_("Name"), renderer, text=_GVariables_COLUMN_KEY)
            column.set_resizable(True)
            column.set_sort_column_id(_GVariables_COLUMN_KEY)
            self.treeview.append_column(column)
            renderer = gtk.CellRendererText()
            renderer.connect('edited', self._edit_cell)
            renderer.set_data('column', _GVariables_COLUMN_VALUE)
            column = gtk.TreeViewColumn(_("Value"), renderer, 
                text=_GVariables_COLUMN_VALUE, editable=_GVariables_COLUMN_EDITABLE)
            column.set_resizable(True)
            column.set_sort_column_id(_GVariables_COLUMN_VALUE)
            self.treeview.append_column(column)
            scroll.add(self.treeview)
            # some buttons
            hbox = gtk.HBox(False, 10)
            self.entry_key = gtk.Entry(256)
            self.entry_key.set_width_chars(20)
            hbox.pack_start(self.entry_key, False, False)
            self.button_add = gtk.Button(stock=gtk.STOCK_ADD)
            self.button_add.connect('clicked', self._add_variable)
            hbox.pack_start(self.button_add, False, False)
            self.button_del = gtk.Button(stock=gtk.STOCK_REMOVE)
            self.button_del.connect('clicked', self._del_variable)
            hbox.pack_end(self.button_del, False, False)
            self.plugin.pack_end(hbox, False, False)


    def _add_variable(self, widget, key=None, value='_'):
        if key:
            lkey = key
        else:
            lkey = self.entry_key.get_text()
        if lkey and not self.options.has_key(lkey):
            new_item = [str(lkey), str(value), True]
            self.treestore.append(None, new_item)
            self.options[str(lkey)] = str(value)
            self.entry_key.set_text('')


    def _del_variable(self, widget):
        selection = self.treeview.get_selection()
        model, model_iter = selection.get_selected()
        if model_iter:
            key = model.get_value(model_iter, _GVariables_COLUMN_KEY)
            model.remove(model_iter)
            try:
                del self.options[key]
            except:
                pass


    def _edit_cell(self, cell, path_string, new_text):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GVariables_COLUMN_KEY)
        editable = self.treestore.get_value(treestore_iter, _GVariables_COLUMN_EDITABLE)
        if editable:
            column = cell.get_data('column')
            self.options[key] = str(new_text)
            self.treestore.set(treestore_iter, column, str(new_text))


    def show_variables(self, options, *args, **kwargs):
        self.treestore.clear()
        self.options = options[_GVariables_OPTIONS_KEY]
        ite_main = self.treestore.append(None, [str(_("Main Variables")), None, False])
        ite_other = self.treestore.append(None, [str(_("Other Variables")), None, False])
        for k, v in self.options.iteritems():
            if k in _GVariables_MAIN :
                if k == 'author' and not v:
                    v = getpass.getuser()
                    self.options[k] = v 
                elif k == 'date' and not v:
                    v = datetime.date.today().strftime("%A %d. %B %Y")
                    self.options[k] = v
                self.treestore.append(ite_main, [str(k), str(v), True])
            else:
                self.treestore.append(ite_other, [str(k), str(v), True])
        #self.treeview.expand_all()
        self.treeview.expand_to_path((0))


    def init(self, options, widget):
        if not self.options:
            # 1st time
            widget.add(self.plugin)
        self.show_variables(options)
        self.plugin.show_all()


    def end(self, options):
        if self.plugin:
            self.plugin.hide_all()


# EOF
