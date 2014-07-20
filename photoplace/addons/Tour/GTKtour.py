#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKtour.py
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
This add-on makes a visual tour with all photos ....
"""
__program__ = "photoplace.tour"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0self.cos_max_diff_corner"
__date__ = "August 2012"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import codecs
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

from tour import *


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, u"locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    #gettext.bindtextdomain(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)


# columns
(
    _KmlTour_COLUMN_KEY,
    _KmlTour_COLUMN_VALUE,
    _KmlTour_COLUMN_EDITABLE,
) = range(3)



class GTKTour(object):

    def __init__(self, gui, logger):
        object.__init__(self)
        self.logger = logger
        self.plugin = gtk.VBox(False)
        # 1st line
        hbox_name = gtk.HBox(False)
        label_name = gtk.Label()
        label_name.set_markup(_("Name:"))
        label_name.set_tooltip_text(_("Tour's name"))
        hbox_name.pack_start(label_name, False, False, 5)
        self.entry_name = gtk.Entry(max=256)
        self.entry_name.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_NAME)
        hbox_name.pack_start(self.entry_name, False, False)
        hbox_desc = gtk.HBox(False)
        label_desc = gtk.Label()
        label_desc.set_markup(_("Description:"))
        label_desc.set_tooltip_text(_("A short description"))
        hbox_desc.pack_start(label_desc, False, False, 5)
        self.entry_desc = gtk.Entry(max=1024)
        self.entry_desc.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_DESC)
        hbox_desc.pack_start(self.entry_desc, True, True)
        #hbox_name.pack_start(hbox_desc, True, True, 10)
        hbox_follow = gtk.HBox(False)
        self.button_follow_path = gtk.CheckButton(_("Follow path with simpl. factor:"))
        self.button_follow_path.set_tooltip_text(
            _("If it is active, the tour will follow GPS tracks. "
            "It does not change the current value in the photos: "
            "if photos are loaded without 'follow path', the parameter "
            "will not be setted up for those photos."))
        self.button_follow_path.connect('toggled', self._set_follow)
        hbox_follow.pack_start(self.button_follow_path, False, False, 5)
        self.adjustment_epsilon = gtk.Adjustment(0, -1, 100000, 3.0, 2.0, 0.0)
        self.spinbutton_epsilon = gtk.SpinButton(self.adjustment_epsilon, 0.0, 0)
        self.spinbutton_epsilon.set_tooltip_text(
            _("Maximum tolerance in meters to determine if a point of track will "
            "be used in the tour. If it is 0, all waypoints of the original track "
            "will be followed, with -1, the value will be automatically estimated."))
        self.spinbutton_epsilon.set_numeric(True)
        self.adjustment_epsilon.connect("value_changed", self._set_epsilon)
        hbox_follow.pack_start(self.spinbutton_epsilon, False, False)
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(hbox_follow)
        hbox_name.pack_start(align, True, True)
        self.button_advanced = gtk.Button(_('Advanced'), gtk.STOCK_PROPERTIES)
        self.button_advanced.connect('clicked', self.show_properties)
        hbox_name.pack_start(self.button_advanced, False, False, 5)
        self.plugin.pack_start(hbox_name, False, False)
        # 2nd line
        hbox_first_last = gtk.HBox(True)
        self.button_from_first_photo = gtk.CheckButton(_("Start tour from first geotagged photo"))
        self.button_from_first_photo.set_tooltip_text(
            _("If it is active, the tour will start with the first geotagged photo, without presentation."))
        self.button_from_first_photo.connect('toggled', self._set_first_photo)
        hbox_first_last.pack_start(self.button_from_first_photo, False, True, 5)
        self.button_to_last_photo = gtk.CheckButton(_("End up tour with last geotagged photo"))
        self.button_to_last_photo.set_tooltip_text(
            _("If it is active, the tour will end up with the last geotagged photo, without ending."))
        self.button_to_last_photo.connect('toggled', self._set_last_photo)
        hbox_first_last.pack_start(self.button_to_last_photo, False, True, 5)
        self.plugin.pack_start(hbox_first_last, False, False, 10)
        # 3rd line
        tooltip_text = _("You can use simple HTML tags like "
            "list (<i>li</i>, <i>ul</i>) or <i>table</i> and use expresions "
            "like <span font_family='monospace' size='small'>"
            "<b>%(<i>variable</i>)s</b></span> "
            "where <i>variable</i> is a key defined in the "
            "<b>Variables</b> section.")
        hbox_text = gtk.HBox(True)
        vbox_ini = gtk.VBox(False)
        self.label_ini = gtk.Label()
        self.label_ini.set_markup(_("Presentation at the beginning of path:"))
        self.label_ini.set_justify(gtk.JUSTIFY_LEFT)
        self.label_ini.set_alignment(0.0, 0.5)
        vbox_ini.pack_start(self.label_ini, False, False)
        frame_ini = gtk.Frame()
        sw_ini = gtk.ScrolledWindow()
        sw_ini.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview_ini = gtk.TextView()
        self.textview_ini.set_tooltip_markup(tooltip_text +
            _("\n\nIf empty no description will appear at the beginning of path."))
        self.textview_ini.connect('populate-popup', self._lclicked_textview, KmlTour_CONFKEY_BEGIN_DESC)
        sw_ini.add(self.textview_ini)
        frame_ini.add(sw_ini)
        #frame_ini.set_size_request(-1, 42)
        vbox_ini.pack_start(frame_ini, True, True)
        hbox_text.pack_start(vbox_ini, True, True, 5)
        # Right
        vbox_end = gtk.VBox(False)
        self.label_end = gtk.Label()
        self.label_end.set_markup(_("Ending text at the end of path:"))
        self.label_end.set_justify(gtk.JUSTIFY_LEFT)
        self.label_end.set_alignment(0.0, 0.5)
        vbox_end.pack_start(self.label_end, False, False)
        frame_end = gtk.Frame()
        sw_end = gtk.ScrolledWindow()
        sw_end.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview_end = gtk.TextView()
        self.textview_end.set_tooltip_markup(tooltip_text +
            _("\n\nIf empty no description will appear at the end of path."))
        self.textview_end.connect('populate-popup', self._lclicked_textview, KmlTour_CONFKEY_END_DESC)
        sw_end.add(self.textview_end)
        frame_end.add(sw_end)
        #frame_end.set_size_request(-1, 42)
        vbox_end.pack_start(frame_end, True, True)
        hbox_text.pack_start(vbox_end, True, True, 5)
        self.plugin.pack_start(hbox_text, True, True, 0)
        # Music buttons
        hbox_music = gtk.HBox(False)
        label_music = gtk.Label()
        label_music.set_markup(_("Music:"))
        hbox_music.pack_start(label_music, False, False, 5)
        self.combobox_mp3 = gtk.combo_box_new_text()
        hbox_music.pack_start(self.combobox_mp3, True, True, 5)
        self.button_music_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.button_music_add.set_tooltip_text(
            _("Add a mp3 file to list"))
        self.button_music_add.connect('clicked', self._add_music)
        hbox_music.pack_start(self.button_music_add, False, False, 5)
        self.button_music_del = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.button_music_del.set_tooltip_text(
            _("Delete the mp3 file selected in the combobox"))
        self.button_music_del.connect('clicked', self._del_music)
        hbox_music.pack_start(self.button_music_del, False, False, 5)
        self.button_music_mix = gtk.CheckButton(_("Mix"))
        self.button_music_mix.set_tooltip_text(
            _("Mix all mp3? If yes, it will sound all mp3's at the same time"))
        self.button_music_mix.connect('toggled', self._set_mix)
        hbox_music.pack_start(self.button_music_mix, False, False, 5)
        hbox_music_uri = gtk.HBox(False)
        label_uri = gtk.Label()
        label_uri.set_markup(_("URI:"))
        hbox_music_uri.pack_start(label_uri, False, False, 5)
        self.entry_uri = gtk.Entry(max=256)
        self.entry_uri.set_tooltip_text(_("URI to reference all mp3's. "
            "If you generate a KML for the web, this parameter will set the "
            "path where the files are."))
        self.entry_uri.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_MUSIC_URI)
        hbox_music_uri.pack_start(self.entry_uri, False, False)
        hbox_music.pack_start(hbox_music_uri, False, False, 10)
        self.plugin.pack_start(hbox_music, False, False, 10)
        # create model for parameters
        self.treestore = gtk.TreeStore(str, str, bool)
        self.options = None
        self.window = gui.builder.get_object("window")


    def show(self, widget=None, options=None):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options)
        self.plugin.show_all()


    def hide(self):
        self.plugin.hide_all()


    def _set_first_photo(self, widget, data=None):
        value = widget.get_active()
        self.textview_ini.set_sensitive(not value)
        self.label_ini.set_sensitive(not value)
        if self.options:
            self.options[KmlTour_CONFKEY_KMLTOUR_FIRST_PHOTO] = value


    def _set_last_photo(self, widget, data=None):
        value = widget.get_active()
        self.textview_end.set_sensitive(not value)
        self.label_end.set_sensitive(not value)
        if self.options:
            self.options[KmlTour_CONFKEY_KMLTOUR_LAST_PHOTO] = value


    def get_placemark(self, key):
        textbuffer = textview.get_buffer()
        start, end = textbuffer.get_bounds()
        textbuffer.get_text(start, end)


    def _set_entry(self, widget, key):
        try:
            self.options[key] = widget.get_text()
        except:
            pass


    def _load_file(self, widget, textview, key):
        dialog = gtk.FileChooserDialog(title=_("Select text file ..."),
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
        if filename != None and os.path.isfile(filename):
            try:
                self._set_textview(textview, filename)
            except:
                pass
            else:
                self.options[key] = filename


    def setup(self, options):
        self.options = None
        self.entry_name.set_text(options[KmlTour_CONFKEY_KMLTOUR_NAME])
        self.entry_desc.set_text(options[KmlTour_CONFKEY_KMLTOUR_DESC])
        filename = options[KmlTour_CONFKEY_BEGIN_DESC]
        try:
            if filename == None:
                raise UserWarning
            self._set_textview(self.textview_ini, filename)
        except:
            self.textview_ini.get_buffer().set_text(KmlTour_BEGIN_DESC)
        filename = options[KmlTour_CONFKEY_END_DESC]
        try:
            if filename == None:
                raise UserWarning
            self._set_textview(self.textview_end, filename)
        except:
            self.textview_end.get_buffer().set_text(KmlTour_END_DESC)
        for mp3 in options[KmlTour_CONFKEY_KMLTOUR_MUSIC]:
            self.combobox_mp3.append_text(os.path.basename(mp3))
        else:
            self.combobox_mp3.set_active(0)
        self.button_music_mix.set_active(options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX])
        self.entry_uri.set_text(options[KmlTour_CONFKEY_KMLTOUR_MUSIC_URI])
        follow_value = options[KmlTour_CONFKEY_FOLLOWPATH]
        self.button_follow_path.set_active(follow_value)
        self.spinbutton_epsilon.set_sensitive(follow_value)
        value = options[KmlTour_CONFKEY_KMLTOUR_FIRST_PHOTO]
        self.textview_ini.set_sensitive(not value)
        self.label_ini.set_sensitive(not value)
        self.button_from_first_photo.set_active(value)
        value = options[KmlTour_CONFKEY_KMLTOUR_LAST_PHOTO]
        self.textview_end.set_sensitive(not value)
        self.label_end.set_sensitive(not value)
        self.button_to_last_photo.set_active(value)
        self.options = options
        self.adjustment_epsilon.set_value(options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE])


    def _lclicked_textview(self, widget, menu, key):
        menu_load = gtk.ImageMenuItem(gtk.STOCK_FILE)
        menu_load.set_property('label', _("Load content from a file"))
        menu_load.connect("activate", self._load_file, widget, key)
        menu_separator = gtk.SeparatorMenuItem()
        menu.prepend(menu_separator)
        menu.prepend(menu_load)
        menu.show_all()


    def _set_textview(self, textview, filename, bytes=102400, wrap=gtk.WRAP_NONE):
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            textview.set_wrap_mode(wrap)
            textbuffer = textview.get_buffer()
            textbuffer.set_text(fd.read(bytes))
        except Exception as exception:
            dgettext = {'file': filename, 'error': str(exception)}
            self.logger.error(_("Cannot read file '%(file)s': %(error)s.") % dgettext)
            raise
        finally:
            if fd:
                fd.close()


    def get_textview(self, key):
        if key == KmlTour_CONFKEY_BEGIN_DESC:
            textview = self.textview_ini
        elif key == KmlTour_CONFKEY_END_DESC:
            textview = self.textview_end
        else:
            return ''
        textbuffer = textview.get_buffer()
        start, end = textbuffer.get_bounds()
        return textbuffer.get_text(start, end)


    def _add_music(self, widget, *args, **kwargs):
        dialog = gtk.FileChooserDialog(_("Select MP3 files ..."),
            self.window, gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("MP3 files"))
        ffilter.add_mime_type("audio/x-mp3")
        ffilter.add_pattern("*.mp3")
        dialog.add_filter(ffilter)
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("All files"))
        ffilter.add_pattern("*")
        dialog.add_filter(ffilter)
        filename = None
        if dialog.run() == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename != None and os.path.isfile(filename):
            self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC].append(filename)
            self.combobox_mp3.append_text(os.path.basename(filename))
            self.combobox_mp3.set_active(0)


    def _del_music(self, widget, *args, **kwargs):
        model = self.combobox_mp3.get_model()
        active = self.combobox_mp3.get_active()
        if active >= 0:
            filename = model[active][0]
            counter = 0
            for mp3 in self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC]:
                if os.path.basename(mp3) == filename:
                    found = True
                    break
                counter += 1
            if found:
                del self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC][counter]
                self.combobox_mp3.remove_text(active)
        self.combobox_mp3.set_active(0)


    def _set_epsilon(self, widget):
        value = self.adjustment_epsilon.get_value()
        self.options[KmlTour_CONFKEY_KMLTOUR_SIMPL_DISTANCE] = float(value)


    def _set_mix(self, widget, data):
        if self.options:
            value = widget.get_active()
            self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX] = value


    def _set_follow(self, widget, data=None):
        value = widget.get_active()
        self.spinbutton_epsilon.set_sensitive(value)
        if self.options:
            self.options[KmlTour_CONFKEY_FOLLOWPATH] = value
            # Hei!, it does not change the current value in the photos


    def show_properties(self, widget=None, height=500, width=300):
        dialog = gtk.Dialog(_('PhotoPlace: Tour parameters'), self.window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))
        vbox = dialog.get_content_area()
        # Parameters
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create tree view
        treeview = gtk.TreeView(self.treestore)
        treeview.set_rules_hint(True)
        treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        # columns
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Name"), renderer, text=_KmlTour_COLUMN_KEY)
        column.set_resizable(True)
        column.set_sort_column_id(_KmlTour_COLUMN_KEY)
        treeview.append_column(column)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._edit_cell)
        column = gtk.TreeViewColumn(_("Value"), renderer,
            text=_KmlTour_COLUMN_VALUE, editable=_KmlTour_COLUMN_EDITABLE)
        column.set_resizable(True)
        column.set_sort_column_id(_KmlTour_COLUMN_VALUE)
        treeview.append_column(column)
        scroll.add(treeview)
        vbox.pack_start(scroll, True, True)
        vbox.show_all()
        self.treestore.clear()
        ite = self.treestore.append(None, [str(_("Default Camera Parameters")), None, False])
        self.treestore.append(ite, [KmlTour_CONFKEY_KMLTOUR_RANGE_MAX,
            self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MAX] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_KMLTOUR_RANGE_MIN,
            self.options[KmlTour_CONFKEY_KMLTOUR_RANGE_MIN] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_KMLTOUR_TILT_MAX,
            self.options[KmlTour_CONFKEY_KMLTOUR_TILT_MAX] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_KMLTOUR_TILT_MIN,
            self.options[KmlTour_CONFKEY_KMLTOUR_TILT_MIN] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_FLYTIME,
            self.options[KmlTour_CONFKEY_FLYTIME], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_HEADING,
            self.options[KmlTour_CONFKEY_HEADING], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_RANGE,
            self.options[KmlTour_CONFKEY_RANGE], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_TILT,
            self.options[KmlTour_CONFKEY_TILT], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_WAIT,
            self.options[KmlTour_CONFKEY_WAIT], True])
        ite = self.treestore.append(None, [str(_("Start Camera Parameters")), None, False])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_DESC,
            self.options[KmlTour_CONFKEY_BEGIN_DESC] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_STYLE,
            self.options[KmlTour_CONFKEY_BEGIN_STYLE], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_FLYTIME,
            self.options[KmlTour_CONFKEY_BEGIN_FLYTIME], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_HEADING,
            self.options[KmlTour_CONFKEY_BEGIN_HEADING], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_RANGE,
            self.options[KmlTour_CONFKEY_BEGIN_RANGE], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_TILT,
            self.options[KmlTour_CONFKEY_BEGIN_TILT], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_BEGIN_WAIT,
            self.options[KmlTour_CONFKEY_BEGIN_WAIT], True])
        ite = self.treestore.append(None, [str(_("End Camera Parameters")), None, False])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_DESC,
            self.options[KmlTour_CONFKEY_END_DESC] , True])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_STYLE,
            self.options[KmlTour_CONFKEY_END_STYLE], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_FLYTIME,
            self.options[KmlTour_CONFKEY_END_FLYTIME], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_HEADING,
            self.options[KmlTour_CONFKEY_END_HEADING], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_RANGE,
            self.options[KmlTour_CONFKEY_END_RANGE], True])
        self.treestore.append(ite, [KmlTour_CONFKEY_END_TILT,
            self.options[KmlTour_CONFKEY_END_TILT], True])
        treeview.expand_all()
        dialog.resize(height, width)
        dialog.run()
        dialog.destroy()


    def _edit_cell(self, cell, path_string, new_text):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _KmlTour_COLUMN_KEY)
        editable = self.treestore.get_value(treestore_iter, _KmlTour_COLUMN_EDITABLE)
        if editable:
            if key == KmlTour_CONFKEY_BEGIN_DESC \
            or key == KmlTour_CONFKEY_BEGIN_STYLE \
            or key == KmlTour_CONFKEY_END_DESC \
            or key == KmlTour_CONFKEY_END_STYLE:
                self.options[key] = new_text
                self.treestore.set(treestore_iter, _KmlTour_COLUMN_VALUE, str(new_text))
            else:
                try:
                    new = float(new_text)
                    self.options[key] = new
                    self.treestore.set(treestore_iter, _KmlTour_COLUMN_VALUE, str(new))
                except:
                    pass


# EOF

