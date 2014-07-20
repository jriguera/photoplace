#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKPhotoInfo.py
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


import os.path
import cStringIO
import warnings
import types
import re
from PIL import Image

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
from PhotoPlace.Facade import parse_str_datetime as parse_str_datetime


# ##############
# JPEG to pixbuf
# ##############

def getPixbuf(geophoto, size=PIXBUFSIZE_GEOPHOTOINFO, interpolation=Image.BILINEAR):
    im = Image.open(geophoto.path)
    (im_width, im_height) = im.size
    # Size transformations
    (width, height) = size
    mirror = im.resize((width, height), interpolation)
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
    #filein = StringIO.StringIO()
    filein = cStringIO.StringIO()
    mirror.save(filein, 'ppm')
    contents = filein.getvalue()
    filein.close()
    loader = gtk.gdk.PixbufLoader("pnm")
    loader.write(contents, len(contents))
    loader.close()
    pixbuf = loader.get_pixbuf()
    return pixbuf



# #################################
# Photo Extended information window
# #################################

class PhotoInfoGUI(gobject.GObject):
    """
    Photo Extended information window
    """
    _instance = None

    __gsignals__ = {
        'save' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        '_save': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        'reload' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        '_reload' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PhotoInfoGUI, cls).__new__(cls)
        return cls._instance

    def __init__(self, resourcedir=None, parentwindow=None):
        if resourcedir:
            gobject.GObject.__init__(self)
            guifile = os.path.join(resourcedir, GTKUI_RESOURCE_PhotoInfoGUIXML)
            self.builder = gtk.Builder()
            self.builder.set_translation_domain(GTKUI_GETTEXT_DOMAIN)
            self.builder.add_from_file(guifile)
            self.window = self.builder.get_object("window")
            self.window.set_transient_for(parentwindow)
            self.window.set_destroy_with_parent(True)
            self.image = self.builder.get_object("image")
            self.label = self.builder.get_object("label-geophotopath")
            self.treeview = self.builder.get_object("treeview")
            self.treeview.set_tooltip_markup(_("Double click on a cell to edit the value. \n\n"
                "If you want to geotag a photo manualy, you have to switch to <b>[write]</b> mode first. "
                "You must use the same format as you see for name, date and numbers. \n\n"
                "<b>Latitude</b>, <b>Longitude</b>, <b>Elevation</b>: (float) GPS coordinates of the photo.\n\n"
                "<b>Status</b>: (integer) value greather than 0 means active.\n\n"
                "<b>Time Offset</b>: (integer) seconds to add to the current date/time to get the original date/time.\n\n"
                "<b>Point Time</b>: (if appears, date/time, not editable) time of GPX point used to geotag the photo.\n\n"
                "<b>Variables</b>: list of attributes settled up by Addons to control their behaviour.")
            )
            treeviewcolumn_key = self.builder.get_object("treeviewcolumn-key")
            treeviewcolumn_key.set_title(_("Property"))
            treeviewcolumn_key.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            treeviewcolumn_key.set_resizable(True)
            treeviewcolumn_key.set_fixed_width(180)
            treeviewcolumn_value = self.builder.get_object("treeviewcolumn-value")
            treeviewcolumn_value.set_title(_("Value"))
            # deletable, editable, key, value, fgcolor, instance
            self.treestore = gtk.TreeStore(bool, bool, str, str, str, gobject.TYPE_PYOBJECT, str)
            self.treeview.set_model(self.treestore)
            self.treeview.set_rules_hint(True)
            self.ready = False

    def __getitem__(self, key):
        return self.builder.get_object(key)

    def __setitem__(self, key, value):
        raise ValueError("Cannot set key!")

    def init(self, userfacade, treemodel):
        self.userfacade = userfacade
        self.stzdiff = userfacade.state.stzdiff
        self.current_geophoto = None
        self.current_pixbuf = None
        self.main_treemodel_iterator = None
        self.main_treemodel = treemodel
        self.cannextprev = True
        self.first_time = True
        self.signals = {
            "on_window_delete_event": self.close,
            "on_treeview_row_activated": self._clicked_attr,
            "on_cellrenderertext-value_edited": self._edit_cell,
            "on_button-add_clicked": self._add_attr,
            "on_button-del_clicked": self._del_attr,
            "on_button-next_clicked": self.next,
            "on_button-close_clicked": self.close,
            "on_button-prev_clicked": self.prev,
        }
        self.builder.connect_signals(self.signals)
        self._signals = {
            'save' : [],
            'reload' : [],
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
                gobject.GObject.disconnect(self, identifier)
                for signal in self._signals:
                    if identifier in self._signals[signal]:
                        self._signals[signal].remove(identifier)
            else:
                for signal in self._signals:
                    for i in self._signals[signal]:
                        gobject.GObject.disconnect(self, i)
                        self._signals[signal].remove(i)
                    self._signals[signal] = list()

    def show(self, geophoto=None, iterator=None, cannextprev=None, sizex=1, sizey=1):
        if not self.ready:
            return False
        if geophoto:
            if not iterator:
                return False
            self.current_geophoto = geophoto
            self.main_treemodel_iterator = iterator
        dgettext = dict()
        dgettext['program'] = PhotoPlace_name
        dgettext['photo'] = self.current_geophoto['name']
        self.window.set_title('%(program)s: Exif info of <%(photo)s>' % dgettext)
        self.current_pixbuf = getPixbuf(self.current_geophoto)
        self.label.set_text(self.current_geophoto.path)
        img_width, img_height = self._image(self.current_pixbuf)
        self._show(self.current_geophoto)
        if self.first_time:
            if img_width > img_height:
                self["hpaned"].set_position(img_width + 2)
            else:
                self["hpaned"].set_position(img_height + 2)
        self.window.show_all()
        if cannextprev != None:
            self.cannextprev = cannextprev
        if not self.cannextprev:
            self["button-prev"].hide()
            self["button-next"].hide()
        else:
            if not self._next():
                self["button-next"].set_sensitive(False)
            else:
                self["button-next"].set_sensitive(True)
            if not self._prev():
                self["button-prev"].set_sensitive(False)
            else:
                self["button-prev"].set_sensitive(True)
        self.first_time = False
        return True

    def _image(self, pixbuf, interpolation=gtk.gdk.INTERP_BILINEAR):
        allocation = self['image'].get_allocation()
        allo_width = allocation.width
        allo_height = allocation.height
        img_width = pixbuf.get_width()
        img_height = pixbuf.get_height()
        if allo_height == 1:
            # fist time
            allo_height = 400
            if img_width > img_height:
                allo_height  = 360
        percent = float(allo_height) / float(img_height)
        allo_width = int(img_width * percent)
        scaled = pixbuf.scale_simple(allo_width, allo_height, interpolation)
        self.image.set_from_pixbuf(scaled)
        return (allo_width, allo_height) 

    def _show(self, geophoto):
        model = self.treeview.get_model()
        model.clear()
        color = TREEVIEWPHOTOINFO_GEOPHOTOINFO_COLOR
        model.append(None,[False, True, _("<b>Name</b>"), str(geophoto['name']), color, types.StringType, 'name'])
        model.append(None,[False, True, _("<b>Date/Time</b>"), str(geophoto['time']), color, types.StringType, 'time'])
        lat = ''
        lon = ''
        ele = ''
        if geophoto.isGeoLocated():
            lon = "%.8f" % geophoto['lon']
            lat = "%.8f" % geophoto['lat']
            ele = "%.3f" % geophoto['ele']
        model.append(None,[False, True, _("<b>Longitude</b>"), lon, color, types.FloatType, 'lon'])
        model.append(None,[False, True, _("<b>Latitude</b>"), lat, color, types.FloatType, 'lat'])
        model.append(None,[False, True, _("<b>Elevation</b>"), ele, color, types.FloatType, 'ele'])
        if geophoto.ptime:
            ptime = geophoto.ptime.strftime("%Y-%m-%dT%H:%M:%S") + self.stzdiff
            model.append(None,[False, False, _("<b>Point Time</b>"), ptime, color, types.StringType, 'ptime'])
        model.append(None,[False, True, _("<b>Time Offset</b>"), "%d" % geophoto['toffset'], color, types.IntType, 'toffset'])
        model.append(None,[False, True, _("<b>Status</b>"), "%d" % geophoto['status'], color, types.IntType, 'status'])
        color = TREEVIEWPHOTOINFO_GEOPHOTOATTR_COLOR
        ite = model.append(None, [False, False, _("Variables"), None, color, None, None])
        if geophoto.attr:
            for k, v in geophoto.attr.iteritems():
                model.append(ite, [ True, True, str(k), str(v), color, type(v), ''])
        color = TREEVIEWPHOTOINFO_GEOPHOTOEXIF_COLOR
        ite = model.append(None, [ False, False, _("Image EXIF Values"), None, color, None, None])
        for k in geophoto.exif.exif_keys:
            try:
                model.append(ite, [ False, False, str(k), str(geophoto[k]), color, None, ''])
            except:
                pass
        self.treeview.expand_all()

    def next(self, widget=None, data=None):
        self.emit('save', self.main_treemodel_iterator, self.current_geophoto)
        self.emit('_save', self.main_treemodel_iterator, self.current_geophoto)
        next = self._next()
        if next != None:
            geophoto_path = self.main_treemodel.get_value(next, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.show(geophoto, next)
                    return

    def _next(self):
        next = self.main_treemodel.iter_next(self.main_treemodel_iterator)
        while next != None and self.main_treemodel.iter_parent(next) == self.main_treemodel_iterator:
            next = self.main_treemodel.iter_next(next)
        return next

    def prev(self, widget=None, data=None):
        self.emit('save', self.main_treemodel_iterator, self.current_geophoto)
        self.emit('_save', self.main_treemodel_iterator, self.current_geophoto)
        prev = self._prev()
        if prev != None:
            geophoto_path = self.main_treemodel.get_value(prev, TREEVIEWPHOTOS_COL_PATH)
            for geophoto in self.userfacade.state.geophotos:
                if geophoto.path == geophoto_path:
                    self.show(geophoto, prev)
                    return

    def _prev(self):
        prev = None
        path = self.main_treemodel.get_path(self.main_treemodel_iterator)
        position = path[0]
        if position != 0:
            prev_path = position - 1
            prev = self.main_treemodel.get_iter(str(prev_path))
        return prev

    def _clicked_attr(self, treeview, path, column, data=None):
        model = treeview.get_model()
        ite = model.get_iter(path)
        if model.get_value(ite, TREEVIEWPHOTOINFO_COL_EDIT):
            key = model.get_value(ite, TREEVIEWPHOTOINFO_COL_VKEY)
            value = model.get_value(ite, TREEVIEWPHOTOINFO_COL_VALUE)
            self["entry-key"].set_text(key)

    def _add_attr(self, widget, value=''):
        key = self["entry-key"].get_text().strip()
        if key:
            self.current_geophoto.attr[key] = value
            self._show(self.current_geophoto)

    def _del_attr(self, widget):
        key = self["entry-key"].get_text().strip()
        if self.current_geophoto.attr.has_key(key):
            del  self.current_geophoto.attr[key]
            self._show(self.current_geophoto)
        self["entry-key"].set_text('')

    def _edit_cell(self, cell, path_string, new_text):
        model = self.treeview.get_model()
        treestore_iter = model.get_iter_from_string(path_string)
        obj = model.get_value(treestore_iter, TREEVIEWPHOTOINFO_COL_TYPE)
        key = model.get_value(treestore_iter, TREEVIEWPHOTOINFO_COL_KEY)
        text = new_text.strip()
        try:
            if key:
                value = None
                # is a geophoto main attr
                if key == "name":
                    text = re.sub(r"[^\w\s\.\-]", '', text)
                    text = re.sub(r"\s+", '_', text)
                    text, new_ext = os.path.splitext(text)
                    if not text:
                        raise ValueError
                    value = text + PhotoPlace_FILE_DEF_EXTENSION
                elif key == "lat":
                    value = obj(text)
                    if value < -90.0 or value > 90.0:
                        raise ValueError
                elif key == "lon":
                    value = obj(text)
                    if value < -180.0 or value > 180.0:
                        raise ValueError
                elif key == "ele":
                    value = obj(text)
                    if value < -100.0 or value > 50000.0:
                        raise ValueError
                elif key == "status":
                    value = obj(text)
                    if value < 0:
                        raise ValueError
                elif key == "toffset":
                    value = obj(text)
                elif key == "ptime" or key == "time":
                    (scope, value) = parse_str_datetime(text)
                    if not scope in [ "day", "hour", "minute", "second" ]:
                        raise ValueError
                if value != None:
                    self.current_geophoto[key] = value
                    model.set(treestore_iter, TREEVIEWPHOTOINFO_COL_VALUE, value)
                else:
                    raise ValueError
            else:
                # user/plugin defined
                key = model.get_value(treestore_iter, TREEVIEWPHOTOINFO_COL_VKEY)
                self.current_geophoto.attr[key] = obj(text)
                model.set(treestore_iter, TREEVIEWPHOTOINFO_COL_VALUE, text)
            self.emit('reload', self.main_treemodel_iterator, self.current_geophoto)
            self.emit('_reload', self.main_treemodel_iterator, self.current_geophoto)
        except:
            pass

    def close(self, window=None, event=None):
        self.emit('save', self.main_treemodel_iterator, self.current_geophoto)
        self.emit('_save', self.main_treemodel_iterator, self.current_geophoto)
        self.window.hide_all()
        self.disconnect()
        return True


# EOF

