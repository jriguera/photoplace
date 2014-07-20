#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKUI.py
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
A GTK+ implementation for a user interface.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2011"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2011"


import os
import sys
import time
import datetime
import codecs
import webbrowser
import StringIO
import xml.dom.minidom
import cgi
import warnings
from PIL import Image

warnings.filterwarnings('error', module='gtk')
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gobject
    gobject.set_prgname(__program__)
    gtk.gdk.threads_init()
    gobject.threads_init()
except Warning as w:
    warnings.resetwarnings()
    if str(w) == 'could not open display':
        raise AttributeError("Cannot open display, no X server found")
except Exception as e:
    warnings.resetwarnings()
    print("Warning: %s" % str(e))
    print("You don't have the PyGTK 2.0 module installed")
    raise
warnings.resetwarnings()


from PhotoPlace.definitions import *
from PhotoPlace.observerHandler import *
from PhotoPlace.stateHandler import *
from PhotoPlace.Facade import *
from PhotoPlace.userFacade import *
from PhotoPlace.Plugins.Interface import *
from Interface import InterfaceUI
from GTKUIdefinitions import *
from GTKPhotoInfo import *
from GTKTemplateEditor import *
from GTKVariableEditor import *



# #####################################################
# Cell text renderer (for treeviews) with click support
# #####################################################

class CellRendererTextClick(gtk.CellRendererText):

    __gproperties__ = {
        'clickable':
            (gobject.TYPE_BOOLEAN, 'clickable', 'is clickable?', False, gobject.PARAM_READWRITE)
    }

    def __init__(self):
        #gtk.CellRendererText.__init__(self)
        gobject.GObject.__init__(self)
        self.clickable = False

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_start_editing(self, event, treeview, path, background_area, cell_area, flags):
        if not self.clickable:
            return gtk.CellRendererText.do_start_editing(self,
                event, treeview, path, background_area, cell_area, flags)
        self.emit('edited', path, '')

gobject.type_register(CellRendererTextClick)



# ############################
# PhotoPlace GTKGUI Definition
# ############################

