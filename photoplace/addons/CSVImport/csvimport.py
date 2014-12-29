#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       csvimport.py
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
Parse a CSV to add variables or geolocate photos.
"""
__program__ = "photoplace.csvimport"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.2"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


import os.path
import gettext
import locale
import csv

from PhotoPlace.Plugins.Interface import *
from PhotoPlace.definitions import *
from PhotoPlace.Facade import Error


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


# Configuration keys
CSVImport_CONFKEY = 'csvimport'
CSVImport_CONFKEY_FILENAME = 'csvfile'
CSVImport_CONFKEY_ENCODINGS = 'csvencodings'
CSVImport_CONFKEY_HEADERS = 'headers'
CSVImport_CONFKEY_DELIMITER = 'delimiter'
CSVImport_CONFKEY_QUOTECHAR = 'quotechar'
CSVImport_CONFKEY_DATE_PARSE = 'dateparse'
CSVImport_CONFKEY_HEADER_ID = 'headerphoto'
CSVImport_CONFKEY_HEADER_LAT = 'headerlat'
CSVImport_CONFKEY_HEADER_LON = 'headerlon'
CSVImport_CONFKEY_HEADER_ELE = 'headerele'
CSVImport_CONFKEY_HEADER_DATE = 'headerdate'
CSVImport_CONFKEY_GEOLOCATE = 'geolocate'

# Default values
CSVImport_ENCODINGS = ['utf-8', 'windows-1252', 'latin1',  'windows-1250', 'iso-8859-1','iso-8859-2', 'us-ascii']
CSVImport_DATE_PARSE = "%Y-%m-%dT%H:%M:%S"
CSVImport_HEADER_ID = 'PHOTO'
CSVImport_HEADER_LAT = ''
CSVImport_HEADER_LON = ''
CSVImport_HEADER_ELE = ''
CSVImport_HEADER_DATE = ''
CSVImport_GEOLOCATE = False
CSVImport_HEADERS = []
CSVImport_DELIMITER = None
CSVImport_QUOTECHAR = None


class CSVImport(Plugin):

    description = _(
        "Parse a CSV to add variables or geolocate photos."
    )
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://www.photoplace.io"
    version = __version__
    copyright = __copyright__
    date = __date__
    license = __license__
    capabilities = {
        'GUI' : PLUGIN_GUI_GTK,
        'UI' : False,
    }


    def __init__(self, logger, userfacade, args, argfiles=[], gui=None):
        Plugin.__init__(self, logger, userfacade, args, argfiles, gui)
        self.options = dict()
        self.fd = None
        self.reader = None
        # GTK widgets
        self.pgui = None
        if gui:
            import GTKcsvimport
            self.pgui = GTKcsvimport.GTKCSVImport(self, gui, userfacade, logger)
        self.ready = -1


    def init(self, options, widget):
        if not options.has_key(CSVImport_CONFKEY):
            options[CSVImport_CONFKEY] = dict()
        opt = options[CSVImport_CONFKEY]
        self.options = None
        self.process_variables(opt)
        self.photovariables_old = list(self.userfacade.state.photovariables)
        if self.pgui:
            if self.ready == -1:
                # 1st time
                self.pgui.show(widget, self.options)
            else:
                self.pgui.show(None, self.options)
        self.ready = 1
        self.logger.debug(_("Starting add-on ..."))


    def _set_option_bool(self, options, key, value):
        current = options.setdefault(key, value)
        if not isinstance(current, bool):
            new = current.lower().strip() in ["yes", "true", "on", "si", "1"]
            options[key] = new


    def _set_option_list(self, options, key, value=[]):
        items = options.setdefault(key, value)
        if not isinstance(items, list):
            items = []
            try:
                char = None
                for c in [',', ';', '|', '#']:
                    if c in options[key]:
                        char = c
                        break
                else:
                    raise Exception
                for item in options[key].split(char):
                    items.append(item.strip())
            except:
                self.logger.error(_("Incorrect value for '%s'.") % key)
            options[key] = items


    def process_variables(self, options):
        self._set_option_bool(options, CSVImport_CONFKEY_GEOLOCATE, CSVImport_GEOLOCATE)
        options.setdefault(CSVImport_CONFKEY_DELIMITER, CSVImport_DELIMITER)
        options.setdefault(CSVImport_CONFKEY_QUOTECHAR, CSVImport_QUOTECHAR)
        options.setdefault(CSVImport_CONFKEY_DATE_PARSE, CSVImport_DATE_PARSE)
        options.setdefault(CSVImport_CONFKEY_HEADER_ID, CSVImport_HEADER_ID)
        options.setdefault(CSVImport_CONFKEY_HEADER_LAT, CSVImport_HEADER_LAT)
        options.setdefault(CSVImport_CONFKEY_HEADER_LON, CSVImport_HEADER_LON)
        options.setdefault(CSVImport_CONFKEY_HEADER_ELE, CSVImport_HEADER_ELE)
        options.setdefault(CSVImport_CONFKEY_HEADER_DATE, CSVImport_HEADER_DATE)
        self._set_option_list(options, CSVImport_CONFKEY_HEADERS, CSVImport_HEADERS)
        self._set_option_list(options, CSVImport_CONFKEY_ENCODINGS, CSVImport_ENCODINGS)
        filename = None
        for argfile in self.argfiles:
            if os.path.splitext(argfile)[1].lower() == '.csv':
                filename = argfile
                break
        else:
            filename = options.setdefault(CSVImport_CONFKEY_FILENAME)
        if filename != None:
            filename = os.path.expandvars(os.path.expanduser(filename))
            try:
                filename = unicode(filename, PLATFORMENCODING)
            except:
                pass
            options[CSVImport_CONFKEY_FILENAME] = filename
        self.options = options


    def init_csv(self, filename):
        dgettext = dict()
        dgettext['file'] = filename
        self.fd = None
        self.reader = None
        try:
            self.fd = open(filename, 'rb')
        except Exception as e:
            dgettext['error'] = str(e)
            msg = _("Cannot read file '%(file)s': %(error)s")
            self.logger.error(msg % dgettext)
        else:
            dialect = 'excel'
            headers = self.options[CSVImport_CONFKEY_HEADERS]
            dgettext['headers'] = headers
            delimiter = self.options[CSVImport_CONFKEY_DELIMITER]
            quotechar = self.options[CSVImport_CONFKEY_QUOTECHAR]
            if not delimiter or not quotechar:
                dialect = csv.Sniffer().sniff(self.fd.read(1024))
                delimiter = dialect.delimiter
                quotechar = dialect.quotechar
                self.fd.seek(0)
                msg = _("Processing CSV '%(file)s' with automatic format.")
            else:
                dgettext['delimiter'] = delimiter
                dgettext['quotechar'] = quotechar
                msg = _("Processing CSV '%(file)s' data (with delimiter='%(delimiter)s', quotechar='%(quotechar)s', headers='%(headers)s').")
            self.logger.info(msg % dgettext)
            has_header = csv.Sniffer().has_header(self.fd.read(1024))
            self.fd.seek(0)
            if headers:
                self.update_headers(headers)
                self.reader = csv.DictReader(self.fd, fieldnames=headers, dialect=dialect, delimiter=delimiter, quotechar=quotechar)
                if has_header:
                    self.reader.next()
            else:
                self.reader = csv.DictReader(self.fd, dialect=dialect, delimiter=delimiter, quotechar=quotechar)
                if has_header:
                    #headers = self.reader.next()
                    self.update_headers(headers)
                else:
                    msg = _("CSV '%(file)s' has no headers and you have not defined them!")
                    self.logger.error(msg % dgettext)
                    self.end_csv()


    def update_headers(self, headers=[]):
        for variable in self.options[CSVImport_CONFKEY_HEADERS]:
            try:
                self.userfacade.state.photovariables.remove(variable)
            except ValueError:
                pass
        self.options[CSVImport_CONFKEY_HEADERS] = headers
        keys = [ CSVImport_CONFKEY_HEADER_ID,
            CSVImport_CONFKEY_HEADER_LAT,
            CSVImport_CONFKEY_HEADER_LON,
            CSVImport_CONFKEY_HEADER_ELE,
            CSVImport_CONFKEY_HEADER_DATE
        ]
        for variable in headers:
            append = True
            for key in keys:
                if variable in self.options[key]:
                    append = False
                    break
            if append:
                if not variable in self.userfacade.state.photovariables:
                    self.userfacade.state.photovariables.append(variable)


    def end_csv(self):
        if self.fd:
            self.fd.close()
            self.fd = None
            self.reader = None


    def process_csv(self, geophotos):
        if self.reader == None:
            return 0
        line = 0
        num_photos = 0
        geolocate = self.options[CSVImport_CONFKEY_GEOLOCATE]
        date_parse = self.options[CSVImport_CONFKEY_DATE_PARSE]
        header_id = self.options[CSVImport_CONFKEY_HEADER_ID]
        header_lat = self.options[CSVImport_CONFKEY_HEADER_LAT]
        header_lon = self.options[CSVImport_CONFKEY_HEADER_LON]
        header_ele = self.options[CSVImport_CONFKEY_HEADER_ELE]
        header_date = self.options[CSVImport_CONFKEY_HEADER_DATE]
        dgettext = dict()
        try:
            for row in self.reader:
                # print "FILA", line, row
                # utf-8 -> unicode because CSV works in utf-8!!
                photo_id = ''
                lat = None
                lon = None
                ele = None
                date = None
                variables = dict()
                for k,v in row.iteritems():
                    for enc in CSVImport_ENCODINGS:
                        try:
                            row[k] = unicode(v, enc, "strict")
                            break
                        except:
                            pass
                    else:
                        row[k] = v
                    if header_id and k == header_id:
                        photo_id = row[k]
                    elif geolocate and header_lat and k == header_lat:
                        lat = float(row[k])
                    elif geolocate and header_lon and k == header_lon:
                        lon = float(row[k])
                    elif geolocate and header_ele and k == header_ele:
                        ele = float(row[k])
                    elif geolocate and header_date and k == header_date:
                        date = datetime.datetime.strptime(row[k], date_parse)
                    else:
                        variables[k] = row[k]
                line += 1
                dgettext['line'] = line
                dgettext['name'] = photo_id
                #self.logger.debug(_("CSV[%(line)s]: " % dgettext) + str(row))
                found_photo = False
                for photo in geophotos:
                    if os.path.basename(photo.path) == photo_id:
                        found_photo = True
                        photo.attr.update(variables)
                        if geolocate:
                            dgettext['lat'] = 0
                            dgettext['lon'] = 0
                            if lat != None and lon != None:
                                photo.lat = lat
                                photo.lon = lon
                                dgettext['lat'] = lat
                                dgettext['lon'] = lon
                            if ele != None:
                                photo.ele = ele
                            msg = _("Geotagging photo '%(name)s': (lon=%(lon).8f, lat=%(lat).8f).")
                            self.logger.info(msg % dgettext)
                        num_photos += 1
                        break
                if not found_photo:
                    msg = _("CSV[%(line)s]: Photo '%(name)s' not found!")
                    self.logger.warning(msg % dgettext)
        except Exception as e:
            dgettext['line'] = line + 1
            dgettext['error'] = str(e)
            self.logger.error(_("Cannot read CSV[%(line)s]: %(error)s.") % dgettext)
        return num_photos


    @DRegister("LoadPhotos:end")
    def loadphotos(self, num_photos):
        filename = self.options[CSVImport_CONFKEY_FILENAME]
        if filename != None:
            self.init_csv(filename)
            counter = self.process_csv(self.state.geophotos)
            self.logger.info(_("%d photos processed with CSV data.") % counter)
            self.end_csv()


    def end(self, options):
        self.ready = 0
        self.end_csv()
        self.userfacade.state.photovariables = self.photovariables_old
        if self.pgui:
            self.pgui.hide(True)
        self.logger.debug(_("Ending add-on ..."))


# EOF
