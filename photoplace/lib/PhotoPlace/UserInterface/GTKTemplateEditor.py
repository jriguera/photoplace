#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKTemplateEditor.py
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
A GTK+ implementation for a user interface. PhotoInfo window
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2011"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2011"


import os
import codecs
import xml.dom.minidom
import StringIO
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



# ###########################
# Window Editor for Templates
# ###########################

class TemplateEditorGUI(gobject.GObject):
    """
    GTK Editor Window
    """
    _instance = None

    __gsignals__ = {
        'load' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'save' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        '_save': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'close': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'new'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateEditorGUI, cls).__new__(cls)
        return cls._instance


    def __init__(self, resourcedir=None, parentwindow=None):
        if resourcedir:
            gobject.GObject.__init__(self)
            guifile = os.path.join(resourcedir, GTKUI_RESOURCE_TemplateEditorGUIXML)
            self.builder = gtk.Builder()
            self.builder.set_translation_domain(GTKUI_GETTEXT_DOMAIN)
            self.builder.add_from_file(guifile)
            self.window = self.builder.get_object("window")
            self.window.set_transient_for(parentwindow)
            self.window.set_destroy_with_parent(True)
            self.statusbar = self.builder.get_object("statusbar")
            self.textbuffer = self.builder.get_object("textbuffer")
            self.textview = self.builder.get_object("textview")
            tag = self.textbuffer.create_tag('attr')
            tag.set_property('foreground', "green")
            tag.set_property('family', "Monospace")
            tag = self.textbuffer.create_tag('defaults')
            tag.set_property('foreground', "red")
            tag.set_property('family', "Monospace")
            tag = self.textbuffer.create_tag('photo')
            tag.set_property('foreground', "blue")
            tag.set_property('family', "Monospace")
            self.tooltip = _("You can use simple HTML tags like <i>list</i> (<i>li</i>, "
                "<i>ul</i>) or <i>table</i> and use expresions like "
                "<b>%(Variable|<i>DEFAULT</i>)s</b> to get values. <b><i>DEFAULT</i></b> is the "
                "value to set up when <b>Variable</b> has no value, if <b><i>DEFAULT</i></b> is "
                "none (not a character, even space) <b>Variable</b> will not be shown. "
                "You can use the all global variables defined in the same way.\n"
                "\nTo get all supported variables press <b>&lt;ctl&gt;&lt;space&gt;</b>\n")
            self.ready = False


    def __getitem__(self, key):
        return self.builder.get_object(key)


    def __setitem__(self, key, value):
        raise ValueError("Cannot set key!")


    def init(self, userfacade):
        self.templatefile = None
        self.recoverfile = None
        self.savefile = None
        self.popup = None
        self.cansave = True
        self.canrecover = True
        self.canload = True
        self.canvalidate = True
        self.userfacade = userfacade
        self.textview.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.signals = {
            "on_window_delete_event": self.close,
            "on_textview_key_press_event": self._key_press,
            "on_toolbutton-wintemplates-exit_clicked": self.close,
            "on_toolbutton-wintemplates-load_clicked": self.load,
            "on_toolbutton-wintemplates-save_clicked": self.save,
            "on_textbuffer_mark_set": self._update_statusbar,
            "on_textbuffer_changed": self._update_statusbar,
            "on_toolbutton-wintemplates-new_clicked": self.new,
            "on_toolbutton-wintemplates-recover_clicked": self.recover,
            "on_toolbutton-wintemplates-check_clicked": self.validate,
        }
        self.builder.connect_signals(self.signals)
        self._signals = {
            'load' : [],
            'save' : [],
            'close': [],
            'new'  : [],
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


    def show(self, text='', template=None, save=None, recover=None, 
        completions=[], tooltip='', cansave=True, canrecover=True, canload=True, canvalidate=True):
        
        if not self.ready:
            return False
        self.popup = None
        dgettext = dict()
        dgettext['program'] = PhotoPlace_name
        can_save = cansave
        can_recover = canrecover
        can_load = canload
        can_validate = canvalidate
        self.templatefile = template
        if template:
            dgettext['template'] = os.path.basename(template)
            self.templatefile = self.userfacade.state.get_template(template)
            self.savefile = save
            if not save and cansave:
                self.savefile = self.userfacade.state.get_savepath(template)
            self.recoverfile = recover
            if not recover and canrecover:
                self.recoverfile = self.userfacade.state.get_recoverpath(template)
        else:
            can_save = False
            can_recover = False
            self.savefile = None
            self.recover = None
        if text:
            fd = StringIO.StringIO(text)
            self._load(fd)
            fd.close()
        else:
            self.load(None, self.templatefile)
        self.autocompletions = list()
        for item in self.userfacade.options['defaults'].iterkeys():
            self.autocompletions.append("%(" + item + "|)s")
        self.autocompletions += completions
        self.textview.set_tooltip_markup(self.tooltip + tooltip)
        self.window.show_all()
        if not can_save:
            self["toolbutton-wintemplates-save"].hide()
            self.window.set_title(_('%(program)s: Editing description') % dgettext)
        else:
            if dgettext.has_key('template'):
                self.window.set_title(_('%(program)s: Editing template <%(template)s>') % dgettext)
            else:
                self.window.set_title(_('%(program)s: Editing template') % dgettext)
        self.cansave = can_save
        if not can_recover:
            self["toolbutton-wintemplates-recover"].hide()
        self.canrecover = can_recover
        if not can_load:
            self["toolbutton-wintemplates-load"].hide()
        self.canload = can_load
        if not can_validate:
            self["toolbutton-wintemplates-check"].hide()
        self.canvalidate = can_validate
        return True


    def load(self, widget=None, template_file=None):
        if not self.canload:
            return False
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
            filename = template_file
        self.statusbar.pop(0)
        fd = None
        try:
            fd = codecs.open(filename, "r", encoding="utf-8")
            self._load(fd)
            self.statusbar.push(0,_("Template from file '%s' loaded") % os.path.basename(filename))
        except Exception as exception:
            self.statusbar.push(0, str(exception))
            return False
        finally:
            if fd != None:
                fd.close()
        ite_start, ite_end = self.textbuffer.get_bounds()
        text = self.textbuffer.get_text(ite_start, ite_end)
        self.emit('load', text, filename)
        return True


    def _load(self, fd):
        tbuffer = self.textbuffer
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


    def save(self, widget=None):
        if not self.cansave:
            return False
        self.statusbar.pop(0)
        start, end = self.textbuffer.get_bounds()
        template = self.textbuffer.get_text(start, end)
        fd = None
        error = False
        savedir = os.path.dirname(self.savefile)
        try:
            if not os.path.exists(savedir):
                os.makedirs(savedir)
            fd = codecs.open(self.savefile, "w", encoding="utf-8")
            fd.write("<div mode='cdata'>\n")
            fd.write(template)
            fd.write("\n</div>\n")
        except Exception as exception:
            self.statusbar.push(0, str(exception))
            error = True
        finally:
            if fd != None:
                fd.close()
        if not error:
            self.emit('save', template, self.savefile)
            self.emit('_save', template, self.savefile)
            self.statusbar.push(0,_('Template saved without problems'))
            return True
        else:
            self.statusbar.push(0,_('Error processing template'))
            return False


    def _key_press(self, textview, event):
        if self.popup != None:
            if event.keyval == gtk.gdk.keyval_from_name("Up"):
                self.popup.prev()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Down"):
                self.popup.next()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name("Return"):
                value = self.popup.confirm()
                tbuffer = self.textbuffer
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
                return self._autocomplete(self.textbuffer)
            elif gtk.gdk.keyval_from_name("percent") == event.keyval:
                return self._autocomplete(self.textbuffer)
        return False


    def _autocomplete(self, textbuffer):
        if self.autocompletions:
            position = self.window.window.get_root_origin()
            self.popup = TextViewCompleter(self.textview, position, self.autocompletions)
            return True
        return False


    def _update_statusbar(self, textbuffer, *args, **kwargs):
        self.statusbar.pop(0)
        count = textbuffer.get_char_count()
        ite = textbuffer.get_iter_at_mark(textbuffer.get_insert())
        row = ite.get_line()
        col = ite.get_line_offset()
        dgettext = {}
        dgettext['line'] = row + 1
        dgettext['column'] = col
        dgettext['chars'] = count
        self.statusbar.push(0,
            _('Line %(line)d, column %(column)d (%(chars)d chars in document)') % dgettext)


    def new(self, widget=None):
        self.statusbar.pop(0)
        start, end = self.textbuffer.get_bounds()
        self.textbuffer.delete(start, end)
        if self.templatefile:
            self.statusbar.push(0, _('New empty template'))
        else:
            self.statusbar.push(0, _('Empty description'))
        self.emit('new')


    def recover(self, widget=None, filename=None):
        if not self.canrecover:
            return False
        template = self.recoverfile
        if filename:
            template = filename
        if not template:
            self.statusbar.pop(0)
            self.statusbar.push(0, _('Cannot be recovered!'))
            return False
        self.new()
        if os.path.isfile(template):
            if self.load(None, template):
                return self.save()
            return True
        else:
            self.statusbar.pop(0)
            self.statusbar.push(0, _('Cannot find system template!'))
            return False


    def validate(self, widget=None):
        if not self.canvalidate:
            return False
        start, end = self.textbuffer.get_bounds()
        template = self.textbuffer.get_text(start, end)
        template = "<div mode='cdata'>\n" + template + "\n</div>"
        self.statusbar.pop(0)
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
                ins = self.textbuffer.get_iter_at_line(pos - 1)
                bound = self.textbuffer.get_iter_at_line(pos)
                self.textbuffer.select_range(ins, bound)
            self.statusbar.push(0, _('XML error: %s') % text)
            return False
        else:
            self.statusbar.push(0, _('Perfect! template is well formed!'))
            return True


    def close(self, widget=None, data=None):
        if self.popup != None:
            self.popup.destroy()
            self.popup = None
        start, end = self.textbuffer.get_bounds()
        text = self.textbuffer.get_text(start, end)
        self.textbuffer.set_text('')
        self.window.hide()
        self.emit('close', text, self.templatefile)
        self.templatefile = None
        self.recoverfile = None
        self.savefile = None
        self.autocompletions = list()
        self.disconnect()
        return True


# EOF

