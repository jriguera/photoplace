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
import codecs
import Image
import webbrowser
import StringIO
import xml.dom.minidom
import getpass
import cgi
import warnings
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
from PhotoPlace.userFacade import *
from PhotoPlace.Plugins.Interface import *
from Interface import InterfaceUI
from GTKUIdefinitions import *



# ##############
# JPEG to pixbuf
# ##############

def get_pixbuf_from_geophoto(geophoto, size=PIXBUFSIZE_GEOPHOTOINFO):
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
# Autocompletion for textviews
# ############################

class TextViewCompleter(object):

    def __init__(self, textview, position, completion, size=TEXVIEWCOMPLETER_SIZE):
        object.__init__(self)
        self.textview = textview
        self.completion = completion
        self.position = position
        self.popup = gtk.Window(gtk.WINDOW_POPUP)
        parent = textview.get_toplevel()
        self.popup.set_transient_for(parent)
        self.popup.set_destroy_with_parent(True)
        frame = gtk.Frame()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        model = gtk.ListStore(gobject.TYPE_STRING)
        for item in self.completion:
            ite = model.append()
            model.set(ite, 0, item)
        self.list_view = gtk.TreeView(model)
        self.list_view.set_property("headers-visible", False)
        selection = self.list_view.get_selection()
        selection.select_path((0,))
        column = gtk.TreeViewColumn("", gtk.CellRendererText(), text=0)
        self.list_view.append_column(column)
        sw.add(self.list_view)
        frame.add(sw)
        self.popup.add(frame)
        self.popup.set_size_request(size[0], size[1])
        self.show_popup()

    def hide_popup(self, *args, **kwargs):
        self.popup.hide()

    def show_popup(self):
        tbuffer = self.textview.get_buffer()
        ite = tbuffer.get_iter_at_mark(tbuffer.get_insert())
        rectangle = self.textview.get_iter_location(ite)
        absX, absY = self.textview.buffer_to_window_coords(gtk.TEXT_WINDOW_TEXT,
            rectangle.x + rectangle.width + 0 ,
            rectangle.y + rectangle.height + 70)
        parent = self.textview.get_parent()
        self.popup.move(self.position[0] + absX, self.position[1] + absY)
        self.popup.show_all()

    def prev(self):
        sel = self.list_view.get_selection()
        model, ite = sel.get_selected()
        mite = model.get_path(ite)
        if mite != None and mite[0] > 0:
            path = (mite[0] - 1,)
            self.list_view.set_cursor(path)

    def next(self):
        sel = self.list_view.get_selection()
        model, ite = sel.get_selected()
        mite = model.iter_next(ite)
        if mite != None:
            path = model.get_path(mite)
            self.list_view.set_cursor(path)

    def confirm(self):
        sel = self.list_view.get_selection()
        selection = self.select(sel)
        self.destroy()
        return selection

    def select(self, selection):
        model, ite = selection.get_selected()
        name = model.get_value(ite, 0)
        return name

    def destroy(self):
        self.popup.hide()
        self.popup.destroy()


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
        InterfaceUI.__init__(self, resourcedir)
        guifile = os.path.join(self.resourcedir, GTKUI_RESOURCE_GUIXML)
        self.builder = gtk.Builder()
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
        self.photoinfo_win = self.builder.get_object("window-photoinfo")
        self.templates_win = self.builder.get_object("window-templates")
        # show window
        self["treeviewcolumn-photoinfo-key"].set_title(_("Property"))
        self["treeviewcolumn-photoinfo-value"].set_title(_("Value"))
        self["treeview-photoinfo"].set_model(gtk.TreeStore(bool, bool, str, str, str))
        self["treeview-photoinfo"].set_rules_hint(True)
        self["treeviewcolumn-geophotos-data"].set_title(_("Name"))
        self["treeviewcolumn-geophotos-value"].set_title(_("Value"))
        self["treeviewcolumn-geophotos-picture"].set_title(_("Picture"))
        self["treeviewcolumn-geophotos-info"].set_title(_("Information"))
        self["treeview-geophotos"].set_model(gtk.TreeStore(
            int, str, str, str, bool, gtk.gdk.Pixbuf, str, str, str, str, bool, bool, str))
        self["treeview-geophotos"].set_rules_hint(True)
        self["treeviewcolumn-variables-name"].set_title(_("Name"))
        self["treeviewcolumn-variables-value"].set_title(_("Value"))
        self["treeview-variables"].set_model(gtk.TreeStore(str, str, bool))
        self["treeview-variables"].set_rules_hint(True)
        textbuffer_templates = self["textbuffer-templates"]
        tag = textbuffer_templates.create_tag('attr')
        tag.set_property('foreground', "green")
        tag.set_property('family', "Monospace")
        tag = textbuffer_templates.create_tag('defaults')
        tag.set_property('foreground', "red")
        tag.set_property('family', "Monospace")
        tag = textbuffer_templates.create_tag('photo')
        tag.set_property('foreground', "blue")
        tag.set_property('family', "Monospace")
        self["textview-templates"].set_tooltip_markup(_("You can use simple "
            "HTML tags like <i>list</i> (<i>li</i>, <i>ul</i>) or <i>table</i> "
            "and use expresions like <b>%(Variable|<i>DEFAULT</i>)s</b> to get values. "
            "<i>DEFAULT</i> is the value to set when <i>Variable</i> has no value, if "
            "<i>DEFAULT</i> is none (not a character, even space) <i>Variable</i> "
            "will not be shown."
            "You can use the variables defined in the <b>[defaults]</b> "
            "section of the configuration file in the same way.\n"
            "To get all supported variables press <b>&lt;ctl&gt;&lt;space&gt;</b>"))
        self["textview-templates"].add_events( gtk.gdk.KEY_PRESS_MASK )
        self["textview-templates"].connect( "key_press_event", self._key_press_wintemplate)
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True
        self.in_process = True
        self.window.show_all()

    def __getitem__(self, key):
        return self.builder.get_object(key)

    def __setitem__(self, key, value):
        raise ValueError(_("Cannot set key!"))

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
            self._set_progressbar_copyfiles_observer, ["CopyFiles:run"], self)
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
        self.variables_iterator = None
        self.in_process = False

    def start(self, load_files=True):
        #gtk.gdk.threads_enter()
        if sys.platform.startswith('win'):
            sleeper = lambda: time.sleep(.001) or True
            gobject.timeout_add(400, sleeper)
            # redirect standard I/O to files
            cfg_dir = '.'
            if self.userfacade.configfile != None:
                cfg_dir = os.path.dirname(self.userfacade.configfile)
            sys.stdout = open(os.path.join(cfg_dir, 'stdout.log'), 'w+')
            sys.stderr = open(os.path.join(cfg_dir, 'stderr.log'), 'w+')
        loaded_templates = self.action_loadtemplates()
        self._show_variables()
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
        # GTK signals
        self.signals = {
            "on_aboutdialog_close": self.dialog_close,
            "on_aboutdialog_response": self.dialog_response,
            "on_aboutdialog_delete_event": self.dialog_close,
            "on_linkbutton-suggestion_clicked": self._open_link,
            "on_linkbutton-donate_clicked": self._open_link,
            "on_window_destroy": self.window_exit,
            "on_notebook_create_window": self._create_notebookwindow,
            "on_imagemenuitem-opendir_activate": self._clicked_photodir,
            "on_imagemenuitem-opengpx_activate": self._clicked_gpx,
            "on_imagemenuitem-save_activate": self._clicked_outfile,
            "on_imagemenuitem-new_activate": self.action_clear,
            "on_imagemenuitem-saveconf_activate": self.action_saveconfig,
            "on_imagemenuitem-recoverconf_activate": self.action_recoverconfig,
            "on_imagemenuitem-exit_activate": self.window_exit,
            "on_imagemenuitem-about_activate": self.dialog_show,
            "on_imagemenuitem-onlinehelp_activate": self._click_onlinehelp,
            "on_button-openphotos_clicked": self._clicked_photodir,
            "on_button-opengpx_clicked": self._clicked_gpx,
            "on_toggletoolbutton-plugins_toggled": self._toggle_loadplugins,
            "on_toolbutton-exit_clicked": self.window_exit,
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
            "on_window-photoinfo_delete_event": self._close_winphotoinfo,
            "on_button-photoinfo-close_clicked": self._close_winphotoinfo,
            "on_button-photoinfo-add_clicked": self._add_photoinfo_attr,
            "on_button-photoinfo-del_clicked": self._del_photoinfo_attr,
            "on_button-photoinfo-next_clicked": self._clicked_next_photoinfo,
            "on_button-photoinfo-prev_clicked": self._clicked_prev_photoinfo,
            "on_cellrenderertext-photoinfo-value_edited": self._edit_cell_photoinfo,
            "on_treeview-photoinfo_row_activated": self._clicked_photoinfo_att,
            "on_button-variables-add_clicked": self._add_variable,
            "on_button-variables-del_clicked": self._del_variable,
            "on_cellrenderertext-variables-value_edited": self._edit_cell_variable,
            "on_cellrenderertext-geophotos-value_edited": self._edit_cell_geophoto,
            "on_button-templates-edit_clicked": self._clicked_template_edit,
            "on_window-templates_delete_event": self._close_wintemplate,
            "on_toolbutton-wintemplates-exit_clicked": self._close_wintemplate,
            "on_toolbutton-wintemplates-load_clicked": self._load_template_file,
            "on_toolbutton-wintemplates-save_clicked": self._save_wintemplate,
            "on_textbuffer-templates_mark_set": self._update_wintemplate_statusbar,
            "on_textbuffer-templates_changed": self._update_wintemplate_statusbar,
            "on_toolbutton-wintemplates-new_clicked": self._new_wintemplate,
            "on_toolbutton-wintemplates-recover_clicked": self._recover_wintemplate,
            "on_toolbutton-wintemplates-check_clicked": self._validate_wintemplate,
        }
        self.builder.connect_signals(self.signals)
        gtk.main()
        gtk.gdk.threads_leave()

    def window_exit(self, widget, data=None):
        for plg in self.plugins:
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
        for p in self.userfacade.options["plugins"]:
            if not p in errors:
                try:
                    error = self.userfacade.activate_plugin(p, self.builder)
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
            if plgobj.capabilities['GUI'] == PLUGIN_GUI_GTK:
                notebooklabel = gtk.Label()
                notebooklabel.set_markup(str("   <b>%s</b>  " % plg))
                labelop = gtk.Label()
                labelop.set_markup(str(_("<b>Options</b>")))
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
        level = "error"
        if record.levelno == logging.DEBUG:
            level = "debug"
        elif record.levelno == logging.WARNING:
            level = "warning"
        elif record.levelno == logging.INFO:
            level = "info"
        gobject.idle_add(self.set_textview, msg, level)

    def set_textview(self, msg, level="info"):
        iterator = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iterator)
        self.textbuffer.insert_with_tags_by_name(iterator, msg, level)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0.1)

    def pulse_progressbar(self, msg=''):
        self.progressbar.set_text(msg)
        self.progressbar.pulse()

    @DObserver
    def _update_progressbar_loadphoto_observer(self, geophoto, *args):
        msg = _("Loading photo %s ...") % geophoto.name
        gobject.idle_add(self.pulse_progressbar, msg)
        self._load_geophoto(geophoto)

    @DObserver
    def _update_progressbar_geolocate_observer(self, photo, *args):
        msg = _("Geotagging photo %s ...") % photo.name
        gobject.idle_add(self.pulse_progressbar, msg)

    @DObserver
    def _update_progressbar_makegpx_observer(self, photo, *args):
        msg = _("Processing photo %s ...") % photo.name
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
        else:
            msg = "[" + str(int(self.progressbar_percent * 100)) + "%]"
            if text:
                msg = msg + "  " + text
        self.progressbar.set_text(msg)
        self.progressbar.set_fraction(self.progressbar_percent)

    @DObserver
    def _set_progressbar_makekml_observer(self, photo, *args):
        msg = _("Adding to KML info of %s ...") % photo.name
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_writeexif_observer(self, photo, *args):
        msg = _("Writing EXIF info of %s ...") % photo.name
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_copyfiles_observer(self, photo, *args):
        msg = _("Copying photo %s ...") % photo.name
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_savefiles_observer(self, filename, *args):
        msg = _("Saving file %s ...") % filename
        gobject.idle_add(self.set_progressbar, msg)

    @DObserver
    def _set_progressbar_end_observer(self, *args):
        gobject.idle_add(self.set_progressbar, None, 0.0)

    @DObserver
    def _set_loadphotos_end_observer(self, *args):
        gobject.idle_add(self.set_progressbar, None, 0.0)
        # order by name
        self["treeviewcolumn-geophotos-picture"].clicked()


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
            filename = self.userfacade.state['outputfile']
            if len(filename) > 34:
                filename = os.path.basename(filename)
            self['togglebutton-outfile'].set_label(_("Generate: ") + filename)
            self['hscale-quality'].set_sensitive(True)
            self['hscale-zoom'].set_sensitive(True)
            self['entry-photouri'].set_sensitive(True)
            self._set_photouri()
        else:
            self['togglebutton-outfile'].set_label(_(" No generate output file!"))
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

    def _toggle_exifmode(self, widget, data=None):
        iter_mode = self['combobox-exif'].get_active_iter()
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
            self['checkbutton-outgeo'].set_label(_("Geolocate photos in mode:"))
            self['combobox-exif'].set_active(default_pos)
        else:
            self['checkbutton-outgeo'].set_label(_("No geolocate photos"))
            self['combobox-exif'].set_sensitive(False)
            self.userfacade.state["exifmode"] = -1

    def _set_photouri(self, name=None):
        if name != None:
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

    def _adjust_timedelta(self, widget, data=None):
        value = widget.get_value()
        self.userfacade.state['maxdeltaseconds'] = int(value)

    def _adjust_toffset(self, widget, data=None):
        value = widget.get_value()
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
        color = TREEVIEWPHOTO_NORMAL_COLOR
        previews = geophoto.exif.previews
        largest = previews[-1]
        loader = gtk.gdk.PixbufLoader('jpeg')
        width, height = TREEVIEWPHOTO_PHOTOSIZE
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
        information = _("<b>%(name)s</b>\nDate: %(date)s\nTime: %(time)s") % dgettext
        if geophoto.toffset != 0:
            information += " (%+ds)" % geophoto.toffset
        geodata = ''
        geovalue = _("Picture not geotagged!")
        if geophoto.isGeoLocated():
            geodata = _("  Longitude :\n  Latitude :\n  Elevation :") % dgettext
            geovalue = "%(lon)f\n%(lat)f\n%(ele)f" % dgettext
            color = TREEVIEWPHOTO_GEOLOCATED_COLOR
        tips = tips % dgettext
        if geophoto.status > 1:
            geophoto.status = 1
            color = TREEVIEWPHOTO_CHANGED_COLOR
        if geophoto.attr:
            tips += _("# Attributes: \n")
            for k,v in geophoto.attr.iteritems():
                tips += "\t%s: %s\n" % (k, v)
        model = self["treeview-geophotos"].get_model()
        iterator = model.append(None, [
            geophoto.status, geophoto.name, geophoto.path, geophoto.time,
            bool(geophoto.status), pixbuf, information, geodata, geovalue, color, True, False, tips])
        self._set_geophoto_variables(model, iterator, geophoto)
        self["treeview-geophotos"].expand_row(model.get_path(iterator), True)

    def _set_geophoto_variables(self, model, iterator, geophoto):
        child_iter = model.iter_children(iterator)
        while child_iter != None:
            model.remove(child_iter)
            child_iter = model.iter_children(iterator)
        for variable in self.userfacade.state.kmldata.photo_variables:
            if not (variable in PhotoPlace_TEMPLATE_VARS):
                #( ... or variable in  self.userfacade.options['defaults']):
                try:
                    value = geophoto.attr[variable]
                except:
                    value = ''
                model.append(iterator, [
                    geophoto.status, variable, geophoto.path, None, bool(geophoto.status), None, None,
                    "<tt><b>%s</b></tt> :" % variable, value, None, False, True, _("Variable from template")])

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
                self.treeview_iterator = ite
                self.show_window_photoinfo(geophoto)
                #self.photoinfo_win.resize(1, 1)
                #self.photoinfo_win.show()
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


    # ######################################
    # Callbacks from notebook page Variables
    # ######################################

    def _show_variables(self, *args, **kwargs):
        model = self["treeview-variables"].get_model()
        model.clear()
        self.variables_iterator = model.append(None, [str(_("Main Parameters")), None, False])
        iterator_other = model.append(None, [str(_("Other Parameters")), None, False])
        for k, v in self.userfacade.options[VARIABLES_KEY].iteritems():
            if k in VARIABLES_OTHER:
                model.append(iterator_other, [str(k), str(v), True])
            else:
                if k == 'author' and not v:
                    v = getpass.getuser()
                    self.userfacade.options[VARIABLES_KEY][k] = v
                elif k == 'date' and not v:
                    v = datetime.date.today().strftime("%A %d. %B %Y")
                    self.userfacade.options[VARIABLES_KEY][k] = v
                model.append(self.variables_iterator, [str(k), str(v), True])
        # Templates
        self["treeview-variables"].expand_to_path((0))
        model = self["combobox-templates"].get_model()
        model.clear()
        for k, v in self.userfacade.options[TEMPLATES_KEY].iteritems():
            model.append([os.path.basename(v), k, v])

    def _add_variable(self, widget, key=None, value='_'):
        if key != None:
            lkey = key
        else:
            lkey = self['entry-variables-add'].get_text().strip()
        if lkey and not self.userfacade.options[VARIABLES_KEY].has_key(lkey):
            model = self["treeview-variables"].get_model()
            iterator = model.append(self.variables_iterator, [str(lkey), str(value), True])
            self.userfacade.options[VARIABLES_KEY][str(lkey)] = str(value)
            self['entry-variables-add'].set_text('')
            path = model.get_path(iterator)
            self["treeview-variables"].scroll_to_cell(path)
            treeselection = self["treeview-variables"].get_selection()
            treeselection.select_path(path)

    def _del_variable(self, widget):
        selection = self["treeview-variables"].get_selection()
        model, ite = selection.get_selected()
        if ite != None and model.get_value(ite, VARIABLES_COLUMN_EDITABLE):
            key = model.get_value(ite, VARIABLES_COLUMN_KEY)
            model.remove(ite)
            try:
                del self.userfacade.options[VARIABLES_KEY][key]
            except:
                pass

    def _edit_cell_variable(self, cell, path_string, new_text):
        model = self["treeview-variables"].get_model()
        treestore_iter = model.get_iter_from_string(path_string)
        key = model.get_value(treestore_iter, VARIABLES_COLUMN_KEY)
        if model.get_value(treestore_iter, VARIABLES_COLUMN_EDITABLE):
            self.userfacade.options[VARIABLES_KEY][key] = str(new_text)
            model.set(treestore_iter, VARIABLES_COLUMN_VALUE, str(new_text))

    def _clicked_template_edit(self, widget=None, data=None):
        ite = self['combobox-templates'].get_active_iter()
        template = self["combobox-templates"].get_model().get_value(ite, 2)
        self._load_template_file(None, template)
        dgettext = {'program': PhotoPlace_name, 'template': os.path.basename(template)}
        self.templates_win.set_title('%(program)s: Editing template <%(template)s>' % dgettext)
        self.templates_win.show()

    def _load_template_file(self, widget=None, template_file=None):
        self.popup = None
        if template_file == None:
            dialog = gtk.FileChooserDialog(title=_("Select file to load ..."),
                parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            ffilter = gtk.FileFilter()
            ffilter.set_name(_("All files"))
            ffilter.add_pattern("*")
            dialog.add_filter(ffilter)
            filename = None
            if dialog.run() == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
            dialog.destroy()
        else:
            filename = self.userfacade.get_filepath(template_file)
        self["statusbar-window-templates"].pop(0)
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            tbuffer = self["textbuffer-templates"]
            ite_end = tbuffer.get_iter_at_mark(tbuffer.get_insert())
            begin = True
            lines = 0
            for line in fd:
                for part in re.split(r"(%\([a-zA-Z0-9_\.]+\|?[a-zA-Z0-9 \?¿_.,:;=!@$&\-\+\*]*\).)", line):
                    if part.startswith('%('):
                        key = re.match(r"%\(([a-zA-Z0-9_\.]+)\|?.*\).", part).group(1)
                        if key in self.userfacade.options['defaults']:
                            tbuffer.insert_with_tags_by_name(ite_end, part, 'defaults')
                        elif key in PhotoPlace_TEMPLATE_VARS:
                            tbuffer.insert_with_tags_by_name(ite_end, part, 'photo')
                        else:
                            tbuffer.insert_with_tags_by_name(ite_end, part, 'attr')
                    else:
                        tbuffer.insert(ite_end, part)
                ite_end = tbuffer.get_iter_at_mark(tbuffer.get_insert())
                lines += 1
            # Delete last template div, if it exists!
            nline = lines
            while nline > 0:
                ite_nline = tbuffer.get_iter_at_line(nline)
                text = tbuffer.get_text(ite_nline, ite_end).strip()
                if text.startswith('</div>'):
                    tbuffer.delete(ite_nline, ite_end)
                    break
                elif len(text) > 1:
                    # Not a valid template
                    break
                else:
                    tbuffer.delete(ite_nline, ite_end)
                ite_end = ite_nline
                nline -= 1
            # Delete first template div, if it exists!
            ite_start = tbuffer.get_start_iter()
            nline = 0
            while nline <= lines:
                ite_nline = tbuffer.get_iter_at_line(nline)
                text = tbuffer.get_text(ite_start, ite_nline).strip()
                search = re.search(r'<div\s+mode=.(\w+).\s*>', text)
                if search:
                    tbuffer.delete(ite_start, ite_nline)
                    mode = search.group(1)
                    break
                elif len(text) > 1:
                    # Not a valid template
                    break
                else:
                    tbuffer.delete(ite_start, ite_nline)
                ite_start = ite_nline
                nline += 1
            self["statusbar-window-templates"].push(0,
                _("Template from file '%s' loaded") % os.path.basename(filename))
        except Exception as exception:
            self["statusbar-window-templates"].push(0, str(exception))
            return False
        finally:
            if fd != None:
                fd.close()
        return True

    def _save_wintemplate(self, widget=None):
        self["statusbar-window-templates"].pop(0)
        ite = self['combobox-templates'].get_active_iter()
        filename = self["combobox-templates"].get_model().get_value(ite, 2)
        start, end = self["textbuffer-templates"].get_bounds()
        filename = self["combobox-templates"].get_model().get_value(ite, 0)
        filename = os.path.join(self.userfacade.state.resourcedir_user, filename)
        template = self["textbuffer-templates"].get_text(start, end)
        fd = None
        error = False
        try:
            fd = codecs.open(filename, "w", encoding="utf-8")
            fd.write("<div mode='cdata'>\n")
            fd.write(template)
            fd.write("\n</div>\n")
        except Exception as exception:
            self["statusbar-window-templates"].push(0, str(exception))
            error = True
        finally:
            if fd != None:
                fd.close()
        if not error:
            # outside because loadtemplates open the file!
            if self.action_loadtemplates():
                model = self["treeview-geophotos"].get_model()
                iterator = model.get_iter_root()
                while iterator != None:
                    geophoto_path = model.get_value(iterator, TREEVIEWPHOTOS_COL_PATH)
                    for geophoto in self.userfacade.state.geophotos:
                        if geophoto.path == geophoto_path:
                            self._set_geophoto_variables(model, iterator, geophoto)
                            break
                    next = model.iter_next(iterator)
                    while next != None and  model.iter_parent(next) == iterator:
                        next = model.iter_next(next)
                    iterator = next
                self["treeview-geophotos"].expand_all()
                self["statusbar-window-templates"].push(0,
                    _('Template saved and reloaded without problems'))
            else:
                self["statusbar-window-templates"].push(0,
                    _('Error processing template'))

    def _key_press_wintemplate(self, textview, event):
        if self.popup != None:
            if event.keyval == gtk.gdk.keyval_from_name("Up"):
                self.popup.prev()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Down"):
                self.popup.next()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Return"):
                value = self.popup.confirm()
                tbuffer = self["textbuffer-templates"]
                end = tbuffer.get_iter_at_mark(tbuffer.get_insert())
                start = end.copy()
                start.backward_char()
                while start.get_char() not in " ,()[]<>|/\\\"\'\n\t":
                    start.backward_char()
                start.forward_char()
                tbuffer.delete(start, end)
                ite = tbuffer.get_iter_at_mark(tbuffer.get_insert())
                key = re.match(r"%\(([a-zA-Z0-9_\.]+)\|?.*]*\).", value).group(1)
                if key in self.userfacade.options['defaults']:
                    tbuffer.insert_with_tags_by_name(ite, value, 'defaults')
                elif key in PhotoPlace_TEMPLATE_VARS:
                    tbuffer.insert_with_tags_by_name(ite, value, 'photo')
                else:
                    tbuffer.insert_with_tags_by_name(ite, value, 'attr')
                self.popup = None
                return True
            else:
                self.popup.destroy()
                self.popup = None
        else:
            if event.keyval == gtk.gdk.keyval_from_name("space") \
            and event.state & gtk.gdk.CONTROL_MASK:
                return self.autocomplete_template_var(self["textbuffer-templates"])
            elif gtk.gdk.keyval_from_name("percent") == event.keyval:
                return self.autocomplete_template_var(self["textbuffer-templates"])
        return False

    def autocomplete_template_var(self, textbuffer):
        completions = []
        ite = self['combobox-templates'].get_active_iter()
        key = self["combobox-templates"].get_model().get_value(ite, 1)
        if key == 'kml.document.folder.placemark.description':
            for item in PhotoPlace_TEMPLATE_VARS:
                completions.append("%(" + item + ")s")
        for item in self.userfacade.options['defaults'].iterkeys():
            completions.append("%(" + item + "|)s")
        if len(completions) > 0:
            position = self.templates_win.window.get_root_origin()
            self.popup = TextViewCompleter(self["textview-templates"], position, completions)
            return True
        return False

    def _update_wintemplate_statusbar(self, textbuffer, *args, **kwargs):
        self["statusbar-window-templates"].pop(0)
        count = textbuffer.get_char_count()
        ite = textbuffer.get_iter_at_mark(textbuffer.get_insert())
        row = ite.get_line()
        col = ite.get_line_offset()
        dgettext = {}
        dgettext['line'] = row + 1
        dgettext['column'] = col
        dgettext['chars'] = count
        self["statusbar-window-templates"].push(0,
            _('Line %(line)d, column %(column)d (%(chars)d chars in document)') % dgettext)

    def _new_wintemplate(self, widget=None):
        self["statusbar-window-templates"].pop(0)
        start, end = self["textbuffer-templates"].get_bounds()
        self["textbuffer-templates"].delete(start, end)
        self["statusbar-window-templates"].push(0, _('New empty template'))

    def _recover_wintemplate(self, widget=None):
        self._new_wintemplate()
        ite = self['combobox-templates'].get_active_iter()
        filename = self["combobox-templates"].get_model().get_value(ite, 0)
        orig = filename
        resourcedir = self.userfacade.state.resourcedir
        language = locale.getdefaultlocale()[0]
        filename = os.path.join(resourcedir, TEMPLATES_KEY, language, orig)
        if not os.path.isfile(filename):
            language = language.split('_')[0]
            filename = os.path.join(resourcedir, TEMPLATES_KEY, language, orig)
            if not os.path.isfile(filename):
                filename = os.path.join(resourcedir, TEMPLATES_KEY, orig)
        if os.path.isfile(filename):
            if self._load_template_file(None, filename):
                self._save_wintemplate()
        else:
            self["statusbar-window-templates"].pop(0)
            self["statusbar-window-templates"].push(0, _('Cannot find system template!'))

    def _validate_wintemplate(self, widget=None):
        start, end = self["textbuffer-templates"].get_bounds()
        template = self["textbuffer-templates"].get_text(start, end)
        template = "<div mode='cdata'>\n" + template + "\n</div>"
        self["statusbar-window-templates"].pop(0)
        try:
            tdom = xml.dom.minidom.parseString(template)
            tdom.normalize()
        except Exception as exception:
            text = str(exception)
            line = re.search(r'line\s+(\d+)', text, re.IGNORECASE)
            if line:
                # correct line numbers ...
                pos = int(line.group(1)) - 1
                text = re.sub(r'(.+line )(\d+)(.+)', r"\1 %s\3" % pos, text)
                ins = self["textbuffer-templates"].get_iter_at_line(pos - 1)
                bound = self["textbuffer-templates"].get_iter_at_line(pos)
                self["textbuffer-templates"].select_range(ins, bound)
            self["statusbar-window-templates"].push(0, _('XML error: %s') % text)
        else:
            self["statusbar-window-templates"].push(0, _('Perfect! template is well formed!'))

    def _close_wintemplate(self, window, event=None):
        if self.popup != None:
            self.popup.destroy()
            self.popup = None
        self["textbuffer-templates"].set_text('')
        window.hide()
        return True


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
        model = self["treeview-geophotos"].get_model()
        self._set_geophoto_variables(model, self.treeview_iterator, self.current_geophoto)
        next = model.iter_next(self.treeview_iterator)
        while next != None and  model.iter_parent(next) == self.treeview_iterator:
            next = model.iter_next(next)
        if next != None:
            geophoto_path = model.get_value(next, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.treeview_iterator = next
                    self.show_window_photoinfo(geophoto)
                    return

    def _clicked_prev_photoinfo(self, widget=None, data=None):
        model = self["treeview-geophotos"].get_model()
        self._set_geophoto_variables(model, self.treeview_iterator, self.current_geophoto)
        path = model.get_path(self.treeview_iterator)
        position = path[0]
        if position != 0:
            prev_path = position - 1
            prev = model.get_iter(str(prev_path))
            geophoto_path = model.get_value(prev, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.treeview_iterator = prev
                    self.show_window_photoinfo(geophoto)
                    return

    def _show_photoinfo_attr(self, geophoto):
        model = self["treeview-photoinfo"].get_model()
        model.clear()
        dgettext = {'program': PhotoPlace_name, 'photo': geophoto['name']}
        self.photoinfo_win.set_title('%(program)s: Exif info of <%(photo)s>' % dgettext)
        color = TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR
        model.append(None,[False, False, str(_("Image name")), str(geophoto['name']), color])
        model.append(None,[False, False, str(_("Date/Time")), str(geophoto['time']), color])
        if geophoto.isGeoLocated():
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
        if model.get_value(ite, TREEVIEWPHOTOINFO_COL_EDIT):
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
            #self["entry-photoinfo-value"].set_text('')

    def _del_photoinfo_attr(self, widget):
        key = self["entry-photoinfo-key"].get_text().strip()
        if self.current_geophoto.attr.has_key(key):
            del  self.current_geophoto.attr[key]
            self._show_photoinfo_attr(self.current_geophoto)
        self["entry-photoinfo-key"].set_text('')
        self["entry-photoinfo-value"].set_text('')

    def _edit_cell_photoinfo(self, cell, path_string, new_text):
        model = self["treeview-photoinfo"].get_model()
        treestore_iter = model.get_iter_from_string(path_string)
        key = model.get_value(treestore_iter, TREEVIEWPHOTOINFO_COL_KEY)
        self.current_geophoto.attr[key] = str(new_text.strip())
        model.set(treestore_iter, TREEVIEWPHOTOINFO_COL_VALUE, new_text)

    def _close_winphotoinfo(self, window, event=None):
        model = self["treeview-geophotos"].get_model()
        self._set_geophoto_variables(model, self.treeview_iterator, self.current_geophoto)
        window.hide()
        return True


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
            self.current_geophoto = None
            self.treeview_iterator = None
            self["treeview-geophotos"].get_model().clear()
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
        try:
            geolocate = self.userfacade.Geolocate()
            if geolocate:
                geolocate.run()
            else:
                return False
        except Error as e:
            self.show_dialog(e.type, e.msg, e.tip)
            return False
        self["treeview-geophotos"].get_model().clear()
        self.num_photos_process = 0
        for geophoto in self.userfacade.state.geophotos:
            self._load_geophoto(geophoto)
            if geophoto.status > 0:
                self.num_photos_process += 1
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
                msg = _("No photos loaded, cannot do anything!.")
                tip = _("Select a directory with photos.")
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