class PhotoPlaceGUI(InterfaceUI):
    """
    GTK GUI for PhotoPlace
    """
    _instance = None

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PhotoPlaceGUI, cls).__new__(cls)
        return cls._instance

    def __init__(self, resourcedir=None):
        if resourcedir:
            InterfaceUI.__init__(self, resourcedir)
            guifile = os.path.join(self.resourcedir, GTKUI_RESOURCE_GUIXML)
            self.builder = gtk.Builder()
            self.builder.set_translation_domain(GTKUI_GETTEXT_DOMAIN)
            self.builder.add_from_file(guifile)
            # Notebook and menuitem for plugins
            self.notebook = self.builder.get_object("notebook")
            self.notebook.set_group_id(20680)
            self.notebook_plugins = self.builder.get_object("notebook-plugins")
            self.toggletoolbutton_plugins = self.builder.get_object("toggletoolbutton-plugins")
            imagemenuitem_plugins = self.builder.get_object("imagemenuitem-plugins")
            self.menuitem_plugins = gtk.Menu()
            imagemenuitem_plugins.set_submenu(self.menuitem_plugins)
            self.progressbar = self.builder.get_object("progressbar-go")
            # textview log and observer defaults
            self.textview = self.builder.get_object("textview-output")
            self.textbuffer = self.textview.get_buffer()
            tag_debug = self.textbuffer.create_tag('debug')
            tag_debug.set_property("font", "Courier")
            tag_debug.set_property("size-points", 8)
            tag_info = self.textbuffer.create_tag('info')
            tag_info.set_property("font", "Courier")
            tag_info.set_property("foreground", "green")
            tag_info.set_property("size-points", 8)
            tag_info.set_property("weight", 700)
            tag_warning = self.textbuffer.create_tag('warning')
            tag_warning.set_property("font", "Courier")
            tag_warning.set_property("foreground", "orange")
            tag_warning.set_property("size-points", 8)
            tag_warning.set_property("weight", 800)
            tag_error = self.textbuffer.create_tag('error')
            tag_error.set_property("font", "Courier")
            tag_error.set_property("foreground", "red")
            tag_error.set_property("size-points", 8)
            tag_error.set_property("weight", 900)
            self.textview_formatter = \
                logging.Formatter(PhotoPlace_Cfg_logtextviewformat + '\n')
            self.statusbar = self.builder.get_object("statusbar")
            self.statusbar_formatter = logging.Formatter(' %(message)s')
            msg = PhotoPlace_name + " v" + PhotoPlace_version
            self.statusbar_context = self.statusbar.get_context_id(msg)
            self.statusbar.push(self.statusbar_context, msg)
            # make dialogs
            self.window = self.builder.get_object("window")
            # show window
            self["treeviewcolumn-geophotos-data"].set_title(_("Name"))
            self["treeviewcolumn-geophotos-value"].set_title(_("Value"))
            self["treeviewcolumn-geophotos-picture"].set_title(_("Picture"))
            self["treeviewcolumn-geophotos-info"].set_title(_("Information"))
            self["treeview-geophotos"].set_model(gtk.TreeStore(
                int, str, str, str, bool, gtk.gdk.Pixbuf, str, str, str, str, bool, bool, str))
            self["treeview-geophotos"].set_rules_hint(True)
            self.in_process = True
            self.windowteditor = TemplateEditorGUI(resourcedir, self.window)
            self.windowphotoinfo = PhotoInfoGUI(resourcedir, self.window)
            self.windowvariables = VariableEditorGUI(resourcedir, self.window)
            self.window.show_all()

    def __getitem__(self, key):
        return self.builder.get_object(key)

    def __setitem__(self, key, value):
        raise ValueError("Cannot set key!")

    def init(self, userfacade):
        gtk.gdk.threads_enter()
        self.userfacade = userfacade
        self.plugins = dict()
        # Observer for statusbar. INFO or ERROR loglevels
        self.userfacade.addlogObserver(self._log_to_statusbar_observer,
            [logging.INFO, logging.ERROR], self, self.statusbar_formatter)
        # Observer for textview
        self.userfacade.addlogObserver(self._log_to_textview_observer,
            [], self, self.textview_formatter)
        # Progress bar
        self.progressbar_fraction = 0.0
        self.progressbar_percent = 0.0
        self.userfacade.addNotifier(
            self._set_progressbar_makekml_observer, ["MakeKML:run"], self)
        self.userfacade.addNotifier(
            self._set_progressbar_writeexif_observer, ["WriteExif:run"], self)
        self.userfacade.addNotifier(
            self._set_progressbar_savefiles_observer, ["SaveFiles:run"], self)
        self.userfacade.addNotifier(
            self._update_progressbar_loadphoto_observer, ["LoadPhotos:run"], self)
        self.userfacade.addNotifier(
            self._update_progressbar_geolocate_observer, ["Geolocate:run"], self)
        self.userfacade.addNotifier(
            self._update_progressbar_makegpx_observer, ["MakeGPX:run"], self)
        self.userfacade.addNotifier(
            self._set_progressbar_end_observer,
            ["Geolocate:end", "MakeGPX:end", "SaveFiles:end",], self)
        self.userfacade.addNotifier(
            self._set_loadphotos_end_observer, ["LoadPhotos:end"], self)
        # Make a new state
        try:
            self.userfacade.init()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            self.userfacade.init(True)
        # adjustments
        self['adjustment-jpgzoom'].set_value(self.userfacade.state['jpgzoom'])
        self['adjustment-tdelta'].set_value(self.userfacade.state['maxdeltaseconds'])
        self['adjustment-toffset'].set_value(self.userfacade.state['timeoffsetseconds'])
        self['adjustment-quality'].set_value(self.userfacade.state['quality'])
        floatmin = minutes_to_timefloat(self.userfacade.state['utczoneminutes'])
        self['adjustment-utc'].set_value(floatmin)
        # toolbar buttons
        self.button_openphotos = self.builder.get_object("button-openphotos")
        self.button_opengpx = self.builder.get_object("button-opengpx")
        # other buttons
        self.togglebutton_outfile = self.builder.get_object("togglebutton-outfile")
        self.checkbutton_outgeo = self.builder.get_object("checkbutton-outgeo")
        self._choose_outfile(False)
        self.set_progressbar(None, 0.0)
        self.num_photos_process = 0
        self.reloadtemplates = False
        self.firstloadedphotos = False
        self.in_process = False
        self.windowteditor.init(self.userfacade)
        self.windowphotoinfo.init(self.userfacade, self["treeview-geophotos"].get_model())
        self.windowvariables.init(self.userfacade)

    def start(self, load_files=True):
        #gtk.gdk.threads_enter()
        if sys.platform.startswith('win'):
            sleeper = lambda: time.sleep(.001) or True
            gobject.timeout_add(400, sleeper)
        loaded_templates = self.action_loadtemplates()
        if load_files and loaded_templates:
            # Read current file
            selection = False
            if self.userfacade.state['gpxinputfile']:
                if self.action_readgpx():
                    label = os.path.basename(self.userfacade.state['gpxinputfile'])
                    self["button-opengpx"].set_label(label + "  ")
                    selection = True
            # Read current photodir
            if self.userfacade.state['photoinputdir']:
                if self.action_loadphotos():
                    label = os.path.basename(self.userfacade.state['photoinputdir'])
                    self["button-openphotos"].set_label(label + "  ")
                    selection = True
            self["checkbutton-outgeo"].set_active(True)
            self._toggle_geolocate_mode()
            if self.userfacade.state["outputfile"]:
                self["togglebutton-outfile"].set_active(True)
                self._choose_outfile()
            if not selection:
                dgettext = dict()
                dgettext['program'] = PhotoPlace_name
                dgettext['version'] = PhotoPlace_version
                msg = _("Welcome to %(program)s v %(version)s. If you like it, "
                    "please consider making a donation ;-) See 'About' menu for "
                    "more information") % dgettext
                gobject.idle_add(self.set_statusbar, msg)
        # Plugins
        for plugin in self.plugins:
            (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plugin]
            menuitem.connect('toggled', self._toggle_active_plugin, plugin)
            notebookframe.show_all()
            menuitem.show()
        # Templates
        imagemenuitem_templates = self.builder.get_object("imagemenuitem-templates")
        menuitem_templates = gtk.Menu()
        imagemenuitem_templates.set_submenu(menuitem_templates)
        for k, v in self.userfacade.options[TEMPLATES_KEY].iteritems():
            menuitem = gtk.MenuItem(os.path.basename(v))
            menuitem.connect('activate', self._clicked_template_edit, k, v)
            menuitem_templates.add(menuitem)
            menuitem.show()
        # GTK signals
        self.signals = {
            "on_aboutdialog_close": self.dialog_close,
            "on_aboutdialog_response": self.dialog_response,
            "on_aboutdialog_delete_event": self.dialog_close,
            "on_linkbutton-suggestion_clicked": self._open_link,
            "on_linkbutton-donate_clicked": self._open_link,
            "on_window_destroy": self.end,
            "on_notebook_create_window": self._create_notebookwindow,
            "on_imagemenuitem-opendir_activate": self._clicked_photodir,
            "on_imagemenuitem-opengpx_activate": self._clicked_gpx,
            "on_imagemenuitem-save_activate": self._clicked_outfile,
            "on_imagemenuitem-new_activate": self.action_clear,
            "on_imagemenuitem-saveconf_activate": self.action_saveconfig,
            "on_imagemenuitem-recoverconf_activate": self.action_recoverconfig,
            "on_imagemenuitem-exit_activate": self.end,
            "on_imagemenuitem-about_activate": self.dialog_show,
            "on_imagemenuitem-onlinehelp_activate": self._click_onlinehelp,
            "on_imagemenuitem-editvariables_activate": self.show_editvariables,
            "on_button-openphotos_clicked": self._clicked_photodir,
            "on_button-opengpx_clicked": self._clicked_gpx,
            "on_toggletoolbutton-plugins_toggled": self._toggle_loadplugins,
            "on_toolbutton-exit_clicked": self.end,
            "on_togglebutton-outfile_toggled": self._toggle_outfile,
            "on_checkbutton-outgeo_toggled": self._toggle_geolocate_mode,
            "on_combobox-exif_changed": self._toggle_exifmode,
            "on_adjustment-utc_value_changed": self._adjust_utctimezone,
            "on_adjustment-tdelta_value_changed": self._adjust_timedelta,
            "on_adjustment-toffset_value_changed": self._adjust_toffset,
            "on_adjustment-quality_value_changed": self._adjust_quality,
            "on_adjustment-jpgzoom_value_changed": self._adjust_jpgzoom,
            "on_button-go_clicked": self.action_process,
            "on_button-geolocate_clicked": self._clicked_geolocate,
            "on_cellgeophotos_toggled": self._toggle_geophoto,
            "on_treeview-geophotos_row_activated": self._clicked_geophoto,
            "on_treeview-geophotos_button_press_event": self._lclicked_geophoto,
            "on_cellrenderertext-geophotos-value_edited": self._edit_cell_geophoto,
        }
        self.builder.connect_signals(self.signals)
        self.windowteditor.connect('_save', self._reload_templates_cb)
        self.windowphotoinfo.connect('_save', self._set_geophoto_variables_cb)
        self.windowphotoinfo.connect('_reload', self._update_geophoto_cb)
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True
        gtk.main()
        gtk.gdk.threads_leave()

    def end(self, widget, data=None):
        for plg in self.plugins:
            (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
            if menuitem.get_active():
                menuitem.set_active(False)
        try:
            #super(InterfaceUI, self).end()
            InterfaceUI.end(self)
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
        gtk.main_quit()

    def dialog_show(self, dialog, data=None):
        dialog.hide_on_delete()
        dialog.show_all()
        return True

    def dialog_close(self, dialog, event=None):
        dialog.hide()
        return True

    def dialog_response(self, dialog, response, *args):
        # http://faq.pygtk.org/index.py?file=faq10.013.htp&req=show
        # system-defined GtkDialog responses are always negative,
        # in which case we want to hide it
        if response < 0:
            dialog.hide()
            dialog.emit_stop_by_name('response')

    def _open_link(self, widget, data=None):
        # hack for windows platform.
        # GTK in windows cannot open links ...
        if sys.platform.startswith('win'):
            uri = widget.get_uri()
            os.startfile(uri)

    def _click_onlinehelp(self, widget=None, data=None):
        webbrowser.open(PhotoPlace_onlinehelp)

    def _create_notebookwindow(self, notebook, page, drop_x, drop_y):
        pages = notebook.get_n_pages()
        if pages != 1:
            new_window = gtk.Window()
            title = notebook.get_tab_label_text(page)
            label = notebook.get_tab_label(page)
            new_window.set_title(PhotoPlace_name + ' [' + title + ']')
            new_window.set_transient_for(self.window)
            page_num = notebook.page_num(page)
            notebook.remove_page(page_num)
            #page.reparent(window)
            new_window.add(page)
            #new_window.connect("delete-event", self._destroy_notebookwindow, page, label)
            new_window.show_all()


    # #################
    # Plugin Management
    # #################

    def loadPlugins(self):
        errors = self.userfacade.load_plugins()
        for p, e in errors.iteritems():
            self.show_dialog(e.type, e.msg, e.tip)
        activation_errors = dict()
        for p in self.userfacade.addons:
            if not p in errors:
                try:
                    error = self.userfacade.activate_plugin(p, self)
                except Error as e:
                    activation_errors[p] = e
                    self.show_dialog(e.type, e.msg, e.tip)
                else:
                    if error != None:
                        activation_errors[p] = error
                        self.show_dialog(error.type, error.msg, error.tip)
            else:
                activation_errors[p] = errors[p]
        # generate menu a menu entry for each plugin
        self.toggling_active_plugin = False
        dgettext = dict()
        for plg, plgobj in self.userfacade.list_plugins().iteritems():
            if plg in self.plugins or plg in activation_errors:
                continue
            notebookindex = -1
            notebookframe = None
            menuitem = gtk.CheckMenuItem(str(plg))
            self.menuitem_plugins.add(menuitem)
            dgettext['plugin_name'] = plg
            dgettext['plugin_version'] = plgobj.version
            dgettext['plugin_author'] = cgi.escape(plgobj.author)
            dgettext['plugin_mail'] = cgi.escape(plgobj.email)
            dgettext['plugin_cpr'] = cgi.escape(plgobj.copyright)
            dgettext['plugin_date'] = cgi.escape(plgobj.date)
            dgettext['plugin_lic'] = cgi.escape(plgobj.license)
            dgettext['plugin_url'] = cgi.escape(plgobj.url)
            dgettext['plugin_desc'] = cgi.escape(plgobj.description)
            markup = _("Add-on <b>%(plugin_name)s</b> version %(plugin_version)s\n"
                "by <b>%(plugin_author)s</b> %(plugin_mail)s\n"
                "%(plugin_cpr)s %(plugin_date)s, License: %(plugin_lic)s\n"
                "More info at: <b>%(plugin_url)s</b>\n\n<i>%(plugin_desc)s</i>")
            menuitem.set_tooltip_markup(markup % dgettext)
            if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                notebooklabel = gtk.Label()
                notebooklabel.set_markup("   <b>%s</b>  " % plg)
                labelop = gtk.Label()
                labelop.set_markup(_("<b>Options</b>"))
                labelop.set_padding(2, 8)
                notebookframe = gtk.Frame()
                notebookframe.set_label_widget(labelop)
                notebookindex = self.notebook_plugins.append_page(
                    notebookframe, notebooklabel)
            try:
                self.userfacade.init_plugin(plg, '*', notebookframe)
                menuitem.set_active(True)
            except Error as e:
                menuitem.set_active(False)
                self.show_dialog(e.type, e.msg, e.tip)
                if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                    notebookframe.set_sensitive(False)
            self.plugins[plg] = (plgobj, menuitem, notebookindex, notebookframe)

    def unloadPlugins(self):
        self["toggletoolbutton-plugins"].set_active(False)
        for plg in self.plugins.keys():
            (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
            if menuitem.get_active():
                menuitem.set_active(False)
            menuitem.destroy()
            if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                self.notebook_plugins.remove_page(notebookindex)
                notebookframe.destroy()
            del self.plugins[plg]
        self.plugins = dict()

    def _toggle_loadplugins(self, widget=None, data=None):
        mode = self["toggletoolbutton-plugins"].get_active()
        for plg in self.plugins:
            (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
            if menuitem.get_active() != mode:
                menuitem.set_active(mode)

    def _toggle_active_plugin(self, widget, plg):
        if self.toggling_active_plugin:
            return
        self.toggling_active_plugin = True
        (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
        if menuitem.get_active():
            try:
                self.userfacade.init_plugin(plg, '*', notebookframe)
                if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                    notebookframe.set_sensitive(True)
            except Error as e:
                menuitem.set_active(False)
                self.show_dialog(e.type, e.msg, e.tip)
        else:
            try:
                self.userfacade.end_plugin(plg)
                if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                    notebookframe.set_sensitive(False)
            except Error as e:
                menuitem.set_active(True)
                self.show_dialog(e.type, e.msg, e.tip)
        self.toggling_active_plugin = False


    # #####################################
    # StatusBar, Textview and log Observers
    # #####################################

    @DObserver
    def _log_to_statusbar_observer(self, formatter, record):
        msg = formatter.format(record)
        gobject.idle_add(self.set_statusbar, msg)

    def set_statusbar(self, msg):
        self.statusbar.pop(self.statusbar_context)
        self.statusbar.push(self.statusbar_context, msg)

    @DObserver
    def _log_to_textview_observer(self, formatter, record):
        msg = formatter.format(record)
        if not isinstance(msg, unicode):
            try:
                msg = unicode(msg, PLATFORMENCODING)
            except:
                pass
        level = "error"
        if record.levelno == logging.DEBUG:
            level = "debug"
        elif record.levelno == logging.WARNING:
            level = "warning"
        elif record.levelno == logging.INFO:
            level = "info"
        gobject.idle_add(self.set_output, msg, level)

    def set_output(self, msg, level="info"):
        iterator = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iterator)
        self.textbuffer.insert_with_tags_by_name(iterator, msg, level)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0.1)

    def pulse_progressbar(self, msg=''):
        self.progressbar.set_text(msg)
        self.progressbar.pulse()

    @DObserver
    def _update_progressbar_loadphoto_observer(self, geophoto, *args):
        msg = _("Loading photo '%s' ...") % geophoto.name
        gobject.idle_add(self.pulse_progressbar, msg)
        self._load_geophoto(geophoto)

    @DObserver
    def _update_progressbar_geolocate_observer(self, photo, *args):
        msg = _("Geotagging photo '%s' ...") % photo.name
        gobject.idle_add(self.pulse_progressbar, msg)

    @DObserver
    def _update_progressbar_makegpx_observer(self, photo, *args):
        msg = _("Processing photo '%s' ...") % photo.name
        gobject.idle_add(self.pulse_progressbar, msg)

    def set_progressbar(self, text=None, percent=-1.0):
        if percent < 0.0:
            self.progressbar_percent += self.progressbar_fraction
        else:
            self.progressbar_percent = percent
        if self.progressbar_percent > 1.0:
            self.progressbar_percent = 1.0
        if percent == 0.0:
            msg = _("Let's Go!")
            tip = _("Click me to start!")
        else:
            msg = "[" + str(int(self.progressbar_percent * 100)) + "%]"
            tip = _("I am working! Please, wait a moment ...")
            if text != None:
                msg = msg + "  " + text
        self.progressbar.set_text(msg)
        self.progressbar.set_tooltip_markup(tip)
        self.progressbar.set_fraction(self.progressbar_percent)

    @DObserver
    def _set_progressbar_makekml_observer(self, photo, *args):
        msg = _("Adding to KML info of '%s' ...") % photo.name
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_writeexif_observer(self, photo, *args):
        msg = _("Writing EXIF info of '%s' ...") % photo.name
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_savefiles_observer(self, filename, *args):
        msg = _("Saving file '%s' ...") % filename
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_end_observer(self, *args):
        gobject.idle_add(self.set_progressbar, None, 0.0)

    @DObserver
    def _set_loadphotos_end_observer(self, *args):
        gobject.idle_add(self.set_progressbar, None, 0.0)
        if not self.firstloadedphotos:
            # order by name (only first time)
            gobject.idle_add(self["treeviewcolumn-geophotos-picture"].clicked)
            # Set name to photo folder
            value = os.path.basename(self.userfacade.state['photoinputdir'])
            if not self.userfacade.options[VARIABLES_KEY].has_key('name'):
                self.userfacade.options[VARIABLES_KEY]['name'] = ''
            if len(self.userfacade.options[VARIABLES_KEY]['name']) < 1:
                self.userfacade.options[VARIABLES_KEY]['name'] = value
            self.firstloadedphotos = True


    # ##############################################
    # Show GTK Dialogs (Open, Select directory, ...)
    # ##############################################

    def show_dialog(self, title, msg, tip='', dtype=gtk.MESSAGE_ERROR):
        dialog = gtk.MessageDialog(self.window,
            gtk.DIALOG_DESTROY_WITH_PARENT, dtype, gtk.BUTTONS_CLOSE)
        #  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        window_title = PhotoPlace_name + " "
        if dtype == gtk.MESSAGE_INFO:
            window_title += _("Info")
        elif dtype == gtk.MESSAGE_WARNING:
            window_title += _("Warning")
        else:
            window_title += _("Error")
        dialog.set_title(window_title)
        dialog.set_markup("<big><b>" + title + "</b></big>\n\n" + cgi.escape(msg))
        dialog.format_secondary_markup("<i>" + cgi.escape(tip) + "</i>")
        dialog.run()
        dialog.destroy()

    def show_dialog_choose_photodir(self, select_dir=None,
        title=_("Select a directory with photos ...")):
        dir_open_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        if select_dir != None:
            dir_open_dlg.set_current_folder(select_dir)
        directory = None
        if dir_open_dlg.run() == gtk.RESPONSE_OK:
            directory = dir_open_dlg.get_filename()
        dir_open_dlg.destroy()
        if directory != None:
            return self.action_loadphotos(directory)

    def show_dialog_choose_gpx(self, select_file=None, title=_("Select input GPX file ...")):
        gpx_open_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("GPS eXchange Format GPX"))
        ffilter.add_mime_type("application/gpx+xml")
        ffilter.add_pattern("*.gpx")
        gpx_open_dlg.add_filter(ffilter)
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("All files"))
        ffilter.add_pattern("*")
        gpx_open_dlg.add_filter(ffilter)
        if select_file != None:
            gpx_open_dlg.set_filename(select_file)
        filename = None
        if gpx_open_dlg.run() == gtk.RESPONSE_OK:
            filename = gpx_open_dlg.get_filename()
        gpx_open_dlg.destroy()
        if filename != None:
            return self.action_readgpx(filename)

    def show_dialog_choose_outfile(self, select_file=None, title=_("Choose output file ...")):
        kmz_save_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("Keyhole Markup Language (Google Earth Layer) KMZ"))
        ffilter.add_mime_type("application/vnd.google-earth.kmz")
        ffilter.add_pattern("*.kmz")
        kmz_save_dlg.add_filter(ffilter)
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("Keyhole Markup Language (Google Earth Layer) KML"))
        ffilter.add_mime_type("application/vnd.google-earth.kml+xml")
        ffilter.add_pattern("*.kml")
        kmz_save_dlg.add_filter(ffilter)
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("All files"))
        ffilter.add_pattern("*")
        kmz_save_dlg.add_filter(ffilter)
        if select_file != None:
            kmz_save_dlg.set_current_name(select_file)
        filename = None
        if kmz_save_dlg.run() == gtk.RESPONSE_OK:
            filename = kmz_save_dlg.get_filename()
        kmz_save_dlg.destroy()
        if filename != None:
            try:
                self.userfacade.state['outputfile'] = unicode(filename, 'UTF-8')
                return True
            except Error as e:
                self.show_dialog(e.type, e.msg, e.tip)
        return False


    # #################################
    # Callbacks from notebook page Main
    # #################################

    def _clicked_photodir(self, widget=None, data=None):
        if self.show_dialog_choose_photodir(self.userfacade.state['photoinputdir']):
            label = os.path.basename(self.userfacade.state['photoinputdir']) + "  "
            self['button-openphotos'].set_label(label)
            try:
                self.userfacade.state.set_outputfile()
            except:
                pass
            else:
                if not self['togglebutton-outfile'].get_active():
                    self._choose_outfile()
                self._set_photouri()

    def _clicked_gpx(self, widget=None, data=None):
        if self.show_dialog_choose_gpx(self.userfacade.state['gpxinputfile']):
            label = os.path.basename(self.userfacade.state['gpxinputfile']) + "  "
            self['button-opengpx'].set_label(label)

    def _clicked_outfile(self, widget=None, data=None):
        self['togglebutton-outfile'].set_active(True)
        self._toggle_outfile()

    def _choose_outfile(self, mode=True):
        if mode:
            filename = self.userfacade.state['outputfile']
            if len(filename) > 34:
                filename = " ... " + os.path.basename(filename)
            self['togglebutton-outfile'].set_label(_("Generate: ") + filename)
            self['hscale-quality'].set_sensitive(True)
            self['hscale-zoom'].set_sensitive(True)
            self['entry-photouri'].set_sensitive(True)
            self._set_photouri()
        else:
            self['togglebutton-outfile'].set_label(_(" Do not generate output file!"))
            self['hscale-quality'].set_sensitive(False)
            self['hscale-zoom'].set_sensitive(False)
            self['entry-photouri'].set_text('')
            self['entry-photouri'].set_sensitive(False)

    def _toggle_outfile(self, widget=None, data=None):
        if self['togglebutton-outfile'].get_active():
            select_file = ''
            if self.userfacade.state['photoinputdir']:
                select_file = self.userfacade.state['photoinputdir'] + ".kmz"
            if self.show_dialog_choose_outfile(select_file):
                self._choose_outfile()
                return
        self['togglebutton-outfile'].set_active(False)
        self._choose_outfile(False)

    def _toggle_exifmode(self, widget=None, data=None):
        iter_mode = self['combobox-exif'].get_active_iter()
        if iter_mode != None:
            mode = self["combobox-exif"].get_model().get_value(iter_mode, 1)
            self.userfacade.state["exifmode"] = mode

    def _toggle_geolocate_mode(self, widget=None, data=None):
        if self['checkbutton-outgeo'].get_active():
            self['combobox-exif'].set_sensitive(True)
            position = 0
            default_pos = 0
            model = self["combobox-exif"].get_model()
            model.clear()
            for k, v in PhotoPlace_Cfg_ExifModes.iteritems():
                if k == -1:
                    continue
                model.append([v, k])
                if k == self.userfacade.state["exifmode"]:
                    default_pos = position
                position += 1
            self['checkbutton-outgeo'].set_label(_("Geotag photos in mode:"))
            self['combobox-exif'].set_active(default_pos)
        else:
            self['checkbutton-outgeo'].set_label(_("Do not geotag photos!"))
            self['combobox-exif'].set_sensitive(False)
            self.userfacade.state["exifmode"] = -1

    def _set_photouri(self, name=None):
        if name != None:
            photouri = name
            if not isinstance(name, unicode):
                try:
                    photouri = unicode(name, 'UTF-8')
                except:
                    pass
            self.userfacade.state['photouri'] = photouri
            self["entry-photouri"].set_text(photouri)
        else:
            photouri = self["entry-photouri"].get_text().strip()
            if not photouri:
                photouri = self.userfacade.state['photouri']
                self["entry-photouri"].set_text(photouri)
            else:
                photouri = unicode(photouri, 'UTF-8')
                self.userfacade.state['photouri'] = photouri
                photouri = self.userfacade.state['photouri']
                self["entry-photouri"].set_text(photouri)

    def _adjust_utctimezone(self, widget=None, data=None):
        value = self['adjustment-utc'].get_value()
        new_value = float_to_timefloat(value)
        if new_value != value:
            self['adjustment-utc'].set_value(new_value)
        self.userfacade.state['utczoneminutes'] = timefloat_to_minutes(new_value)

    def _adjust_timedelta(self, widget=None, data=None):
        value = self['adjustment-tdelta'].get_value()
        self.userfacade.state['maxdeltaseconds'] = int(value)

    def _adjust_toffset(self, widget=None, data=None):
        value = self['adjustment-toffset'].get_value()
        self.userfacade.state['timeoffsetseconds'] = int(value)
        self["treeview-geophotos"].get_model().clear()
        self.num_photos_process = 0
        for geophoto in self.userfacade.state.geophotos:
            offset = geophoto.toffset + self.userfacade.state['timeoffsetseconds']
            geophoto.time = geophoto.time + datetime.timedelta(seconds=offset)
            geophoto.toffset = -self.userfacade.state['timeoffsetseconds']
            self._load_geophoto(geophoto)
            if geophoto.status > 0:
                self.num_photos_process += 1

    def _adjust_quality(self, widget=None, data=None):
        value = self['adjustment-quality'].get_value()
        self.userfacade.state['quality'] = int(value)

    def _adjust_jpgzoom(self, widget=None, data=None):
        value = self['adjustment-jpgzoom'].get_value()
        self.userfacade.state['jpgzoom'] = value


    # ###################################
    # Callbacks from notebook page Photos
    # ###################################

    def _clicked_geolocate(self, widget=None):
        if self.userfacade.state['gpxinputfile']:
            self.action_geolocate()
        else:
            mtype = _("OOps ...")
            msg = _("Cannot geolocate!. No GPX data file loaded!")
            tip = _("Load a GPX file to do that.")
            self.show_dialog(mtype, msg, tip, gtk.MESSAGE_INFO)

    def _load_geophoto(self, geophoto, main_iterator=None):
        color = TREEVIEWPHOTO_NORMAL_COLOR
        previews = geophoto.exif.previews
        width, height = TREEVIEWPHOTO_PHOTOSIZE
        # Patch submitted by Noela's team
        if previews :
            loader = gtk.gdk.PixbufLoader('jpeg')
            loader.set_size(width, height)
            largest = previews[-1]
            loader.write(largest.data)
            loader.close()
            pixbuf = loader.get_pixbuf()
        else :
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(geophoto.path, width, height)
        dgettext = dict()
        dgettext['name'] = geophoto.name
        dgettext['path'] = geophoto.path
        dgettext['date'] = geophoto.time.strftime(PhotoPlace_Cfg_timeformat)
        dgettext['time'] = geophoto.time.strftime("%H:%M:%S")
        dgettext['lon'] = geophoto.lon
        dgettext['lat'] = geophoto.lat
        dgettext['ele'] = geophoto.ele
        tips = "%(path)s\n"
        try:
            dgettext['author'] = geophoto["Exif.Image.Artist"]
            tips = tips + _("# Author: %(author)s\n")
        except:
            dgettext['author'] = _("Unknown")
        try:
            dgettext['description'] = geophoto["Exif.Image.ImageDescription"]
            tips = tips + _("# Description:\n %(description)s\n")
        except:
            dgettext['description'] = ''
        information = _("<b>%(name)s</b>\nDate: %(date)s\nTime: %(time)s") % dgettext
        if geophoto.toffset != 0:
            information += " (%+ds)" % geophoto.toffset
        geodata = ''
        geovalue = _("Picture not geotagged!")
        if geophoto.isGeoLocated():
            geodata = _("  Longitude\n  Latitude\n  Elevation") % dgettext
            geovalue = "%(lon).8f\n%(lat).8f\n%(ele).3f" % dgettext
            color = TREEVIEWPHOTO_GEOLOCATED_COLOR
        tips = tips % dgettext
        if geophoto.status > 1:
            geophoto.status = 1
            color = TREEVIEWPHOTO_CHANGED_COLOR
        #if geophoto.attr:
        #    tips += _("# Attributes: \n")
        #    for k,v in geophoto.attr.iteritems():
        #        tips += "\t%s: %s\n" % (k, v)
        model = self["treeview-geophotos"].get_model()
        if main_iterator == None:
            iterator = model.append(None, [
                geophoto.status, geophoto.name, geophoto.path, geophoto.time, bool(geophoto.status),
                pixbuf, information, geodata, geovalue,
                color, True, False, tips]
            )
        else:
            model.set(main_iterator,
                TREEVIEWPHOTOS_COL_STATUS, geophoto.status,
                TREEVIEWPHOTOS_COL_NAME, geophoto.name,
                TREEVIEWPHOTOS_COL_DATE, geophoto.time,
                TREEVIEWPHOTOS_COL_ACTIVE, bool(geophoto.status),
                TREEVIEWPHOTOS_COL_MAIN_INFO, information,
                TREEVIEWPHOTOS_COL_DATA, geodata,
                TREEVIEWPHOTOS_COL_VALUE, geovalue,
                TREEVIEWPHOTOS_COL_BGCOLOR, color,
                TREEVIEWPHOTOS_COL_INFO, tips
             )
            iterator = main_iterator
        self.set_geophoto_variables(iterator, geophoto)
        self["treeview-geophotos"].expand_row(model.get_path(iterator), True)

    def set_geophoto_variables(self, iterator, geophoto):
        model = self["treeview-geophotos"].get_model()
        child_iter = model.iter_children(iterator)
        while child_iter != None:
            model.remove(child_iter)
            child_iter = model.iter_children(iterator)
        for variable in self.userfacade.state.photovariables:
            if not (variable in PhotoPlace_TEMPLATE_VARS):
                #( ... or variable in  self.userfacade.options['defaults']):
                try:
                    value = geophoto.attr[variable]
                except:
                    value = ''
                model.append(iterator, [
                    geophoto.status, variable, geophoto.path, None, bool(geophoto.status), None, None,
                    "<tt><b>%s</b></tt> " % variable, value, None, False, True, _("Template Variable")])

    def _set_geophoto_variables_cb(self, obj, iterator, geophoto, *args, **kwargs):
        self.set_geophoto_variables(iterator, geophoto)
        model = self["treeview-geophotos"].get_model()
        self["treeview-geophotos"].expand_row(model.get_path(iterator), True)

    def _update_geophoto_cb(self, obj, iterator, geophoto, *args, **kwargs):
        self._load_geophoto(geophoto, iterator)

    def _toggle_geophoto(self, cell, path, data=None):
        model = self["treeview-geophotos"].get_model()
        ite = model.get_iter(path)
        status = model.get_value(ite, TREEVIEWPHOTOS_COL_ACTIVE)
        path = model.get_value(ite, TREEVIEWPHOTOS_COL_PATH)
        status = not status
        for geophoto in self.userfacade.state.geophotos:
            if geophoto.path == path:
                geophoto.status = int(status)
                break
        model.set(ite, TREEVIEWPHOTOS_COL_ACTIVE, status)
        children = model.iter_n_children(ite)
        counter = 0
        while counter < children:
            child_iter = model.iter_nth_child(ite, counter)
            model.set(child_iter, TREEVIEWPHOTOS_COL_ACTIVE, status)
            counter += 1

    def _clicked_geophoto(self, treeview, path, column, data=None):
        model = treeview.get_model()
        ite = model.get_iter(path)
        iterator = model.iter_parent(ite)
        if iterator != None:
            ite = iterator
        name = model.get_value(ite, TREEVIEWPHOTOS_COL_NAME)
        geophoto_path = model.get_value(ite, TREEVIEWPHOTOS_COL_PATH)
        for geophoto in self.userfacade.state.geophotos:
            if geophoto.path == geophoto_path:
                self.windowphotoinfo.show(geophoto, ite)
                return True
        return False

    def _edit_cell_geophoto(self, cell, path_string, new_text):
        model = self["treeview-geophotos"].get_model()
        ite = model.get_iter_from_string(path_string)
        geophoto_path = model.get_value(ite, TREEVIEWPHOTOS_COL_PATH)
        variable = model.get_value(ite, TREEVIEWPHOTOS_COL_NAME)
        for geophoto in self.userfacade.state.geophotos:
            if geophoto.path == geophoto_path:
                geophoto.attr[variable] = str(new_text.strip())
                model.set(ite, TREEVIEWPHOTOS_COL_VALUE, new_text.strip())
                return

    def _lclicked_geophoto(self, widget, event):
        if event.button == 3:
            paths_ite = widget.get_path_at_pos(int(event.x), int(event.y))
            if paths_ite == None:
                # invalid path
                pass
            elif len(paths_ite) > 0:
                model = self["treeview-geophotos"].get_model()
                ite = model.get_iter(paths_ite[0])
                geophoto_path = model.get_value(ite, TREEVIEWPHOTOS_COL_PATH)
                active = True
                if geophoto_path in self.userfacade.state.geophotostyle:
                    style = self.userfacade.state.geophotostyle[geophoto_path]
                    try:
                        active = style[PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path] == None
                    except:
                        pass
                menu = gtk.Menu()
                menu_view = gtk.MenuItem(_("View EXIF and Variables"))
                menu_edit = gtk.MenuItem(_("Edit Template/Description"))
                menu_default = gtk.CheckMenuItem(_("Default Template"))
                menu_default.set_active(active)
                menu.append(menu_view)
                menu.append(menu_edit)
                menu.append(menu_default)
                menu.show_all()
                menu.popup(None, None, None, event.button, event.time)
                for geophoto in self.userfacade.state.geophotos:
                    if geophoto.path == geophoto_path:
                        menu_view.connect("activate", self._activate_viewgeophoto, geophoto, ite)
                        menu_default.connect("activate", self._activate_setdesc, geophoto)
                        menu_edit.connect("activate", self._activate_menuedit, geophoto, ite)
                        break

    def _activate_viewgeophoto(self, widget, geophoto, ite):
        self.windowphotoinfo.show(geophoto, ite)

    def _activate_setdesc(self, widget, geophoto):
        key = geophoto.path
        if key in self.userfacade.state.geophotostyle:
            self.userfacade.state.geophotostyle[key] = None
            del self.userfacade.state.geophotostyle[key]

    def _activate_menuedit(self, widget, geophoto, ite):
        key = geophoto.path
        text = None
        if key in self.userfacade.state.geophotostyle:
            style = self.userfacade.state.geophotostyle[key]
            if PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path in style:
                text = style[PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path]
        completions = list()
        for item in PhotoPlace_TEMPLATE_VARS:
            completions.append("%(" + item + ")s")
        filename = None
        try:
            templates = self.userfacade.options[TEMPLATES_KEY]
            filename = templates[PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path]
        except:
            pass
        tooltip = ''
        self.windowteditor.show(text=text, template=filename, recover=filename,
            completions=completions, tooltip=tooltip, cansave=False)
        self.windowteditor.connect('close', self._editor_setdesc, geophoto, ite)

    def _editor_setdesc(self, obj, text, filename, geophoto, ite):
        key = geophoto.path
        if key in self.userfacade.state.geophotostyle:
            style = self.userfacade.state.geophotostyle[key]
        else:
            style = dict()
            self.userfacade.state.geophotostyle[key] = style
        style[PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path] = text

    def _clicked_template_edit(self, widget, keypath, template):
        completions = list()
        if keypath == PhotoPlace_Cfg_KmlTemplateDescriptionPhoto_Path:
            for item in PhotoPlace_TEMPLATE_VARS:
                completions.append("%(" + item + ")s")
        self.windowteditor.show(template=template, completions=completions)

    def show_editvariables(self, widget=None, data=None):
        self.windowvariables.show()

    def reload_templates(self):
        if self.action_loadtemplates():
            model = self["treeview-geophotos"].get_model()
            iterator = model.get_iter_root()
            while iterator != None:
                geophoto_path = model.get_value(iterator, TREEVIEWPHOTOS_COL_PATH)
                for geophoto in self.userfacade.state.geophotos:
                    if geophoto.path == geophoto_path:
                        self.set_geophoto_variables(iterator, geophoto)
                        break
                next = model.iter_next(iterator)
                while next != None and  model.iter_parent(next) == iterator:
                    next = model.iter_next(next)
                iterator = next
            self["treeview-geophotos"].expand_all()

    def _reload_templates_cb(self, obj, text, filename, *args, **kwargs):
        for k, v in self.userfacade.options[TEMPLATES_KEY].iteritems():
            if os.path.basename(v) == os.path.basename(filename):
                # Only reload templates if are main (in the config file)
                self.reload_templates()
                return

    def reload_treeviewgeophotos(self):
        self["treeview-geophotos"].get_model().clear()
        self.num_photos_process = 0
        for geophoto in self.userfacade.state.geophotos:
            self._load_geophoto(geophoto)
            if geophoto.status > 0:
                self.num_photos_process += 1


    # ####################
    # User Actions Section
    # ####################

    def action_saveconfig(self, widget=None):
        try:
            self.userfacade.save_config()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)

    def action_recoverconfig(self, widget, data=None):
        try:
            self.userfacade.recover_config()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
        else:
            dgettext = dict()
            dgettext['file'] = self.userfacade.configfile
            msg = _("The original configuration file was recovered to '%(file)s'.")
            msg = msg % dgettext
            tip = _("Restart the program in order to read the new configuration.")
            mtype = _("Attention!")
            self.show_dialog(mtype, msg, tip, gtk.MESSAGE_INFO)

    def action_clear(self, widget=None):
        plugin_mode = self["toggletoolbutton-plugins"].get_active()
        if plugin_mode:
            for plg in self.plugins:
                (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
                if menuitem.get_active():
                    #menuitem.set_active(False)
                    try:
                        self.userfacade.reset_plugin(plg, '*')
                    except Error as e:
                        self.show_dialog(e.type, e.msg, e.tip)
        try:
            self.userfacade.Clear()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
        else:
            self["button-openphotos"].set_label(_("Select input photo directory"))
            self["button-opengpx"].set_label(_("Input GPX file"))
            self["checkbutton-outgeo"].set_active(True)
            self._toggle_geolocate_mode()
            self["togglebutton-outfile"].set_active(False)
            self._toggle_outfile()
            self["treeview-geophotos"].get_model().clear()
            self.userfacade.DoTemplates().run()
            self.num_photos_process = 0
            self.firstloadedphotos = False
            self.reloadtemplates = False

    def action_loadtemplates(self):
        try:
            loadtemplates = self.userfacade.DoTemplates()
            if loadtemplates:
                loadtemplates.run()
                return True
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False

    def action_loadphotos(self, directory=None):
        try:
            photoinputdir = directory
            if directory != None and not isinstance(directory, unicode):
                try:
                    photoinputdir = unicode(directory, 'UTF-8')
                except:
                    pass
            loadphotos = self.userfacade.LoadPhotos(photoinputdir)
            if loadphotos:
                loadphotos.start()
                return True
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False

    def action_readgpx(self, filename=None):
        try:
            gpxinputfile = filename
            if filename != None and not isinstance(filename, unicode):
                try:
                    gpxinputfile = unicode(filename, 'UTF-8')
                except:
                    pass
            readgpx = self.userfacade.ReadGPX(gpxinputfile)
            if readgpx:
                readgpx.run()
                return True
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False

    def action_geolocate(self):
        try:
            geolocate = self.userfacade.Geolocate()
            if geolocate:
                geolocate.run()
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False
        self.reload_treeviewgeophotos()
        return True

    def action_process(self, widget, data=None):
        if self.in_process:
            return False
        self.in_process = True
        if self.reloadtemplates:
            if not self.action_loadtemplates():
                self.in_process = False
                return False
        self._set_photouri()
        if self.userfacade.state['gpxinputfile']:
            if not self.action_geolocate():
                self.in_process = False
                return False
        if self.num_photos_process < 1:
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.status > 0 and geophoto.isGeoLocated():
                    self.num_photos_process += 1
            if self.num_photos_process < 1:
                mtype = _("OOps ...")
                msg = _("There are no geotagged photos!, I cannot do anything!.")
                tip = _("Load a GPX file or select a folder with geotagged photos.")
                self.show_dialog(mtype, msg, tip, gtk.MESSAGE_INFO)
                self.in_process = False
                return False
        self.progressbar.set_fraction(0.0)
        self.progressbar_percent = 0.0
        if self.userfacade.state.outputkmz != None:
            factor = self.num_photos_process * 7
        else:
            factor = self.num_photos_process * 6
        self.progressbar_fraction = 1.0/factor
        try:
            self.userfacade.goprocess()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            self.in_process = False
            return False
        self.reloadtemplates = True
        self.in_process = False
        return True


# EOF
