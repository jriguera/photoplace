#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKGpxdata.py
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
Add-on for PhotoPlace to generate paths and waypoints from GPX tracks to show them in the KML layer.
"""
__program__ = "photoplace.gpxdata"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.2.3"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera Lopez"


import os.path
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

from gpxdata import *

from PhotoPlace.UserInterface.GTKTemplateEditor import TemplateEditorGUI
from PhotoPlace.UserInterface.GTKUI import CellRendererTextClick


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
    _GTKGPXData_COLUMN_ID,
    _GTKGPXData_COLUMN_TYPE,
    _GTKGPXData_COLUMN_ACT,
    _GTKGPXData_COLUMN_VIS,
    _GTKGPXData_COLUMN_KEY,
    _GTKGPXData_COLUMN_VKEY,
    _GTKGPXData_COLUMN_VALUE,
    _GTKGPXData_COLUMN_EDITKEY,
    _GTKGPXData_COLUMN_EDITVAL,
    _GTKGPXData_COLUMN_CLICK,
    _GTKGPXData_COLUMN_TOOLTIP,
    _GTKGPXData_COLUMN_FAMILY,
) = range(12)

# Data type
(
    _GTKGPXData_TYPE_TITLE,
    _GTKGPXData_TYPE_PATH,
    _GTKGPXData_TYPE_TRACK,
    _GTKGPXData_TYPE_WPT,
) = range(4)

# 2 types for columns
(
    _GTKGPXData_COLUMN_TYPE_KEY,
    _GTKGPXData_COLUMN_TYPE_VALUE,
) = range(2)

_GTKGPXData_DESCRIPTION_CHARS = 45
_GTKGPXData_DEFAULT_FAMILY = None
_GTKGPXData_DESC_FAMILY = "Monospace"
_GTKGPXData_TRACKS_WIDTH = _("Width")
_GTKGPXData_TRACKS_COLOR = _("Color")



class GTKGPXData(object):

    def __init__(self, gui, userfacade, logger):
        object.__init__(self)
        self.options = None
        self.goptions = None
        self.tracksinfo = None
        self.logger = logger
        self.userfacade = userfacade
        self.plugin = gtk.VBox(False)
        # 1st line
        hbox_checks = gtk.HBox(False)
        label = gtk.Label()
        label.set_markup(_("Include in KML: "))
        hbox_checks.pack_start(label, False, False, 5)
        self.checkbutton_genpath = gtk.CheckButton(_("Path from geottaged photos"))
        self.checkbutton_genpath.connect('toggled',
            self._toggled_button, _GTKGPXData_TYPE_PATH)
        self.checkbutton_genpath.set_sensitive(False)
        hbox_checks.pack_start(self.checkbutton_genpath, False, False, 5)
        self.checkbutton_gentrack = gtk.CheckButton(_("Tracks from GPX"))
        self.checkbutton_gentrack.connect('toggled',
            self._toggled_button, _GTKGPXData_TYPE_TRACK)
        self.checkbutton_gentrack.set_sensitive(False)
        hbox_checks.pack_start(self.checkbutton_gentrack, False, False, 8)
        self.checkbutton_genwpts = gtk.CheckButton(_("WayPoints from GPX"))
        self.checkbutton_genwpts.connect('toggled',
            self._toggled_button, _GTKGPXData_TYPE_WPT)
        self.checkbutton_genwpts.set_sensitive(False)
        hbox_checks.pack_start(self.checkbutton_genwpts, False, False, 5)
        self.plugin.pack_start(hbox_checks, False, False, 10)
        # Parameters
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create model for parameters
        self.treestore = gtk.TreeStore(
            int, int, bool, bool, str, str, str, bool, bool, bool, str, str)
        treeview = gtk.TreeView(self.treestore)
        treeview.set_rules_hint(True)
        treeview.set_tooltip_column(_GTKGPXData_COLUMN_TOOLTIP)
        treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        treeview.connect('button-press-event' , self._lclick_row)
        # columns
        renderer = gtk.CellRendererToggle()
        renderer.set_radio(True)
        renderer.connect('toggled', self._toggled_row)
        column = gtk.TreeViewColumn(None, renderer,
            active=_GTKGPXData_COLUMN_ACT,
            visible=_GTKGPXData_COLUMN_VIS)
        treeview.append_column(column)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self._edit_cell, _GTKGPXData_COLUMN_TYPE_KEY)
        column = gtk.TreeViewColumn(_("Path Name/Parameter"), renderer,
            text=_GTKGPXData_COLUMN_VKEY,
            editable=_GTKGPXData_COLUMN_EDITKEY)
        column.set_resizable(True)
        treeview.append_column(column)
        treeview.set_expander_column(column)
        renderer = CellRendererTextClick()
        renderer.connect('editing-started', self._edit_property)
        renderer.connect('edited', self._edit_cell, _GTKGPXData_COLUMN_TYPE_VALUE)
        column = gtk.TreeViewColumn(_("Description/Value"), renderer,
            text=_GTKGPXData_COLUMN_VALUE,
            editable=_GTKGPXData_COLUMN_EDITVAL,
            clickable=_GTKGPXData_COLUMN_CLICK,
            family=_GTKGPXData_COLUMN_FAMILY)
        column.set_resizable(True)
        treeview.append_column(column)
        scroll.add(treeview)
        self.plugin.pack_start(scroll, True, True)
        self.windoweditor = TemplateEditorGUI()
        self.window = gui.builder.get_object("window")


    def show(self, widget=None, options=None, tracks=None, wpts=None, goptions=None):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options, tracks, wpts, goptions)
        self.plugin.show_all()


    def setup(self, options, tracks, wpts, goptions):
        self.tracksinfo = tracks
        self.wptsinfo = wpts
        self.options = options
        self.goptions = goptions
        self.reset()


    def hide(self, reset=False):
        self.plugin.hide_all()
        if reset:
            self.reset()


    def reset(self):
        self.treestore.clear()
        self.iterator_paths = None
        self.pathlist = {}
        self.pathstyles = {}
        self.iterator_tracks = None
        self.tracklist = {}
        self.trackstyles = {}
        self.iterator_wpts = None
        self.wptlist = {}
        self.wptstyles = {}
        if self.checkbutton_genpath.get_active() != self.options[GPXData_CONFKEY_GENPATH]:
            self.checkbutton_genpath.set_active(self.options[GPXData_CONFKEY_GENPATH])
        else:
            tmp = self.options[GPXData_CONFKEY_GENPATH]
            self.checkbutton_genpath.set_active(False)
            if tmp:
                self.checkbutton_genpath.set_active(True)
        if self.checkbutton_gentrack.get_active() != self.options[GPXData_CONFKEY_GENTRACK]:
            self.checkbutton_gentrack.set_active(self.options[GPXData_CONFKEY_GENTRACK])
        else:
            tmp = self.options[GPXData_CONFKEY_GENTRACK]
            self.checkbutton_gentrack.set_active(False)
            if tmp:
                self.checkbutton_gentrack.set_active(True)
        if self.checkbutton_genwpts.get_active() != self.options[GPXData_CONFKEY_GENPOINTS]:
            self.checkbutton_genwpts.set_active(self.options[GPXData_CONFKEY_GENPOINTS])
        else:
            tmp = self.options[GPXData_CONFKEY_GENPOINTS]
            self.checkbutton_genwpts.set_active(False)
            if tmp:
                self.checkbutton_genwpts.set_active(True)
        self.checkbutton_genpath.set_sensitive(False)
        self.checkbutton_gentrack.set_sensitive(False)
        self.checkbutton_genwpts.set_sensitive(False)


    def _toggled_button(self, widget, data):
        value = widget.get_active()
        if data == _GTKGPXData_TYPE_PATH:
            self.options[GPXData_CONFKEY_GENPATH] = value
            self.set_paths(value)
        elif data == _GTKGPXData_TYPE_TRACK:
            self.options[GPXData_CONFKEY_GENTRACK] = value
            self.set_tracks(value)
        elif data == _GTKGPXData_TYPE_WPT:
            self.options[GPXData_CONFKEY_GENPOINTS] = value
            self.set_wpts(value)


    def clear(self, iterator, remove=True):
        if iterator == None:
            return
        deleted = []
        nchildren = self.treestore.iter_n_children(iterator)
        while nchildren > 0:
            nchildren -= 1
            ite = self.treestore.iter_nth_child(iterator, nchildren)
            deleted.append(ite)
        for ite in deleted:
            self.treestore.remove(ite)
        if remove:
            self.treestore.remove(iterator)


    def set_paths_widget(self, mode=True):
        self.checkbutton_genpath.set_sensitive(mode)
        if self.options[GPXData_CONFKEY_GENPATH]:
            self.checkbutton_genpath.set_active(mode)


    def set_tracks_widget(self, mode=True):
        self.checkbutton_gentrack.set_sensitive(mode)
        if self.options[GPXData_CONFKEY_GENTRACK]:
            self.checkbutton_gentrack.set_active(mode)


    def set_wpts_widget(self, mode=True):
        self.checkbutton_genwpts.set_sensitive(mode)
        if self.options[GPXData_CONFKEY_GENPOINTS]:
            self.checkbutton_genwpts.set_active(mode)


    def set_paths(self, mode=True):
        if mode:
            tip = _("List of generated paths from geotagged photos")
            name = _("Paths from geottaged photos")
            self.iterator_paths = self.treestore.append(None,
                [-1, _GTKGPXData_TYPE_PATH, False, False, '',
                name , '', False, False, False, tip, None])
            self.add_paths()
        else:
            self.clear(self.iterator_paths)
            self.iterator_paths = None


    def add_paths(self, pathlist=None, pathstyles=None):
        if pathlist != None and pathstyles != None:
            self.pathlist = pathlist
            self.pathstyles = pathstyles
        num = 0
        if self.options[GPXData_CONFKEY_GENPATH]:
            for path_id, path in self.pathlist.iteritems():
                style = self.pathstyles[path_id]
                self.add_track(self.iterator_paths, path_id, path, style, _GTKGPXData_TYPE_PATH)
                num += 1
            desc = _(" %d path(s)") % num
            self.treestore.set(self.iterator_paths, _GTKGPXData_COLUMN_VALUE, desc)
        return num


    def set_tracks(self, mode=True):
        if mode:
            tip = _("List of tracks read from GPX file")
            name = _("Tracks from GPS data")
            self.iterator_tracks = self.treestore.append(None,
                [-1, _GTKGPXData_TYPE_TRACK, False, False, '',
                name , '', False, False, False, tip, None])
            self.add_tracks()
        else:
            self.clear(self.iterator_tracks)
            self.iterator_tracks = None


    def add_tracks(self, tracklist=None, trackstyles=None):
        if tracklist != None and trackstyles != None:
            self.tracklist = tracklist
            self.trackstyles = trackstyles
        num = 0
        if self.options[GPXData_CONFKEY_GENTRACK]:
            for track_id, track in self.tracklist.iteritems():
                style = self.trackstyles[track_id]
                self.add_track(self.iterator_tracks, track_id, track, style)
                num += 1
            desc = _(" %d track(s)") % num
            self.treestore.set(self.iterator_tracks, _GTKGPXData_COLUMN_VALUE, desc)
        return num


    def set_wpts(self, mode=True):
        if mode:
            tip = _("List of WayPoints read from GPX file")
            name = _("WayPoints from GPS data")
            self.iterator_wpts = self.treestore.append(None,
                [-1, _GTKGPXData_TYPE_WPT, False, False, '',
                name , '', False, False, False, tip, None])
            self.add_wpts()
        else:
            self.clear(self.iterator_wpts)
            self.iterator_wpts = None


    def add_wpts(self, wptlist=None, wptstyles=None):
        if wptlist != None and wptstyles != None:
            self.wptlist = wptlist
            self.wptstyles = wptstyles
        num = 0
        if self.options[GPXData_CONFKEY_GENPOINTS]:
            for wpt_id, wpt in self.wptlist.iteritems():
                style = self.wptstyles[wpt_id]
                self.add_wpt(self.iterator_wpts, wpt_id, wpt, style)
                num += 1
            desc = _(" %d waypoint(s)") % num
            self.treestore.set(self.iterator_wpts, _GTKGPXData_COLUMN_VALUE, desc)
        return num


    def add_track(self, iterator, track_id, track, style, kind=_GTKGPXData_TYPE_TRACK):
        desc = track.desc
        name = track.name
        dgettext = dict()
        color = GPXData_TRACKS_COLOR
        if style.has_key(GPXData_CONFKEY_TRACKS_COLOR):
            color = style[GPXData_CONFKEY_TRACKS_COLOR]
        width = GPXData_TRACKS_WIDTH
        if style.has_key(GPXData_CONFKEY_TRACKS_WIDTH):
            width = style[GPXData_CONFKEY_TRACKS_WIDTH]
        dgettext['path_oname'] = track.attr['.orig-name']
        dgettext['path_id'] = track_id
        tooltip = _("Track #%(path_id)s (original name: %(path_oname)s)\n")
        try:
            (tmin, tmax, duration) = track.timeMinMaxDuration()
            (lmin, lmax, length) = track.lengthMinMaxTotal()
            dgettext['path_npoints'] = len(track.listpoints())
            dgettext['path_len'] = length
            dgettext['path_time'] = duration
            dgettext['path_end'] = tmax
            dgettext['path_begin'] = tmin
            tooltip += _("Points: %(path_npoints)s, length: %(path_len).3f m.\n")
            tooltip += _("Duration: %(path_time)s\n")
            tooltip += _("Begin time: %(path_begin)s\n")
            tooltip += _("Final time: %(path_end)s\n")
        except:
            pass
        tooltip = tooltip % dgettext
        default_tip = _("Double click to edit values ...")
        tip = tooltip + '\n' + default_tip
        status = bool(track.status)
        ite = self.treestore.append(iterator, [
            track_id, kind, status, True, GPXData_CONFKEY_TRACKS_NAME,
            name, desc, True, True, False, tip, _GTKGPXData_DEFAULT_FAMILY])
        self.treestore.append(ite, [
            track_id, kind, None, False, GPXData_CONFKEY_TRACKS_COLOR,
            _GTKGPXData_TRACKS_COLOR, color, False, True, True,
            default_tip, _GTKGPXData_DEFAULT_FAMILY])
        self.treestore.append(ite, [
            track_id, kind, None, False, GPXData_CONFKEY_TRACKS_WIDTH,
            _GTKGPXData_TRACKS_WIDTH, width, False, True, False,
            default_tip, _GTKGPXData_DEFAULT_FAMILY])


    def add_wpt(self, iterator, wpt_id, wpt, style):
        name = wpt.attr['name']
        desc = wpt.attr['desc']
        dgettext = dict()
        icon = GPXData_WPT_ICON
        if style.has_key(GPXData_CONFKEY_WPT_ICON):
            icon = style[GPXData_CONFKEY_WPT_ICON]
        scale = GPXData_WPT_ICONSCALE
        if style.has_key(GPXData_CONFKEY_WPT_ICONSCALE):
            scale = style[GPXData_CONFKEY_WPT_ICONSCALE]
        dgettext['wpt_oname'] = wpt.attr['.orig-name']
        dgettext['wpt_id'] = wpt_id
        tooltip = _("WayPoint #%(wpt_id)s (original name: %(wpt_oname)s)\n")
        tooltip = tooltip % dgettext
        default_tip = _("Double click to edit values ...")
        tip = tooltip + '\n' + default_tip
        status = bool(wpt.status)
        ite = self.treestore.append(iterator, [
            wpt_id, _GTKGPXData_TYPE_WPT, status, True, GPXData_CONFKEY_TRACKS_NAME,
            name, desc, True, True, False, tip, None])


    def _lclick_row(self, widget, event):
        if event.button == 3:
            paths_ite = widget.get_path_at_pos(int(event.x), int(event.y))
            if paths_ite == None:
                # invalid path
                pass
            elif len(paths_ite) > 0:
                treestore_iter = self.treestore.get_iter(paths_ite[0])
                key = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_KEY)
                obj_id = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ID)
                if key == GPXData_CONFKEY_TRACKS_NAME or obj_id == -1:
                    kind = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_TYPE)
                    style = None
                    menu = gtk.Menu()
                    if obj_id < 0:
                        msg = _("Edit main default template ...")
                        if kind == _GTKGPXData_TYPE_TRACK:
                            msg = _("Edit main default template for tracks")
                        elif kind == _GTKGPXData_TYPE_PATH:
                            msg = _("Edit main default template for generated paths")
                        elif kind == _GTKGPXData_TYPE_WPT:
                            msg = _("Edit main default template for waypoints")
                        menu_edit = gtk.MenuItem(msg)
                        menu.append(menu_edit)
                    else:
                        active = True
                        if kind == _GTKGPXData_TYPE_TRACK:
                            style = self.trackstyles[obj_id]
                            if style.has_key(GPXData_CONFKEY_TRACKS_DESC) \
                            and style[GPXData_CONFKEY_TRACKS_DESC]:
                                active = False
                        elif kind == _GTKGPXData_TYPE_PATH:
                            style = self.pathstyles[obj_id]
                            if style.has_key(GPXData_CONFKEY_TRACKS_DESC) \
                            and style[GPXData_CONFKEY_TRACKS_DESC]:
                                active = False
                        elif kind == _GTKGPXData_TYPE_WPT:
                            style = self.wptstyles[obj_id]
                            if style.has_key(GPXData_CONFKEY_WPT_DESC) \
                            and style[GPXData_CONFKEY_WPT_DESC]:
                                active = False
                        menu_edit = gtk.MenuItem(_("Edit Template/Description"))
                        menu_default = gtk.CheckMenuItem(_("Default Template"))
                        menu_default.set_active(active)
                        menu.append(menu_edit)
                        menu.append(menu_default)
                        menu_default.connect("activate", self._activate_setdesc, style, kind, obj_id)
                    menu_edit.connect("activate", self._activate_menuedit, treestore_iter, style, kind, obj_id)
                    menu.show_all()
                    menu.popup(None, None, None, event.button, event.time)


    def _activate_menuedit(self, widget, iterator, style, kind, obj_id):
        if kind == _GTKGPXData_TYPE_WPT:
            tooltip = _("\n<span font_family='monospace' size='small'>"
            "<b>%(PhotoPlace.WptNAME)s</b> -> WayPoint name\n"
            "<b>%(PhotoPlace.WptDESC)s</b> -> Description\n"
            "<b>%(PhotoPlace.WptLAT)s</b>  -> Latitude\n"
            "<b>%(PhotoPlace.WptLON)s</b>  -> Longitude\n"
            "<b>%(PhotoPlace.WptELE)s</b>  -> Altitude\n"
            "<b>%(PhotoPlace.WptTIME)s</b> -> UTC Time\n"
            "</span>")
            autocompletions = [
                PhotoPlace_WptNAME,
                PhotoPlace_WptDESC,
                PhotoPlace_WptLAT,
                PhotoPlace_WptLON,
                PhotoPlace_WptELE,
                PhotoPlace_WptTIME,
            ]
        else:
            tooltip = _("\n<span font_family='monospace' size='small'>"
            "<b>%(PhotoPlace.PathNAME)s</b>   -> Path name\n"
            "<b>%(PhotoPlace.PathDESC)s</b>   -> Path description\n"
            "<b>%(PhotoPlace.PathTINI)s</b>   -> Initial time (first point)\n"
            "<b>%(PhotoPlace.PathTEND)s</b>   -> End time (last point)\n"
            "<b>%(PhotoPlace.PathDRTN)s</b>   -> Duration\n"
            "<b>%(PhotoPlace.PathLEN)s</b>    -> Length (in meters)\n"
            "<b>%(PhotoPlace.PathLENMIN)s</b> -> Minimum length\n"
            "<b>%(PhotoPlace.PathLENMAX)s</b> -> Maximum length\n"
            "<b>%(PhotoPlace.PathSPMIN)s</b>  -> Minimum speed (m/s)\n"
            "<b>%(PhotoPlace.PathSPMAX)s</b>  -> Maximum speed (m/s)\n"
            "<b>%(PhotoPlace.PathSPAVG)s</b>  -> Average speed (m/s)\n"
            "<b>%(PhotoPlace.PathNSEG)s</b>   -> Number of segments\n"
            "<b>%(PhotoPlace.PathNWPT)s</b>   -> Number of waypoints\n"
            "</span>")
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
        text = ''
        filename = None
        if style != None:
            if kind == _GTKGPXData_TYPE_WPT:
                if style.has_key(GPXData_CONFKEY_WPT_DESC):
                    text = style[GPXData_CONFKEY_WPT_DESC]
                if style.has_key(GPXData_CONFKEY_WPT_FTEMPLATE):
                    filename = style[GPXData_CONFKEY_WPT_FTEMPLATE]
            elif kind == _GTKGPXData_TYPE_TRACK:
                if style.has_key(GPXData_CONFKEY_TRACKS_DESC):
                    text = style[GPXData_CONFKEY_TRACKS_DESC]
                if style.has_key(GPXData_CONFKEY_TRACKS_FTEMPLATE):
                    filename = style[GPXData_CONFKEY_TRACKS_FTEMPLATE]
            else:
                if style.has_key(GPXData_CONFKEY_TRACKS_DESC):
                    text = style[GPXData_CONFKEY_TRACKS_DESC]
                if text == None:
                    text = self.tracksinfo[0][GPXData_CONFKEY_TRACKS_DESC]
            self.windoweditor.show(text=text, template=filename, recover=filename,
                completions=completions, tooltip=tooltip, cansave=False)
            self.windoweditor.connect('close', self._editor_setdesc, style, kind, obj_id)
        else:
            cansave = True
            if kind == _GTKGPXData_TYPE_PATH:
                filename = self.tracksinfo[0][GPXData_CONFKEY_TRACKS_FTEMPLATE]
                text = self.tracksinfo[0][GPXData_CONFKEY_TRACKS_DESC]
                style = self.tracksinfo[0]
                cansave = False
            elif kind == _GTKGPXData_TYPE_TRACK:
                filename = self.tracksinfo[1][GPXData_CONFKEY_TRACKS_FTEMPLATE]
                text = self.tracksinfo[1][GPXData_CONFKEY_TRACKS_DESC]
                style = self.tracksinfo[1]
            elif kind == _GTKGPXData_TYPE_WPT:
                filename = self.wptsinfo[0][GPXData_CONFKEY_WPT_FTEMPLATE]
                text = self.wptsinfo[0][GPXData_CONFKEY_WPT_DESC]
                style = self.wptsinfo[0]
            if filename or text:
                filename = os.path.basename(filename)
                self.windoweditor.show(text=text, template=filename,
                    completions=completions, tooltip=tooltip, cansave=cansave)
                self.windoweditor.connect('close', self._editor_setdesc, style, kind, obj_id)


    def _editor_setdesc(self, obj, text, template, style, kind, obj_id):
        if kind == _GTKGPXData_TYPE_WPT:
            style[GPXData_CONFKEY_WPT_DESC] = text
        else:
            style[GPXData_CONFKEY_TRACKS_DESC] = text


    def _activate_setdesc(self, widget, style, kind, obj_id, text=None):
        if kind == _GTKGPXData_TYPE_WPT:
            style[GPXData_CONFKEY_WPT_DESC] = text
        elif kind == _GTKGPXData_TYPE_PATH:
            style[GPXData_CONFKEY_TRACKS_DESC] = text
        else:
            style[GPXData_CONFKEY_TRACKS_DESC] = text


    def _toggled_row(self, widget, path_string):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        obj_id = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ID)
        kind = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_TYPE)
        if obj_id >= 0:
            value = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ACT)
            value = not value
            self.treestore.set(treestore_iter, _GTKGPXData_COLUMN_ACT, value)
            if kind == _GTKGPXData_TYPE_WPT:
                wpt = self.wptlist[obj_id]
                wpt.status = int(value)
            elif kind == _GTKGPXData_TYPE_PATH:
                path = self.pathlist[obj_id]
                path.status = int(value)
            elif kind == _GTKGPXData_TYPE_TRACK:
                track = self.tracklist[obj_id]
                track.status = int(value)


    def _edit_cell(self, cell, path_string, new_text, column):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_KEY)
        if column == _GTKGPXData_COLUMN_TYPE_VALUE:
            obj_id = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ID)
            kind = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_TYPE)
            if key == GPXData_CONFKEY_TRACKS_WIDTH:
                try:
                    new = int(new_text)
                    self.treestore.set(treestore_iter, _GTKGPXData_COLUMN_VALUE, new_text)
                    if kind == _GTKGPXData_TYPE_PATH:
                        self.pathstyles[obj_id][GPXData_CONFKEY_TRACKS_WIDTH] = new_text
                    else:
                        self.trackstyles[obj_id][GPXData_CONFKEY_TRACKS_WIDTH] = new_text
                except:
                    pass
            elif key == GPXData_CONFKEY_TRACKS_NAME:
                if kind == _GTKGPXData_TYPE_WPT:
                    wpt = self.wptlist[obj_id]
                    wpt.attr['desc'] = str(new_text)
                elif kind == _GTKGPXData_TYPE_PATH:
                    path = self.pathlist[obj_id]
                    path.desc = str(new_text)
                elif kind == _GTKGPXData_TYPE_TRACK:
                    track = self.tracklist[obj_id]
                    track.desc = str(new_text)
                self.treestore.set(treestore_iter, _GTKGPXData_COLUMN_VALUE, new_text)
        else:
            if key == GPXData_CONFKEY_TRACKS_NAME:
                old_name = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_VKEY)
                obj_id = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ID)
                kind = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_TYPE)
                if kind == _GTKGPXData_TYPE_WPT:
                    wpt = self.wptlist[obj_id]
                    wpt.attr['name'] = str(new_text)
                elif kind == _GTKGPXData_TYPE_PATH:
                    path = self.pathlist[obj_id]
                    path.name = str(new_text)
                elif kind == _GTKGPXData_TYPE_TRACK:
                    track = self.tracklist[obj_id]
                    track.name = str(new_text)
                self.treestore.set(treestore_iter, _GTKGPXData_COLUMN_VKEY, new_text)


    def _edit_property(self, cellrenderer, editable, path_string):
        treestore_iter = self.treestore.get_iter_from_string(path_string)
        key = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_KEY)
        obj_id = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_ID)
        kind = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_TYPE)
        if kind == _GTKGPXData_TYPE_WPT or obj_id < 0:
            return
        if key == GPXData_CONFKEY_TRACKS_COLOR:
            value = self.treestore.get_value(treestore_iter, _GTKGPXData_COLUMN_VALUE)
            color = self._show_color(value)
            if color:
                self.treestore.set(treestore_iter, _GTKGPXData_COLUMN_VALUE, color)
                if kind == _GTKGPXData_TYPE_PATH:
                    self.pathstyles[obj_id][GPXData_CONFKEY_TRACKS_COLOR] = color
                elif kind == _GTKGPXData_TYPE_TRACK:
                    self.trackstyles[obj_id][GPXData_CONFKEY_TRACKS_COLOR] = color


    def _show_color(self, value, title=_("Select a color for path ...")):
        dialog =  gtk.ColorSelectionDialog(title)
        colorsel = dialog.get_color_selection()
        colorsel.set_has_opacity_control(True)
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
        dialog.destroy()
        return color_str


#EOF
