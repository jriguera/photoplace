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
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import os
import sys
import time
import Image
import StringIO
import cgi
import warnings

if sys.platform.startswith("win"):
    # Fetchs gtk2 path from registry
    import _winreg
    import msvcrt
    try:
        k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\GTK\\2.0")
    except EnvironmentError:
        print("You must install the Gtk+ 2.2 Runtime Environment to run this program")
        while not msvcrt.kbhit():
            pass
        raise
    else:
        gtkdir = _winreg.QueryValueEx(k, "Path")
        os.environ['PATH'] += ";%s/lib;%s/bin" % (gtkdir[0], gtkdir[0])

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



__RESOURCES_GTK_PATH__ = "gtkui"
__GUIXML_FILE__ = os.path.join(__RESOURCES_GTK_PATH__, "photoplace.ui")
__GUIICON_FILE__ = os.path.join(__RESOURCES_GTK_PATH__, "photoplace.png")
__PIXBUF_SIZE__ = (568,426)


from definitions import *
from observerHandler import *
from stateHandler import *
from userFacade import *
from Plugins.Interface import *
from Interface import InterfaceUI



def get_pixbuf_from_geophoto(geophoto, size=__PIXBUF_SIZE__):
    im = Image.open(geophoto.path)
    (im_width, im_height) = im.size
    # Size transformations
    (width, height) = size
    mirror = im.resize((width, height), Image.ANTIALIAS)
    if 'Exif.Image.Orientation' in geophoto.exif.exif_keys:
        orientation = geophoto.exif['Exif.Image.Orientation'].value
        if orientation == 1:
            pass
        elif orientation == 2:
            # Vertical Mirror
            mirror = mirror.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            # Rotation 180
            mirror = mirror.transpose(Image.ROTATE_180)
        elif orientation == 4:
            # Horizontal Mirror
            mirror = mirror.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            # Horizontal Mirror + Rotation 270
            mirror = mirror.transpose(Image.FLIP_TOP_BOTTOM). \
                transpose(Image.ROTATE_270)
        elif orientation == 6:
            # Rotation 270
            mirror = mirror.transpose(Image.ROTATE_270)
        elif orientation == 7:
            # Vertical Mirror + Rotation 270
            mirror = mirror.transpose(Image.FLIP_LEFT_RIGHT). \
                transpose(Image.ROTATE_270)
        elif orientation == 8:
            # Rotation 90
            mirror = mirror.transpose(Image.ROTATE_90)
    filein = StringIO.StringIO()
    mirror.save(filein, 'ppm')
    contents = filein.getvalue()
    filein.close()
    loader = gtk.gdk.PixbufLoader("pnm")
    loader.write(contents, len(contents))
    loader.close()
    pixbuf = loader.get_pixbuf()
    return pixbuf



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
        gtk.gdk.threads_enter()
        InterfaceUI.__init__(self, resourcedir)
        guifile = os.path.join(self.resourcedir, __GUIXML_FILE__)
        self.builder = gtk.Builder()
        self.builder.add_from_file(guifile)
        # Notebook and menuitem for plugins
        self.notebook = self.builder.get_object("notebook")
        self.notebook_plugins = self.builder.get_object("notebook-plugins")
        self.toggletoolbutton_plugins = self.builder.get_object("toggletoolbutton-plugins")
        imagemenuitem_plugins = self.builder.get_object("imagemenuitem-plugins")
        self.menuitem_plugins = gtk.Menu()
        imagemenuitem_plugins.set_submenu(self.menuitem_plugins)
        self.progressbar = self.builder.get_object("progressbar-go")
        #self.progressbar.set_pulse_step(0.05)
        self.treeview = self.builder.get_object("treeview-geophotos")
        self.treeview_model = self.treeview.get_model()
        # exif modes
        self.combobox_exif = self.builder.get_object("combobox-exif")
        self.combobox_exif_model = self.combobox_exif.get_model()
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
        self.photoinfo_win = self.builder.get_object("window-photoinfo")
        self.kmz_save_dlg = self.make_save_dialog()
        self.dir_open_dlg = self.make_opendir_dialog()
        self.gpx_open_dlg = self.make_opengpx_dialog()
        # show window
        #self.window.set_icon_from_file(os.path.join(resourcedir, __GUIICON_FILE__))
        #gtk.window_set_default_icon_from_file(os.path.join(resourcedir, __GUIICON_FILE__))
        self["treeviewcolumn-photoinfo-key"].set_title(_("Property"))
        self["treeviewcolumn-photoinfo-value"].set_title(_("Value"))
        self["treeview-photoinfo"].set_model(gtk.TreeStore(bool, bool, str, str, str))
        self["treeview-photoinfo"].set_rules_hint(True)
        self.window.show_all()

    def __getitem__(self, key):
        return self.builder.get_object(key)

    def __setitem__(self, key, value):
        raise ValueError(_("Cannot set key!"))

    def init(self, userfacade):
        self.userfacade = userfacade
        self.plugins = dict()
        self.num_photos_process = 0
        # Observer for statusbar. INFO or ERROR loglevels
        self.userfacade.addlogObserver(self._log_to_statusbar_observer, 
            [logging.INFO, logging.ERROR], self, self.statusbar_formatter)
        # Observer for textview
        self.userfacade.addlogObserver(self._log_to_textview_observer, 
            [], self, self.textview_formatter)
        # Progress bar
        self.progressbar_fraction = 0.0
        self.progressbar_percent = 0.0
        self.userfacade.addNotifier(self._set_progressbar_makekml_observer,
            ["MakeKML:run"], self)
        self.userfacade.addNotifier(self._set_progressbar_writeexif_observer,
            ["WriteExif:run"], self)
        self.userfacade.addNotifier(self._set_progressbar_copyfiles_observer,
            ["CopyFiles:run"], self)
        self.userfacade.addNotifier(self._set_progressbar_savefiles_observer,
            ["SaveFiles:run"], self)
        self.userfacade.addNotifier(self._update_progressbar_loadphoto_observer, 
            ["LoadPhotos:run"], self)
        self.userfacade.addNotifier(self._update_progressbar_geolocate_observer, 
            ["Geolocate:run"], self)
        self.userfacade.addNotifier(self._update_progressbar_makegpx_observer, 
            ["MakeGPX:run"], self)
        self.userfacade.addNotifier(
            self._set_progressbar_end_observer, [
                "LoadPhotos:end",
                "Geolocate:end",
                "MakeGPX:end",
                "SaveFiles:end",
            ], self)
        # Make a new state
        try:
            self.userfacade.init()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            self.userfacade.init(True)
        # adjustments
        self['adjustment-jpgzoom'].set_value(self.userfacade.state['jpgzoom'])
        self['adjustment-tdelta'].set_value(self.userfacade.state['maxdeltaseconds'])
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


    def start(self, load_files=True):
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
                gobject.idle_add(self.statusbar.pop, self.statusbar_context)
                gobject.idle_add(self.statusbar.push, self.statusbar_context, msg)
        # GTK signals
        self.signals = {
            "on_aboutdialog_close": self.dialog_close,
            "on_aboutdialog_response": self.dialog_response,
            "on_aboutdialog_delete_event": self.dialog_close,
            "on_window_destroy": self.window_exit,
            "on_imagemenuitem-opendir_activate": self._clicked_photodir,
            "on_imagemenuitem-opengpx_activate": self._clicked_gpx,
            "on_imagemenuitem-save_activate": self._clicked_outfile,
            "on_imagemenuitem-new_activate": self.action_clear,
            "on_imagemenuitem-exit_activate": self.window_exit,
            "on_imagemenuitem-about_activate": self.dialog_show,
            "on_button-openphotos_clicked": self._clicked_photodir,
            "on_button-opengpx_clicked": self._clicked_gpx,
            "on_toggletoolbutton-plugins_toggled": self._toggle_loadplugins,
            "on_toolbutton-exit_clicked": self.window_exit,
            "on_togglebutton-outfile_toggled": self._toggle_outfile,
            "on_checkbutton-outgeo_toggled": self._toggle_geolocate_mode,
            "on_adjustment-utc_value_changed": self._adjust_utctimezone,
            "on_adjustment-quality_value_changed": self._adjust_quality,
            "on_adjustment-jpgzoom_value_changed": self._adjust_jpgzoom,
            "on_button-go_clicked": self.action_process,
            "on_button-geolocate_clicked": self._clicked_geolocate,
            "on_cellgeophotos_toggled": self._toggle_geophoto,
            "on_treeview-geophotos_row_activated": self._clicked_geophoto,
            "on_window-photoinfo_delete_event": self.dialog_close,
            "on_button-photoinfo-close_clicked": self.dialog_close,
            "on_button-photoinfo-add_clicked": self._add_photoinfo_attr,
            "on_button-photoinfo-del_clicked": self._del_photoinfo_attr,
            "on_button-photoinfo-next_clicked": self._clicked_next_photoinfo,
            "on_button-photoinfo-prev_clicked": self._clicked_prev_photoinfo,
            "on_treeview-photoinfo_row_activated": self._clicked_photoinfo_att
        }
        self.builder.connect_signals(self.signals)
        if sys.platform.startswith('win'):
            sleeper = lambda: time.sleep(.001) or True
            gobject.timeout_add(400, sleeper)
        #gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()

    def window_exit(self,widget,data=None):
        for plg in self.plugins.keys():
            (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
            if menuitem.get_active():
                menuitem.set_active(False)
        try:
            self.end()
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


    # #################
    # Plugin Management
    # #################

    def loadPlugins(self):
        try:
            errors = self.userfacade.load_plugins('*', self.builder)
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
        else:
            for e in errors:
                self.show_dialog(e.type, e.msg, e.tip)
        # generate menu a menu entry for each plugin
        self.toggling_active_plugin = False
        dgettext = dict()
        for plg, plgobj in self.userfacade.list_plugins().iteritems():
            if plg in self.plugins:
                continue
            menuitem = gtk.CheckMenuItem(str(plg))
            notebookindex = -1
            notebookframe = None
            menuitem.set_active(False)
            self.menuitem_plugins.add(menuitem)
            menuitem.connect('toggled', self._toggle_active_plugin, plg)
            dgettext['plugin_name'] = str(plg)
            dgettext['plugin_version'] = str(plgobj.version)
            dgettext['plugin_author'] = cgi.escape(plgobj.author)
            dgettext['plugin_mail'] = cgi.escape(plgobj.email)
            dgettext['plugin_cpr'] = cgi.escape(plgobj.copyright)
            dgettext['plugin_date'] = cgi.escape(plgobj.date)
            dgettext['plugin_lic'] = cgi.escape(plgobj.license)
            dgettext['plugin_url'] = cgi.escape(plgobj.url)
            dgettext['plugin_desc'] = cgi.escape(plgobj.description)
            markup = _("Plugin <b>%(plugin_name)s</b> version %(plugin_version)s\n"
                "by <b>%(plugin_author)s</b> %(plugin_mail)s\n"
                "%(plugin_cpr)s %(plugin_date)s, License: %(plugin_lic)s\n"
                "More info at: <b>%(plugin_url)s</b>\n\n<i>%(plugin_desc)s</i>")
            menuitem.set_tooltip_markup(markup % dgettext)
            menuitem.show()
            if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                notebooklabel = gtk.Label()
                notebooklabel.set_markup(str("<b>%s</b>" % plg))
                labelop = gtk.Label()
                labelop.set_markup(str(_("<b>Options</b>")))
                labelop.set_padding(2, 8)
                notebookframe = gtk.Frame()
                notebookframe.set_label_widget(labelop)
                notebookindex = self.notebook_plugins.append_page(
                    notebookframe, notebooklabel)
                notebookframe.show_all()
            self.plugins[plg] = (plgobj, menuitem, notebookindex, notebookframe)
        # Active all plugins
        self["toggletoolbutton-plugins"].set_active(True)
        self._toggle_loadplugins()

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
        for plg in self.plugins.keys():
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
        gobject.idle_add(self.statusbar.pop, self.statusbar_context)
        gobject.idle_add(self.statusbar.push, self.statusbar_context, msg)

    @DObserver
    def _log_to_textview_observer(self, formatter, record):
        msg = formatter.format(record)
        level = "error"
        if record.levelno == logging.DEBUG:
            level = "debug"
        elif record.levelno == logging.WARNING:
            level = "warning"
        elif record.levelno == logging.INFO:
            level = "info"
        gobject.idle_add(self.set_textview, msg, level)

    def set_textview(self, msg, level="info"):
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iter)
        self.textbuffer.insert_with_tags_by_name(iter, msg, level)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0.1)

    def pulse_progressbar(self, msg=''):
        gobject.idle_add(self.progressbar.set_text, msg)
        gobject.idle_add(self.progressbar.pulse)

    @DObserver
    def _update_progressbar_loadphoto_observer(self, geophoto, *args):
        msg = _("Loading photo %s ...") % geophoto.name
        self.pulse_progressbar(msg)
        self._load_geophoto(geophoto)

    @DObserver
    def _update_progressbar_geolocate_observer(self, photo, *args):
        msg = _("Geotagging photo %s ...") % photo.name
        self.pulse_progressbar(msg)

    @DObserver
    def _update_progressbar_makegpx_observer(self, photo, *args):
        msg = _("Processing photo %s ...") % photo.name
        self.pulse_progressbar(msg)

    def set_progressbar(self, text=None, percent=-1.0):
        if percent < 0.0:
            self.progressbar_percent += self.progressbar_fraction
        else:
            self.progressbar_percent = percent
        if self.progressbar_percent > 1.0:
            self.progressbar_percent = 1.0
        if percent == 0.0:
            msg = _("Let's Go!")
        else:
            msg = "[" + str(int(self.progressbar_percent * 100)) + "%]"
            if text:
                msg = msg + "  " + text 
        gobject.idle_add(self.progressbar.set_text, msg)
        gobject.idle_add(self.progressbar.set_fraction, self.progressbar_percent)

    @DObserver
    def _set_progressbar_makekml_observer(self, photo, *args):
        msg = _("Adding to KML info of %s ...") % photo.name
        self.set_progressbar(msg)

    @DObserver
    def _set_progressbar_writeexif_observer(self, photo, *args):
        msg = _("Writing EXIF info of %s ...") % photo.name
        self.set_progressbar(msg)

    @DObserver
    def _set_progressbar_copyfiles_observer(self, photo, *args):
        msg = _("Copying photo %s ...") % photo.name
        self.set_progressbar(msg)

    @DObserver
    def _set_progressbar_savefiles_observer(self, filename, *args):
        msg = _("Saving file %s ...") % filename
        self.set_progressbar(msg)

    @DObserver
    def _set_progressbar_end_observer(self, *args):
        self.set_progressbar(None, 0.0)


    # ##############################################
    # Make GTK Dialogs (Open, Select directory, ...)
    # ##############################################

    def make_opengpx_dialog(self, title=_("Select input GPX file ...")):
        gpx_open_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name(_("GPS eXchange Format GPX"))
        filter.add_mime_type("application/gpx+xml")
        filter.add_pattern("*.gpx")
        gpx_open_dlg.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        gpx_open_dlg.add_filter(filter)
        return gpx_open_dlg

    def make_opendir_dialog(self, title=_("Select a directory with photos ...")):
        photodir_open_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        return photodir_open_dlg

    def make_save_dialog(self, title=_("Choose output file ...")):
        kmz_save_dlg = gtk.FileChooserDialog(title=title, parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name(_("Keyhole Markup Language (Google Earth Layer) KMZ"))
        filter.add_mime_type("application/vnd.google-earth.kmz")
        filter.add_pattern("*.kmz")
        kmz_save_dlg.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name(_("Keyhole Markup Language (Google Earth Layer) KML"))
        filter.add_mime_type("application/vnd.google-earth.kml+xml")
        filter.add_pattern("*.kml")
        kmz_save_dlg.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        kmz_save_dlg.add_filter(filter)
        return kmz_save_dlg


    # ##############################################
    # Show GTK Dialogs (Open, Select directory, ...)
    # ##############################################

    def show_dialog(self, title, msg, tip="", dtype=gtk.MESSAGE_ERROR):
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

    def show_dialog_choose_photodir(self, select_dir=None):
        if select_dir:
            self.dir_open_dlg.set_current_folder(select_dir)
        directory = None
        if self.dir_open_dlg.run() == gtk.RESPONSE_OK:
            directory = self.dir_open_dlg.get_filename()
        self.dir_open_dlg.hide()
        if directory:
            return self.action_loadphotos(directory)

    def show_dialog_choose_gpx(self, select_file=None):
        if select_file:
            self.gpx_open_dlg.set_filename(select_file)
        filename = None
        if self.gpx_open_dlg.run() == gtk.RESPONSE_OK:
            filename = self.gpx_open_dlg.get_filename()
        self.gpx_open_dlg.hide()
        if filename:
            return self.action_readgpx(filename)

    def show_dialog_choose_outfile(self, select_file=None):
        if select_file:
            self.kmz_save_dlg.set_current_name(select_file)
        filename = None
        if self.kmz_save_dlg.run() == gtk.RESPONSE_OK:
            filename = self.kmz_save_dlg.get_filename()
        self.kmz_save_dlg.hide()
        if filename:
            try:
                self.userfacade.state['outputfile'] = filename
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
            self['togglebutton-outfile'].set_label(_("Generate: ") +
                self.userfacade.state['outputfile'])
            self['hscale-quality'].set_sensitive(True)
            self['hscale-zoom'].set_sensitive(True)
            self['entry-photouri'].set_sensitive(True)
            self._set_photouri()
        else:
            self['togglebutton-outfile'].set_label(
                _("No generate output file! Select a file to continue."))
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

    def _toggle_geolocate_mode(self, widget=None, data=None):
        if self['checkbutton-outgeo'].get_active():
            self['combobox-exif'].set_sensitive(True)
            position = 0
            default_pos = 0
            self.combobox_exif_model.clear()
            for k, v in PhotoPlace_Cfg_ExifModes.iteritems():
                if k == -1:
                    continue
                self.combobox_exif_model.append([v, k])
                if k == self.userfacade.state["exifmode"]:
                    default_pos = position
                position += 1
            self['checkbutton-outgeo'].set_label(_("Geolocate photos in mode:"))
            self['combobox-exif'].set_active(default_pos)
        else:
            self['checkbutton-outgeo'].set_label(_("No geolocate photos"))
            self['combobox-exif'].set_sensitive(False)
            self.userfacade.state["exifmode"] = -1

    def _set_photouri(self, name=None):
        if name:
            self.userfacade.state['photouri'] = name
            self["entry-photouri"].set_text(name)
        else:
            photouri = self["entry-photouri"].get_text().strip()
            if not photouri:
                photouri = self.userfacade.state['photouri']
                self["entry-photouri"].set_text(photouri)
            else:
                self.userfacade.state['photouri'] = photouri
                photouri = self.userfacade.state['photouri']
                self["entry-photouri"].set_text(photouri)

    def _adjust_utctimezone(self, widget, data=None):
        value = widget.get_value()
        new_value = float_to_timefloat(value)
        if new_value != value:
            widget.set_value(new_value)
        self.userfacade.state['utczoneminutes'] = timefloat_to_minutes(new_value)

    def _adjust_quality(self, widget, data=None):
        value = widget.get_value()
        self.userfacade.state['quality'] = int(value)

    def _adjust_jpgzoom(self, widget, data=None):
        value = widget.get_value()
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

    def _load_geophoto(self, geophoto):
        color = PhotoPlace_Cfg_TreeViewColorNormal
        previews = geophoto.exif.previews
        largest = previews[-1]
        loader = gtk.gdk.PixbufLoader('jpeg')
        width, height = PhotoPlace_Cfg_TreeViewPhotoSize
        loader.set_size(width, height)
        loader.write(largest.data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        dgettext = dict()
        dgettext['name'] = geophoto.name
        dgettext['path'] = geophoto.path
        dgettext['date'] = geophoto.time.strftime("%A, %d. %B %Y")
        dgettext['time'] = geophoto.time.strftime("%H:%M:%S")
        dgettext['lon'] = geophoto.lon
        dgettext['lat'] = geophoto.lat
        dgettext['ele'] = geophoto.ele
        tips = "%(path)s\n\n"
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
        information = _("Name: %(name)s\nDate: %(date)s\nTime: %(time)s") % dgettext
        if geophoto.isGeoLocated():
            geodata = _("Longitude: %(lon)f\nLatitude: %(lat)f\nElevation: %(ele)f") % dgettext
            color = PhotoPlace_Cfg_TreeViewColorGeo
        else:
            geodata = _("Picture not Geolocated!")
        tips = tips % dgettext
        if geophoto.status > 1:
            geophoto.status = 1
            color = PhotoPlace_Cfg_TreeViewColorChanged
        if geophoto.attr:
            tips += _("# Attributes: \n")
            for k,v in geophoto.attr.iteritems():
                tips += "\t%s: %s\n" % (k, v)
        self.treeview_model.append([ 
            geophoto.status, geophoto.name, geophoto.path, geophoto.time,
            bool(geophoto.status), pixbuf, information, geodata, 
            tips, color])
    
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

    def _clicked_geophoto(self, treeview, path, column, data=None):
        model = treeview.get_model()
        ite = model.get_iter(path)
        name = model.get_value(ite, TREEVIEWPHOTOS_COL_NAME)
        geophoto_path = model.get_value(ite, TREEVIEWPHOTOS_COL_PATH)
        for geophoto in self.userfacade.state.geophotos:
            if geophoto.path == geophoto_path:
                self.treeview_iterator = ite
                self.show_window_photoinfo(geophoto)
                #self.photoinfo_win.resize(1, 1)
                #self.photoinfo_win.show()
                return True
        return False


    # #################################
    # Photo Extended information window
    # #################################

    def show_window_photoinfo(self, geophoto):
        photoinfo_path = self["label-photoinfo-geophotopath"]
        photoinfo_path.set_text(geophoto.path)
        photoinfo_image = self["image-photoinfo"]
        scaled = get_pixbuf_from_geophoto(geophoto)
        photoinfo_image.set_from_pixbuf(scaled)
        self._show_photoinfo_attr(geophoto)
        self.photoinfo_win.resize(1, 1)
        self.current_geophoto = geophoto
        self.photoinfo_win.show()

    def _clicked_next_photoinfo(self, widget=None, data=None):
        next = self.treeview_model.iter_next(self.treeview_iterator)
        if next:
            geophoto_path = self.treeview_model.get_value(next, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.treeview_iterator = next
                    self.show_window_photoinfo(geophoto)
                    return

    def _clicked_prev_photoinfo(self, widget=None, data=None):
        path = self.treeview_model.get_path(self.treeview_iterator)
        position = path[-1]
        if position != 0:
            prev_path = list(path)[:-1]
            prev_path.append(position - 1)
            prev = self.treeview_model.get_iter(tuple(prev_path))
            geophoto_path = self.treeview_model.get_value(prev, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.treeview_iterator = prev
                    self.show_window_photoinfo(geophoto)
                    return

    def _show_photoinfo_attr(self, geophoto):
        model = self["treeview-photoinfo"].get_model()
        model.clear()
        color = TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR
        model.append(None,[False, False, str(_("Image name")), str(geophoto['name']), color])
        model.append(None,[False, False, str(_("Date/Time")), str(geophoto['time']), color])
        model.append(None,[False, False, str(_("Longitude")), str("%f" % geophoto['lon']), color])
        model.append(None,[False, False, str(_("Latitude")), str("%f" % geophoto['lat']), color])
        model.append(None,[False, False, str(_("Elevation")), str("%f" % geophoto['ele']), color])
        color = TREEVIEWPHOTOINFO_GEOPHOTOATTR_COLOR
        if geophoto.attr:
            ite = model.append(None, [False, False, _("Image Attributes"), None, color])
            for k, v in geophoto.attr.iteritems():
                model.append(ite, [ True, True, str(k), str(v), color])
        color = TREEVIEWPHOTOINFO_GEOPHOTOEXIF_COLOR
        ite = model.append(None, [ False, False, _("Image EXIF Values"), None, color])
        for k in geophoto.exif.exif_keys:
            try:
                model.append(ite, [ False, False, str(k), str(geophoto[k]), color])
            except:
                pass
        self["treeview-photoinfo"].expand_all()

    def _clicked_photoinfo_att(self, treeview, path, column, data=None):
        model = treeview.get_model()
        ite = model.get_iter(path)
        editable = model.get_value(ite, TREEVIEWPHOTOINFO_COL_EDIT)
        if editable:
            key = model.get_value(ite, TREEVIEWPHOTOINFO_COL_KEY)
            value = model.get_value(ite, TREEVIEWPHOTOINFO_COL_VALUE)
            self["entry-photoinfo-key"].set_text(key)
            self["entry-photoinfo-value"].set_text(value)

    def _add_photoinfo_attr(self, widget):
        key = self["entry-photoinfo-key"].get_text().strip()
        if key:
            value = self["entry-photoinfo-value"].get_text()
            self.current_geophoto.attr[key] = value.strip()
            self._show_photoinfo_attr(self.current_geophoto)

    def _del_photoinfo_attr(self, widget):
        key = self["entry-photoinfo-key"].get_text().strip()
        if self.current_geophoto.attr.has_key(key):
            del  self.current_geophoto.attr[key]
            self._show_photoinfo_attr(self.current_geophoto)
        self["entry-photoinfo-key"].set_text('')
        self["entry-photoinfo-value"].set_text('')


    # ####################
    # User Actions Section
    # ####################

    def action_clear(self, widget=None):
        plugin_mode = self["toggletoolbutton-plugins"].get_active()
        plugin_list = list()
        if plugin_mode:
            for plg in self.plugins.keys():
                (plgobj, menuitem, notebookindex, notebookframe) = self.plugins[plg]
                if menuitem.get_active():
                    menuitem.set_active(False)
                    plugin_list.append(menuitem)
        try:
            self.userfacade.Clear()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            if plugin_mode:
                for menuitem in plugin_list:
                    menuitem.set_active(True)
        else:
            self["button-openphotos"].set_label(_("Select input photo directory") + "  ")
            self["button-opengpx"].set_label(_("Input GPX file") + "  ")
            self["checkbutton-outgeo"].set_active(True)
            self._toggle_geolocate_mode()
            self["togglebutton-outfile"].set_active(False)
            self._toggle_outfile()
            self.current_geophoto = None
            self.treeview_iterator = None
            self.treeview_model.clear()
            if plugin_mode:
                for menuitem in plugin_list:
                    menuitem.set_active(True)
            self.userfacade.DoTemplates().run()
            self.num_photos_process = 0

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
            loadphotos = self.userfacade.LoadPhotos(directory)
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
            readgpx = self.userfacade.ReadGPX(filename)
            if readgpx:
                readgpx.run()
                return True
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False

    def action_geolocate(self):
        iter_mode = self['combobox-exif'].get_active_iter()
        mode = self.combobox_exif_model.get_value(iter_mode, 1)
        self.userfacade.state["exifmode"] = mode
        try:
            geolocate = self.userfacade.Geolocate()
            if geolocate:
                geolocate.run()
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False
        self.treeview_model.clear()
        self.num_photos_process = 0
        for geophoto in self.userfacade.state.geophotos:
            self._load_geophoto(geophoto)
            if geophoto.status > 0:
                self.num_photos_process += 1
        return True

    def action_process(self, widget, data=None):
        self._set_photouri()
        iter_mode = self['combobox-exif'].get_active_iter()
        mode = self.combobox_exif_model.get_value(iter_mode, 1)
        self.userfacade.state["exifmode"] = mode
        if self.userfacade.state['gpxinputfile']:
            if not self.action_geolocate():
                return False
        if self.num_photos_process < 1:
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.status > 0 and geophoto.isGeoLocated():
                    self.num_photos_process += 1
            if self.num_photos_process < 1:
                mtype = _("OOps ...")
                msg = _("Cannot do anything!. No GPX data and those photos are not geolocated!")
                tip = _("Load a GPX file to do that.")
                self.show_dialog(mtype, msg, tip, gtk.MESSAGE_INFO)
                return False
        self.progressbar.set_fraction(0.0)
        self.progressbar_percent = 0.0
        if self.userfacade.state.outputkmz != None:
            factor = self.num_photos_process * 8
        else:
            factor = self.num_photos_process * 7
        self.progressbar_fraction = 1.0/factor
        try:
            self.userfacade.goprocess()
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False
        return True


# EOF
