#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       GTKcsvimport.py
#
#       Copyright 2014 Jose Riguera Lopez <jriguera@gmail.com>
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
Parse a CSV to add variables or geolocate photos. GTK User Interface.
"""
__program__ = "photoplace.csvimport"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.0"
__date__ = "July 2014"
__license__ = "GPL v3"
__copyright__ ="(c) Jose Riguera"


import os.path
import csv
import sys
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

from csvimport import *


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



class GTKCSVImport(object):

    def __init__(self, plugin, gui, userfacade, logger):
        object.__init__(self)
        self.plugin = gtk.VBox(False)
        self.logger = logger
        self.options = None
        self.userfacade = userfacade
        # 1st line
        hbox = gtk.HBox(False)
        label_name = gtk.Label()
        align = gtk.Alignment(0.01, 0.5, 0, 0)
        label_name.set_markup(_("CSV file:"))
        align.add(label_name)
        hbox.pack_start(align, False, False, 5)
        self.button_addfile = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self.button_addfile.set_image(image)
        self.button_addfile.set_tooltip_text(_("Select a CSV file to load photo's variables"))
        self.button_addfile.set_label(_("Select file"))
        self.button_addfile.connect('clicked', self._load_csv)
        align = gtk.Alignment(0.01, 0.5, 0, 0)
        align.add(self.button_addfile)
        hbox.pack_start(align, False, False, 5)
        self.plugin.pack_start(hbox, False, False, 5)
        # 3rd line
        hbox_headers = gtk.HBox(False)
        label_headers = gtk.Label()
        label_headers.set_markup(_("Headers:"))
        hbox_headers.pack_start(label_headers, False, False, 5)
        self.entry_headers = gtk.Entry(max=256)
        self.entry_headers.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADERS)
        self.entry_headers.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADERS)
        self.entry_headers.set_tooltip_text(_("List of column headers of the CSV file. Each header will be a variable for each photo"))
        self.entry_headers.set_sensitive(False)
        hbox_headers.pack_start(self.entry_headers, True, True, 2)
        label_headerid = gtk.Label()
        label_headerid.set_markup(_("where photo name is:"))
        hbox_headers.pack_start(label_headerid, False, False, 0)
        self.entry_headerid = gtk.Entry(max=32)
        self.entry_headerid.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADER_ID)
        self.entry_headerid.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADER_ID)
        self.entry_headerid.set_tooltip_text(_("Name of the column to match with each photo file name. It must be one of the Headers"))
        self.entry_headerid.set_sensitive(False)
        hbox_headers.pack_start(self.entry_headerid, False, False, 5)
        self.plugin.pack_start(hbox_headers, False, False, 5)
        # 4st line
        self.checkbutton_geolocate = gtk.CheckButton(_("Geolocate photos using CSV headers"))
        self.checkbutton_geolocate.set_tooltip_text(_("It is active, it will assign the following headers to each photo. It will geotag the photos by using those headers, but, warning: GPX data will take precedence!"))
        self.checkbutton_geolocate.connect('toggled', self._geolocate)
        self.checkbutton_geolocate.set_sensitive(False)
        # Headers Variables
        self.frame = gtk.Frame()
        self.frame.set_label_widget(self.checkbutton_geolocate)
        table = gtk.Table(2, 4, True)
        label_lat = gtk.Label()
        label_lat.set_markup(_("Latitude:"))
        align = gtk.Alignment(1.00, 0.5, 0, 0)
        align.add(label_lat)
        table.attach(align, 0, 1, 0, 1, gtk.FILL)
        self.entry_lat = gtk.Entry(max=256)
        self.entry_lat.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADER_LAT)
        self.entry_lat.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADER_LAT)
        self.entry_lat.set_tooltip_text(_("Latitude header name"))
        table.attach(self.entry_lat, 1, 2, 0, 1)
        label_lon = gtk.Label()
        label_lon.set_markup(_("Longitude:"))
        align = gtk.Alignment(1.00, 0.5, 0, 0)
        align.add(label_lon)
        table.attach(align, 2, 3, 0, 1, gtk.FILL)
        self.entry_lon = gtk.Entry(max=256)
        self.entry_lon.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADER_LON)
        self.entry_lon.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADER_LON)
        self.entry_lon.set_tooltip_text(_("Longitude header name"))
        table.attach(self.entry_lon, 3, 4, 0, 1)
        label_date = gtk.Label()
        label_date.set_markup(_("Time-Date:"))
        align = gtk.Alignment(1.00, 0.5, 0, 0)
        align.add(label_date)
        table.attach(align, 0, 1, 1, 2)
        self.entry_date = gtk.Entry(max=256)
        self.entry_date.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADER_DATE)
        self.entry_date.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADER_DATE)
        table.attach(self.entry_date, 1, 2, 1, 2)
        label_ele = gtk.Label()
        label_ele.set_markup(_("Elevation:"))
        align = gtk.Alignment(1.00, 0.5, 0, 0)
        align.add(label_ele)
        table.attach(align, 2, 3, 1, 2)
        self.entry_ele = gtk.Entry(max=256)
        self.entry_ele.connect('activate', self._set_entry, CSVImport_CONFKEY_HEADER_ELE)
        self.entry_ele.connect('focus-out-event', self._out_entry, CSVImport_CONFKEY_HEADER_ELE)
        self.entry_ele.set_tooltip_text(_("Elevation header name"))
        table.attach(self.entry_ele, 3, 4, 1, 2)
        table.set_border_width(20)
        table.set_row_spacings(5)
        self.frame.add(table)
        self.frame.set_border_width(5)
        self.frame.set_sensitive(False)
        self.plugin.pack_start(self.frame, False, False, 5)
        # Button
        self.button_process = gtk.Button()
        self.button_process.set_label(_("Process"))
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.button_process.set_image(image)
        self.button_process.connect('clicked', self.process)
        align = gtk.Alignment(0.50, 0.5, 0.1, 0)
        align.add(self.button_process)
        self.plugin.pack_start(align, False, False, 0)
        self.button_process.set_sensitive(False)
        # Attributes
        self.rootplugin = plugin
        self.rootgui = gui
        self.window = gui.builder.get_object("window")


    def _load_csv(self, widget):
        dialog = gtk.FileChooserDialog(title=_("Select CSV file ..."),
            parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("Comma Separated Values (CSV)"))
        ffilter.add_pattern("*.csv")
        dialog.add_filter(ffilter)
        ffilter = gtk.FileFilter()
        ffilter.set_name(_("All files"))
        ffilter.add_pattern("*")
        dialog.add_filter(ffilter)
        filename = None
        if dialog.run() == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
        dialog.destroy()
        self._set_csv(filename)


    def _set_csv(self, filename):
        if filename != None and os.path.isfile(filename):
            if not isinstance(filename, unicode):
                try:
                    filename = unicode(filename, 'UTF-8')
                except:
                    pass
            shortfilename = "   " + os.path.basename(filename) + "   "
            if len(shortfilename) > 150:
                shortfilename =  shortfilename[0:150] + " ... "
            image = self.button_addfile.get_image()
            image.clear()
            self.button_addfile.set_label(shortfilename)
            self.frame.set_sensitive(True)
            self.checkbutton_geolocate.set_sensitive(True)
            self.entry_headerid.set_sensitive(True)
            self.entry_headers.set_sensitive(True)
            self.button_process.set_sensitive(True)
            self._init_csv(filename)
            self._geolocate()
        else:
            self.reset()


    def _init_csv(self, filename):
        dgettext = dict()
        dgettext['file'] = filename
        try:
            fd = open(filename, 'rb')
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot read file '%(file)s': %(error)s")
            self.logger.error(msg % dgettext)
            self.rootgui.show_dialog(_("Error"), msg, _('Please check file permisions'))
        else:
            dialect = 'excel'
            headers = self.options[CSVImport_CONFKEY_HEADERS]
            delimiter = self.options[CSVImport_CONFKEY_DELIMITER]
            quotechar = self.options[CSVImport_CONFKEY_QUOTECHAR]
            if not delimiter or not quotechar:
                dialect = csv.Sniffer().sniff(fd.read(1024))
                delimiter = dialect.delimiter
                quotechar = dialect.quotechar
                fd.seek(0)
            else:
                dgettext['delimiter'] = delimiter
                dgettext['quotechar'] = quotechar
            has_header = csv.Sniffer().has_header(fd.read(1024))
            fd.seek(0)
            headers_defined = False
            if headers:
                headers_defined = True
            else:
                reader = csv.DictReader(fd, dialect=dialect, delimiter=delimiter, quotechar=quotechar)
                if has_header:
                    reader.next()
                    headers = reader.fieldnames
                    headers_defined = True
            self.options[CSVImport_CONFKEY_FILENAME] = filename
            if not headers_defined:
                msg = _("File has no headers")
                tip = _('You have to define the name of the headers.')
                self.rootgui.show_dialog(_("Warning"), msg, tip, gtk.MESSAGE_WARNING)
            else:
                self.entry_headers.set_text(', '.join(headers))
                self.entry_headerid.set_text(headers[0])
                self.options[CSVImport_CONFKEY_HEADER_ID] = headers[0]
                self.rootplugin.update_headers(headers)
            fd.close()


    def process(self, widget=None):
        filename = self.options[CSVImport_CONFKEY_FILENAME]
        if filename != None:
            self.rootplugin.init_csv(filename)
            counter = self.rootplugin.process_csv(self.userfacade.state.geophotos)
            self.rootplugin.logger.info(_("%d photos processed with CSV data.") % counter)
            self.rootplugin.end_csv()
            self.rootgui.reload_treeviewgeophotos()


    def _geolocate(self, widget=None):
        value = self.checkbutton_geolocate.get_active()
        self.entry_date.set_sensitive(value)
        self.entry_ele.set_sensitive(value)
        self.entry_lon.set_sensitive(value)
        self.entry_lat.set_sensitive(value)
        self.options[CSVImport_CONFKEY_GEOLOCATE] = value
        if not value:
            header = ''
            self.options[CSVImport_CONFKEY_HEADER_LAT] = header
            self.options[CSVImport_CONFKEY_HEADER_LON] = header
            self.options[CSVImport_CONFKEY_HEADER_ELE] = header
            self.options[CSVImport_CONFKEY_HEADER_DATE] = header
            self.entry_lat.set_text(header)
            self.entry_lon.set_text(header)
            self.entry_ele.set_text(header)
            self.entry_date.set_text(header)
        else:
            for i in self.options[CSVImport_CONFKEY_HEADERS]:
                item = i.lower()
                if 'lat' in item:
                    self.entry_lat.set_text(i)
                    self.options[CSVImport_CONFKEY_HEADER_LAT] = i
                elif 'lon' in item:
                    self.entry_lon.set_text(i)
                    self.options[CSVImport_CONFKEY_HEADER_LON] = i
                elif 'ele' in item:
                    self.entry_ele.set_text(i)
                    self.options[CSVImport_CONFKEY_HEADER_ELE] = i
                elif 'date' in item or 'time' in item:
                    self.entry_date.set_text(i)
                    self.options[CSVImport_CONFKEY_HEADER_DATE] = i


    def _out_entry(self, widget, e, key):
        if key == CSVImport_CONFKEY_HEADERS:
            widget.set_text(', '.join(self.options[key]))
        else:
            widget.set_text(self.options[key])
        return False


    def _set_entry(self, widget, key):
        value = widget.get_text()
        if key == CSVImport_CONFKEY_HEADERS:
            items = []
            try:
                char = None
                for c in [',', ';', '|', '#']:
                    if c in value:
                        char = c
                        break
                else:
                    raise Exception
                for item in value.split(char):
                    items.append(item.strip())
                if len(items) < 2:
                    raise Exception
            except:
                msg = _("Cannot set headers")
                tip = _("Please, define the name of the headers to be used as variables.")
                self.rootgui.show_dialog(_("Error"), msg, tip)
            else:
                self.rootplugin.update_headers(items)
        else:
            if value in self.options[CSVImport_CONFKEY_HEADERS]:
                self.options[key] = value
            else:
                msg = _("Cannot find header")
                tip = _("Please, use the name of a header.")
                self.rootgui.show_dialog(_("Error"), msg, tip)


    def show(self, widget=None, options=None):
        if widget:
            widget.add(self.plugin)
        if options:
            self.setup(options)
        self.plugin.show_all()


    def hide(self, reset=False):
        self.plugin.hide_all()
        if reset:
            self.reset()


    def reset(self):
        header = ''
        self.button_process.set_sensitive(False)
        self.checkbutton_geolocate.set_sensitive(False)
        self.frame.set_sensitive(False)
        self.entry_headerid.set_sensitive(False)
        self.entry_headers.set_sensitive(False)
        self.entry_headers.set_text(header)
        self.entry_headerid.set_text(header)
        image = self.button_addfile.get_image()
        image.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self.button_addfile.set_image(image)
        self.button_addfile.set_label(_("Select file"))
        self.checkbutton_geolocate.set_active(False)
        self.options[CSVImport_CONFKEY_FILENAME] = header
        self.rootplugin.update_headers()
        self.options[CSVImport_CONFKEY_HEADER_ID] = header
        self.userfacade.state.photovariables = self.rootplugin.photovariables_old
        self._geolocate()
        self.rootgui.reload_treeviewgeophotos()


    def setup(self, options):
        self.options = options
        self.entry_date.set_tooltip_text(_("Date header name. Format should be: ") + self.options[CSVImport_CONFKEY_DATE_PARSE])
        filename = options[CSVImport_CONFKEY_FILENAME]
        if filename:
            self._set_csv(filename)
            self.entry_headers.set_text(', '.join(options[CSVImport_CONFKEY_HEADERS]))
            self.entry_headerid.set_text(options[CSVImport_CONFKEY_HEADERS][0])
        if options[CSVImport_CONFKEY_GEOLOCATE]:
            self.checkbutton_geolocate.set_active(True)
            header = self.options[CSVImport_CONFKEY_HEADER_LAT]
            if header:
                self.entry_lat.set_text(header)
            header = self.options[CSVImport_CONFKEY_HEADER_LON]
            if header:
                self.entry_lon.set_text(header)
            header = self.options[CSVImport_CONFKEY_HEADER_ELE]
            if header:
                self.entry_ele.set_text(header)
            header = self.options[CSVImport_CONFKEY_HEADER_DATE]
            if header:
                self.entry_date.set_text(header)


#EOF
