#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKPaths.py
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
A plugin for PhotoPlace to generate paths from GPX tracks to show them in the KML layer.
GTK User Interface.
"""
__program__ = "photoplace.paths"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.3.1"
__date__ = "December 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import StringIO
import codecs
import warnings
import gettext
import locale

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

from paths import *
from PhotoPlace.UserInterface.GTKUI import TextViewCompleter


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

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
    _GTKPaths_COLUMN_ACT,
    _GTKPaths_COLUMN_VIS,
    _GTKPaths_COLUMN_KEY,
    _GTKPaths_COLUMN_VKEY,
    _GTKPaths_COLUMN_VALUE,
    _GTKPaths_COLUMN_DESC,
    _GTKPaths_COLUMN_FILE,
    _GTKPaths_COLUMN_EDITKEY,
    _GTKPaths_COLUMN_EDITVAL,
    _GTKPaths_COLUMN_CLICK,
    _GTKPaths_COLUMN_FAMILY,
) = range(11)

_GTKPaths_DESCRIPTION_CHARS = 45
_GTKPaths_DEFAULT_FAMILY = None
_GTKPaths_DESC_FAMILY = "Monospace"



class CellRendererTextClick(gtk.CellRendererText):

    __gproperties__ = {
        'clickable': (gobject.TYPE_BOOLEAN, 'clickable', 'is clickable?',
            False, gobject.PARAM_READWRITE),
    }

    def __init__(self):
        gtk.CellRendererText.__init__(self)
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



class GTKPaths(object):

    def __init__(self, gtkbuilder, state, logger):
        object.__init__(self)
        self.options = None
        self.goptions = None
        self.tracksinfo = None
        self.tracknum = 0
        self.photopaths = 0
        self.photodirlist = None
        self.state = state
        self.logger = logger
        self.plugin = gtk.VBox(False)
        # 1st line
        self.checkbutton_genpath = gtk.CheckButton(
            _("Generate a path from geotagged photos"))
        self.checkbutton_genpath.connect('toggled', self.photo_path)
        self.plugin.pack_start(self.checkbutton_genpath, False, False, 10)
        # Parameters
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create model for parameters
        self.treestore = gtk.TreeStore(
            bool, bool, str, str, str, str, str, bool, bool, bool, str)
        treeview = gtk.TreeView(self.treestore)
        treeview.set_rules_hint(True)
        treeview.set_tooltip_text(_("Double click to edit these values ..."))
        treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        # columns
        renderer = gtk.CellRendererToggle()
        renderer.set_radio(True)
        renderer.connect('toggled', self._toggled_track)
        column = gtk.TreeViewColumn(None, renderer, 
            active=_GTKPaths_COLUMN_ACT,
            visible=_GTKPaths_COLUMN_VIS)
        treeview.append_column(column)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._edit_cell, KmlPaths_CONFKEY_TRACKS_NAME)
        column = gtk.TreeViewColumn(_("Path Name/Parameter"), renderer,
            text=_GTKPaths_COLUMN_VKEY,
            editable=_GTKPaths_COLUMN_EDITKEY)
        column.set_resizable(True)
        treeview.append_column(column)
        treeview.set_expander_column(column)
        renderer = CellRendererTextClick()
        renderer.connect('editing-started', self._edit_value)
        renderer.connect('edited', self._edit_cell, KmlPaths_CONFKEY_TRACKS_DESC)
        column = gtk.TreeViewColumn(_("Description/Value"), renderer,
            text=_GTKPaths_COLUMN_VALUE,
            editable=_GTKPaths_COLUMN_EDITVAL,
            clickable=_GTKPaths_COLUMN_CLICK,
            family=_GTKPaths_COLUMN_FAMILY)
        column.set_resizable(True)
        treeview.append_column(column)
        scroll.add(treeview)
        self.plugin.pack_start(scroll, True, True)
        self.window = gtkbuilder.get_object("window")


    def show(self, widget=None, options=None, tracks=None, goptions=None, photodirlist=[]):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options, tracks, goptions)
        self.photodirlist = photodirlist
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
        self.tracknum = 0
        self.photopaths = 0


    def clear_tracks(self):
        ite = self.treestore.get_iter_first()
        if ite and self.options[KmlPaths_CONFKEY_KMLPATH_GENTRACK]:
            counter = 0
            while counter != self.photopaths:
                ite = self.treestore.iter_next(ite)
                counter += 1
        deleted = []
        while ite:
            deleted.insert(0, ite)
            ite = self.treestore.iter_next(ite)
        for ite in deleted:
            self.treestore.remove(ite)
        self.tracknum = 0


    def photo_path(self, widget=None, newtrackname=None):
        if self.state['photoinputdir'] and self.options:
            self.options[KmlPaths_CONFKEY_KMLPATH_GENTRACK] = \
                self.checkbutton_genpath.get_active()
            if self.options[KmlPaths_CONFKEY_KMLPATH_GENTRACK]:
                if newtrackname != None:
                    self.add_track(newtrackname, KmlPaths_KMLPATH_GENDESC, 0)
                    self.photopaths += 1
                else:
                    position = len(self.photodirlist) - 1
                    while position >= 0:
                        name = self.photodirlist[position][0]
                        self.add_track(name, KmlPaths_KMLPATH_GENDESC, 0)
                        self.photopaths += 1
                        position -= 1
            else:
                while self.photopaths != 0:
                    self.treestore.remove(self.treestore.get_iter_root())
                    self.tracknum -= 1
                    self.photopaths -= 1


    def _toggled_track(self, widget, path_string):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        value = self.treestore.get_value(treestore_iter, _GTKPaths_COLUMN_ACT)
        value = not value
        self.treestore.set(treestore_iter, _GTKPaths_COLUMN_ACT, value)
        position = int(path_string)
        if position < self.photopaths:
            name, active = self.photodirlist[position]
            self.photodirlist[position] = (name, value)
        else:
            position -= self.photopaths
            self.state.gpxdata.tracks[position].status = int(value)


    def _set_entry(self, widget, key):
        try:
            self.options[key] = widget.get_text()
        except:
            pass


    def get_description(self, filename, bytes=102400):
        description = ''
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            description = fd.read(bytes)
        except Exception as e:
            self.logger.error(_("Cannot read file '%s'.") % str(e))
        finally:
            if fd != None:
                fd.close()
        return description


    def setup(self, options, tracks, goptions):
        self.treestore.clear()
        self.checkbutton_genpath.set_active(options[KmlPaths_CONFKEY_KMLPATH_GENTRACK])
        self.tracksinfo = tracks
        self.options = options
        self.goptions = goptions


    def add_track(self, nam, des, pos=None):
        if pos == None:
            number = divmod(self.tracknum, len(self.tracksinfo)-1)[1]
            trackinfo = self.tracksinfo[number + 1]
        else:
            trackinfo = self.tracksinfo[pos]
        name = nam
        if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_NAME):
            name = trackinfo[KmlPaths_CONFKEY_TRACKS_NAME]
        description = des
        desc = des
        desc_file = None
        if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_DESC):
            filename = trackinfo[KmlPaths_CONFKEY_TRACKS_DESC]
            if os.path.isfile(filename):
                description = self.get_description(filename)
                filename = os.path.basename(filename)
                desc = '\t[' + _('file: ') + filename + ']'
                desc_file = filename
        color = KmlPaths_TRACKS_COLOR
        if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_COLOR):
            color = trackinfo[KmlPaths_CONFKEY_TRACKS_COLOR]
        width = KmlPaths_TRACKS_WIDTH
        if trackinfo.has_key(KmlPaths_CONFKEY_TRACKS_WIDTH):
            width = trackinfo[KmlPaths_CONFKEY_TRACKS_WIDTH]
        if pos != None:
            active = True
            # POS = 0 -> track from photos
            if pos == 0:
                i = 0
                for phototrackname, phototrackactive in self.photodirlist:
                    if phototrackname == nam:
                        active = phototrackactive
                        self.photodirlist[i] = (name, active)
                        break
                    i += 1
            ite = self.treestore.insert(None, pos,
                [active, True, str(KmlPaths_CONFKEY_TRACKS_NAME),
                    name, desc, description, desc_file, 
                    True, True, True, _GTKPaths_DESC_FAMILY])
        else:
            ite = self.treestore.append(None,
                [True, True, str(KmlPaths_CONFKEY_TRACKS_NAME),
                    name, desc, description, desc_file, 
                    True, True, True, _GTKPaths_DESC_FAMILY])
        self.treestore.append(ite,
            [None, False, str(KmlPaths_CONFKEY_TRACKS_COLOR),
                str(KmlPaths_CONFKEY_TRACKS_COLOR), color, None, None, 
                False, True, True, _GTKPaths_DEFAULT_FAMILY])
        self.treestore.append(ite,
            [None, False, str(KmlPaths_CONFKEY_TRACKS_WIDTH),
                str(KmlPaths_CONFKEY_TRACKS_WIDTH), width, None, None, 
                False, True, False, _GTKPaths_DEFAULT_FAMILY])
        self.tracknum += 1


    def _edit_cell(self, cell, path_string, new_text, column):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GTKPaths_COLUMN_KEY)
        if key == KmlPaths_CONFKEY_TRACKS_WIDTH:
            try:
                new = int(new_text)
                self.treestore.set(treestore_iter, _GTKPaths_COLUMN_VALUE, str(new))
            except:
                pass
        elif key == KmlPaths_CONFKEY_TRACKS_NAME and key == column:
            old_name = self.treestore.get_value(treestore_iter, _GTKPaths_COLUMN_VKEY)
            pos = 0
            for phototrackname, phototrackactive in self.photodirlist:
                if phototrackname == old_name:
                    active = phototrackactive
                    self.photodirlist[pos] = (str(new_text), phototrackactive)
                    break
                pos += 1
            self.treestore.set(treestore_iter, _GTKPaths_COLUMN_VKEY, new_text)


    def _edit_value(self, cellrenderer, editable, path_string):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GTKPaths_COLUMN_KEY)
        if key == KmlPaths_CONFKEY_TRACKS_COLOR:
            self._show_color(treestore_iter)
        elif key == KmlPaths_CONFKEY_TRACKS_NAME:
            self._show_description(treestore_iter)


    def _show_color(self, ite, title=_("Select a color for path ...")):
        dialog =  gtk.ColorSelectionDialog(title)
        colorsel = dialog.get_color_selection()
        colorsel.set_has_opacity_control(True)
        value = self.treestore.get_value(ite, _GTKPaths_COLUMN_VALUE)
        try:
            colorsel.set_current_alpha(int((int(value[0:2], 16)*65535)/255))
            colorsel.set_current_color(gtk.gdk.Color(
                red=int((int(value[6:8], 16)*65535)/255),
                green=int((int(value[4:6], 16)*65535)/255),
                blue=int((int(value[2:4], 16)*65535)/255) ))
        except:
            pass
        color_str = None
        if dialog.run() == gtk.RESPONSE_OK:
            color = colorsel.get_current_color()
            alpha = colorsel.get_current_alpha()
            color_str = "%.2X%.2X%.2X%.2X" % (
                int((alpha * 255)/65535),
                int((color.blue * 255)/65535),
                int((color.green * 255)/65535),
                int((color.red * 255)/65535))
            self.treestore.set(ite, _GTKPaths_COLUMN_VALUE, color_str)
        dialog.destroy()


    def _key_press_textiew(self, textview, event, dialog):
        if self.popup != None:
            if event.keyval == gtk.gdk.keyval_from_name("Up"):
                self.popup.prev()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Down"):
                self.popup.next()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Return"):
                value = self.popup.confirm()
                tbuffer = textview.get_buffer()
                end = tbuffer.get_iter_at_mark(tbuffer.get_insert())
                start = end.copy()
                start.backward_char()
                while start.get_char() not in " ,()[]<>|/\\\"\'\n\t":
                    start.backward_char()
                start.forward_char()
                tbuffer.delete(start, end)
                ite = tbuffer.get_iter_at_mark(tbuffer.get_insert())
                key = re.match(r"%\(([a-zA-Z0-9_\.]+)\|?.*]*\).", value).group(1)
                if key in self.goptions['defaults']:
                    tbuffer.insert_with_tags_by_name(ite, value, 'defaults')
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
                return self.autocomplete_textview(textview.get_buffer(), textview, dialog)
            elif gtk.gdk.keyval_from_name("percent") == event.keyval:
                return self.autocomplete_textview(textview.get_buffer(), textview, dialog)
        return False


    def autocomplete_textview(self, textbuffer, textview, dialog):
        autocompletions = [
            PhotoPlace_PathNAME,
            PhotoPlace_PathDESC,
            PhotoPlace_PathTINI,
            PhotoPlace_PathTEND,
            PhotoPlace_PathDRTN,
            PhotoPlace_PathLEN,
            PhotoPlace_PathLENMIN,
            PhotoPlace_PathLENMAX,
            PhotoPlace_PathSPMIN,
            PhotoPlace_PathSPMAX,
            PhotoPlace_PathSPAVG,
            PhotoPlace_PathNSEG,
            PhotoPlace_PathNWPT,
        ]
        completions = []
        for item in autocompletions:
            completions.append("%(" + item + ")s")
        for item in self.goptions['defaults'].iterkeys():
            completions.append("%(" + item + "|)s")
        if len(completions) > 0:
            position = dialog.window.get_root_origin()
            self.popup = TextViewCompleter(textview, position, completions)
            return True
        return False


    def _show_description(self, ite, height=500, width=400):
        self.popup = None
        filename = _('[select a file]')
        prefilename = self.treestore.get_value(ite, _GTKPaths_COLUMN_FILE)
        if prefilename:
            filename = os.path.basename(prefilename)
        dialog = gtk.Dialog(_('PhotoPlace: Path Description Template'), self.window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))
        dialog.set_has_separator(True)
        vbox = dialog.get_content_area()
        # Parameters
        label = gtk.Label()
        label.set_markup(_("Type the presentation text ... "))
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_alignment(0.0, 0.5)
        vbox.pack_start(label, False, False, 5)
        frame = gtk.Frame()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textview.set_tooltip_markup(_("You can use simple "
            "HTML tags like list (<i>li</i>, <i>ul</i>) or <i>table</i>"
            "and use these expresions to get some interesting values: \n"
            "\n<span font_family='monospace' size='small'>"
            "<b>%(PhotoPlace.PathNAME)s</b> -> Path name\n"
            "<b>%(PhotoPlace.PathDESC)s</b> -> Path description\n"
            "<b>%(PhotoPlace.PathTINI)s</b> -> Initial time (first point)\n"
            "<b>%(PhotoPlace.PathTEND)s</b> -> End time (last point)\n"
            "<b>%(PhotoPlace.PathDRTN)s</b> -> Duration\n"
            "<b>%(PhotoPlace.PathLEN)s</b> -> Length (in meters)\n"
            "<b>%(PhotoPlace.PathLENMIN)s</b> -> Minimum length\n"
            "<b>%(PhotoPlace.PathLENMAX)s</b> -> Maximum length\n"
            "<b>%(PhotoPlace.PathSPMIN)s</b> -> Minimum speed (m/s)\n"
            "<b>%(PhotoPlace.PathSPMAX)s</b> -> Maximum speed (m/s)\n"
            "<b>%(PhotoPlace.PathSPAVG)s</b> -> Average speed (m/s)\n"
            "<b>%(PhotoPlace.PathNSEG)s</b> -> Number of segments\n"
            "<b>%(PhotoPlace.PathNWPT)s</b> -> Number of waypoints\n"
            "</span>\n You can also use the <b>[defaults]</b> variables defined"
            " in the same way."))
        textview.add_events(gtk.gdk.KEY_PRESS_MASK)
        textbuffer = textview.get_buffer()
        tag = textbuffer.create_tag('attr')
        tag.set_property('foreground', "green")
        tag.set_property('family', "Monospace")
        tag = textbuffer.create_tag('defaults')
        tag.set_property('foreground', "red")
        tag.set_property('family', "Monospace")
        sw.add(textview)
        frame.add(sw)
        vbox.pack_start(frame, True, True)
        hbox = gtk.HBox(False, 5)
        label_text = gtk.Label()
        label_text.set_markup(_("... or load it from"))
        label_text.set_justify(gtk.JUSTIFY_RIGHT)
        label_text.set_alignment(1.0, 0.5)
        hbox.pack_start(label_text, False, False)
        filechooserbutton = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON)
        filechooserbutton.set_image(image)
        filechooserbutton.set_label(filename)
        filechooserbutton.connect('clicked', self._load_file, textview, ite, prefilename)
        hbox.pack_start(filechooserbutton, False, False, 5)
        alignment = gtk.Alignment(1.0, 0.5, 0.0, 0.0)
        alignment.add(hbox)
        vbox.pack_start(alignment, False, False, 10)
        value = self.treestore.get_value(ite, _GTKPaths_COLUMN_DESC)
        fd = StringIO.StringIO(self.treestore.get_value(ite, _GTKPaths_COLUMN_DESC))
        self._set_textbuffer(fd, textview)
        fd.close()
        dialog.resize(height, width)
        dialog.show_all()
        textview.connect("key_press_event", self._key_press_textiew, dialog)
        dialog.run()
        # wait to close ...
        start, end = textbuffer.get_bounds()
        char_count = textbuffer.get_char_count()
        char_limit = _GTKPaths_DESCRIPTION_CHARS
        line_count = textbuffer.get_line_count()
        if line_count > 1:
            mid = textbuffer.get_iter_at_line(1)
            contents = textbuffer.get_text(start, mid).strip()[0:char_limit]
        else:
            if char_count < char_limit:
                char_limit = char_count
            mid = textbuffer.get_iter_at_line_offset(0, char_limit)
            contents = textbuffer.get_text(start, mid)
        if line_count > 1 or char_count > char_limit:
            space_counter = _GTKPaths_DESCRIPTION_CHARS - len(contents)
            contents += "".join([' ' for num in xrange(space_counter)]) + "[... ->]"
        all_template = "<div mode='cdata'>\n" + textbuffer.get_text(start, end) + "\n</div>"
        self.treestore.set(ite, _GTKPaths_COLUMN_DESC, all_template)
        self.treestore.set(ite, _GTKPaths_COLUMN_VALUE, contents)
        self.popup = None
        dialog.destroy()
        dialog = None


    def _set_textbuffer(self, fd, textview):
        textview.set_wrap_mode(gtk.WRAP_NONE)
        tbuffer = textview.get_buffer()
        ite_end = tbuffer.get_iter_at_mark(tbuffer.get_insert())
        begin = True
        lines = 0
        for line in fd:
            for part in re.split(r"(%\([a-zA-Z0-9_\.]+\|?[a-zA-Z0-9 \?¿_.,:;=!@$&\-\+\*]*\).)", line):
                if part.startswith('%('):
                    key = re.match(r"%\(([a-zA-Z0-9_\.]+)\|?.*\).", part).group(1)
                    if key in self.goptions['defaults']:
                        tbuffer.insert_with_tags_by_name(ite_end, part, 'defaults')
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


    def _load_file(self, widget, textview, ite,prefilename=None):
        dialog = gtk.FileChooserDialog(title=_("Select file ..."),
            parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("All files"))
        ffilter.add_pattern("*")
        dialog.add_filter(ffilter)
        if prefilename:
            dialog.set_current_folder(os.path.dirname(prefilename))
        filename = None
        if dialog.run() == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            widget.set_label(str(os.path.basename(filename)))
        dialog.destroy()
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            self._set_textview(fd, textview)
        except:
            pass
        finally:
            if fd != None:
                fd.close()
        self.treestore.set(ite, _GTKPaths_COLUMN_FILE, filename)


    def get_data(self, key, index):
        ite = self.treestore.get_iter_from_string(str(index))
        if key == KmlPaths_CONFKEY_TRACKS_COLOR:
            ite = self.treestore.iter_nth_child(ite, 0)
            return self.treestore.get_value(ite, _GTKPaths_COLUMN_VALUE)
        elif key == KmlPaths_CONFKEY_TRACKS_WIDTH:
            ite = self.treestore.iter_nth_child(ite, 1)
            return self.treestore.get_value(ite, _GTKPaths_COLUMN_VALUE)
        elif key == KmlPaths_CONFKEY_TRACKS_NAME:
            return self.treestore.get_value(ite, _GTKPaths_COLUMN_VKEY)
        elif key == KmlPaths_CONFKEY_TRACKS_DESC:
            return self.treestore.get_value(ite, _GTKPaths_COLUMN_DESC)
        else:
            return ''


#EOF
