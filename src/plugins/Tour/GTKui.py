#! /usr/bin/env python

import os.path
import sys
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

# columns
(
    _GVariables_COLUMN_KEY,
    _GVariables_COLUMN_VALUE,
    _GVariables_COLUMN_EDITABLE,
) = range(3)



class GTKTour(object):

    def __init__(self, gtkbuilder):
        object.__init__(self)
        self.plugin = gtk.VBox(False)
        # 1st line
        hbox_name = gtk.HBox(False)
        label_name = gtk.Label()
        label_name.set_markup(_("Name :"))
        hbox_name.pack_start(label_name, False, False, 5)
        self.entry_name = gtk.Entry(max=256)
        self.entry_name.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_NAME)
        hbox_name.pack_start(self.entry_name, False, False)
        hbox_desc = gtk.HBox(False)
        label_desc = gtk.Label()
        label_desc.set_markup(_("Description :"))
        hbox_desc.pack_start(label_desc, False, False, 5)
        self.entry_desc = gtk.Entry(max=1024)
        self.entry_desc.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_DESC)
        hbox_desc.pack_start(self.entry_desc, True, True)
        hbox_name.pack_start(hbox_desc, True, True, 10)
        self.button_advanced = gtk.Button(_('Advanced'), gtk.STOCK_PROPERTIES)
        #self.button_advanced.connect('clicked', self._add_music)
        hbox_name.pack_start(self.button_advanced, False, False, 5)
        self.plugin.pack_start(hbox_name, False, False)
        # 2nd line
        hbox_text = gtk.HBox(True)
        vbox_ini = gtk.VBox(False)
        label_ini = gtk.Label()
        label_ini.set_markup(_("Type the presentation text ... "))
        label_ini.set_justify(gtk.JUSTIFY_LEFT)
        label_ini.set_alignment(0.0, 0.5)
        vbox_ini.pack_start(label_ini, False, False)
        frame_ini = gtk.Frame()
        sw_ini = gtk.ScrolledWindow()
        sw_ini.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview_ini = gtk.TextView()
        sw_ini.add(self.textview_ini)
        frame_ini.add(sw_ini)
        frame_ini.set_size_request(-1, 42)
        vbox_ini.pack_start(frame_ini, True, True, 5)
        hbox_ini = gtk.HBox(False)
        label_ini_text = gtk.Label()
        label_ini_text.set_markup(_("... or load it from"))
        label_ini_text.set_justify(gtk.JUSTIFY_LEFT)
        hbox_ini.pack_start(label_ini_text, False, False)
        self.filechooserbutton_ini = gtk.Button(_('(select file)'))
        self.filechooserbutton_ini.connect('clicked', 
            self._load_file, self.textview_ini, KmlTour_CONFKEY_BEGIN_PLCMK)
        hbox_ini.pack_start(self.filechooserbutton_ini, True, True, 10)
        vbox_ini.pack_start(hbox_ini, False, False)
        hbox_text.pack_start(vbox_ini, True, True, 5)
        # Right
        vbox_end = gtk.VBox(False)
        label_end = gtk.Label()
        label_end.set_markup(_("Ending text ... "))
        label_end.set_justify(gtk.JUSTIFY_LEFT)
        label_end.set_alignment(0.0, 0.5)
        vbox_end.pack_start(label_end, False, False)
        frame_end = gtk.Frame()
        sw_end = gtk.ScrolledWindow()
        sw_end.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview_end = gtk.TextView()
        sw_end.add(self.textview_end)
        frame_end.add(sw_end)
        frame_end.set_size_request(-1, 42)
        vbox_end.pack_start(frame_end, True, True, 5)
        hbox_end = gtk.HBox(False)
        label_end_text = gtk.Label()
        label_end_text.set_markup(_("... or load it from"))
        label_end_text.set_justify(gtk.JUSTIFY_LEFT)
        hbox_end.pack_start(label_end_text, False, False)
        self.filechooserbutton_end = gtk.Button(_('(select file)'))
        self.filechooserbutton_end.connect('clicked', 
            self._load_file, self.textview_end, KmlTour_CONFKEY_END_PLCMK)
        hbox_end.pack_start(self.filechooserbutton_end, True, True, 10)
        vbox_end.pack_start(hbox_end, False, False)
        hbox_text.pack_start(vbox_end, True, True, 5)
        self.plugin.pack_start(hbox_text, True, True, 10)
        # Music buttons
        hbox_music = gtk.HBox(False)
        label_music = gtk.Label()
        label_music.set_markup(_("Music :"))
        hbox_music.pack_start(label_music, False, False, 5)
        self.combobox_mp3 = gtk.combo_box_new_text()
        hbox_music.pack_start(self.combobox_mp3, True, True, 5)
        self.button_music_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.button_music_add.connect('clicked', self._add_music)
        hbox_music.pack_start(self.button_music_add, False, False, 5)
        self.button_music_del = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.button_music_del.connect('clicked', self._del_music)
        hbox_music.pack_start(self.button_music_del, False, False, 5)
        self.button_music_mix = gtk.CheckButton(_("Mix"))
        self.button_music_mix.connect('toggled', self._set_mix)
        hbox_music.pack_start(self.button_music_mix, False, False, 5)
        hbox_music_uri = gtk.HBox(False)
        label_uri = gtk.Label()
        label_uri.set_markup(_("URI :"))
        hbox_music_uri.pack_start(label_uri, False, False, 5)
        self.entry_uri = gtk.Entry(max=256)
        self.entry_uri.connect('changed', self._set_entry, KmlTour_CONFKEY_KMLTOUR_MUSIC_URI)
        hbox_music_uri.pack_start(self.entry_uri, False, False)
        hbox_music.pack_start(hbox_music_uri, False, False, 10)
        self.plugin.pack_start(hbox_music, False, False, 10)
        # Parametres
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create model
        self.treestore = gtk.TreeStore(str, str, bool)
        # create tree view
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_rules_hint(True)
        self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        # columns
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Name"), renderer, text=_GVariables_COLUMN_KEY)
        column.set_resizable(True)
        column.set_sort_column_id(_GVariables_COLUMN_KEY)
        self.treeview.append_column(column)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._edit_cell)
        column = gtk.TreeViewColumn(_("Value"), renderer, 
            text=_GVariables_COLUMN_VALUE, editable=_GVariables_COLUMN_EDITABLE)
        column.set_resizable(True)
        column.set_sort_column_id(_GVariables_COLUMN_VALUE)
        self.treeview.append_column(column)
        scroll.add(self.treeview)
        #self.plugin.pack_start(scroll, True, True)
        #
        self.options = None
        self.window = gtkbuilder.get_object("window")


    def show(self, widget=None, options=None):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options)
        self.plugin.show_all()


    def hide(self):
        self.plugin.hide_all()


    def get_placemark(self, key):
        textbuffer = textview.get_buffer()
        textbuffer.get_text(0, -1)


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
        if filename and os.path.isfile(filename):
            try:
                self._set_textview(textview, filename)
            except:
                pass
            else:
                self.options[key] = str(filename)
                widget.set_label(os.path.basename(filename))


    def setup(self, options):
        self.entry_name.set_text(options[KmlTour_CONFKEY_KMLTOUR_NAME])
        self.entry_desc.set_text(options[KmlTour_CONFKEY_KMLTOUR_DESC])
        filename = options[KmlTour_CONFKEY_BEGIN_PLCMK]
        try:
            self._set_textview(self.textview_ini, filename)
        except:
            pass
        else:
            self.filechooserbutton_ini.set_filename(filename)
        filename = options[KmlTour_CONFKEY_END_PLCMK]
        try:
            self._set_textview(self.textview_end, filename)
        except:
            pass
        else:
            self.filechooserbutton_end.set_filename(filename)
        for mp3 in options[KmlTour_CONFKEY_KMLTOUR_MUSIC]:
            self.combobox_mp3.append_text(os.path.basename(mp3))
        self.button_music_mix.set_active(options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX])
        self.entry_uri.set_text(options[KmlTour_CONFKEY_KMLTOUR_MUSIC_URI])
        self.options = options


    def _set_textview(self, textview, filename, wrap=gtk.WRAP_NONE):
        try:
            fd = open(filename, "r")
            textview.set_wrap_mode(wrap)
            textbuffer = textview.get_buffer()
            textbuffer.set_text(fd.read())
        except:
            raise
        finally:
            if fd:
                fd.close()


    def get_textview(self, key):
        if key == KmlTour_CONFKEY_BEGIN_DESC:
            textview = self.textview_end
        elif key == KmlTour_CONFKEY_END_DESC:
            textview = self.textview_ini
        else:
            textview = None
        if textview:
            textbuffer = textview.get_buffer()
            start, end = textbuffer.get_bounds()
            return textbuffer.get_text(start, end)
        return ''


    def _add_music(self, widget, *args, **kwargs):
        dialog = gtk.FileChooserDialog(title=_("Select MP3 files ..."), 
            parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
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
        if filename and os.path.isfile(filename):
            self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC].append(str(filename))
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


    def _set_mix(self, widget, *args, **kwargs):
        value = widget.get_active()
        self.options[KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX] = value




    def _edit_cell(self, cell, path_string, new_text):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GVariables_COLUMN_KEY)
        editable = self.treestore.get_value(treestore_iter, _GVariables_COLUMN_EDITABLE)
        if editable:
            if key == KmlTour_CONFKEY_KMLTOUR_NAME \
            or key == KmlTour_CONFKEY_KMLTOUR_DESC \
            or key == KmlTour_CONFKEY_KMLTOUR_MUSIC_URI :
                self.options[key] = new_text
                self.treestore.set(treestore_iter, _GVariables_COLUMN_VALUE, str(new_text))
            elif key == KmlTour_CONFKEY_KMLTOUR_MUSIC_MIX :
                value = new_text.lower().strip() in ["yes", "true", "1", "si"]
                self.button_music_mix.set_active(value)
            elif key == KmlTour_CONFKEY_BEGIN_PLCMK:
                self._set_textview(self.textview_ini, new_text)
                self.options[key] = new_text
                self.filechooserbutton_ini.set_filename(new_text)
                self.treestore.set(treestore_iter, _GVariables_COLUMN_VALUE, str(new_text))
            elif key == KmlTour_CONFKEY_END_PLCMK:
                self._set_textview(self.textview_end, new_text)
                self.options[key] = new_text
                self.filechooserbutton_end.set_filename(new_text)
                self.treestore.set(treestore_iter, _GVariables_COLUMN_VALUE, str(new_text))
            else:
                try:
                    new = float(new_text)
                    self.options[key] = new
                    self.treestore.set(treestore_iter, _GVariables_COLUMN_VALUE, str(new))
                except:
                    pass








