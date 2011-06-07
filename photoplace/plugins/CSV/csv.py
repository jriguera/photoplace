#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       csv.py:  csv plugin for photoplace
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright © 2008 Jose Riguera Lopez <jriguera@gmail.com>
#
"""
A plugin for PhotoPlace to read CSV data.
"""
__program__ = "photoplace.csv"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.2.0"
__date__ = "March 2011"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import sys
import time
import codecs
import datetime
import urlparse
import gettext
import locale


# I18N gettext support
__GETTEXT_DOMAIN__ = __program__
__PACKAGE_DIR__ = os.path.dirname(__file__)
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    gettext.install(__GETTEXT_DOMAIN__, __LOCALE_DIR__)
except Exception as e:
    _ = lambda s: s
    print("Error setting up the translations: %s" % (e))


from PhotoPlace.userFacade import TemplateDict
from PhotoPlace.Plugins.Interface import *
from PhotoPlace.definitions import *


PhotoPlace_Cfg_csv_headers = [] # ["PHOTO", "TITLE", "DESCRIPTION", "LAT", "LON", "ELE"]
PhotoPlace_Cfg_csv_quotechar = ';'
PhotoPlace_Cfg_csv_delimiter = '"'
PhotoPlace_Cfg_csv_photonameheader = '' #"PHOTO"
PhotoPlace_Cfg_csv_photolatheader = '' #"LAT"
PhotoPlace_Cfg_csv_photolonheader =  '' #"LON"
PhotoPlace_Cfg_csv_photoeleheader = '' #"ELE"
PhotoPlace_Cfg_csv_encodings = ["utf-8", "iso-8859-1", "iso-8859-2", "us-ascii"]


def check_config(options):
    if options['main'].has_key('gpxinputfile'):
        options['main']['gpxinputfile'] = os.path.expandvars(options['main']['gpxinputfile'])
        if not os.path.isfile(options['main']['gpxinputfile']):
            errors.append(_("Input GPX file '%s' does not exists!.") % \
                options['main']['gpxinputfile'])

#        # csv section
#    if options['csv'].has_key('headers'):
#        options['csv']['headers'] = options['csv']['headers'].split()
#    else:
#        options['csv']['headers'] = PhotoPlace_Cfg_csv_headers
#    options['csv'].setdefault('delimiter', PhotoPlace_Cfg_csv_delimiter)
#    options['csv'].setdefault('quotechar', PhotoPlace_Cfg_csv_quotechar)
#    options['csv'].setdefault('photonameheader', PhotoPlace_Cfg_csv_photonameheader)
#    if options['csv'].has_key('encodings'):
#        options['csv']['encodings'] = options['csv']['encodings'].split()
#    else:
#        options['csv']['encodings'] = PhotoPlace_Cfg_csv_encodings



# bajo nivel
def check_cvs_file(fd, options):
    """
    It does some checks with CSV configuration. Checks the existence of headers ...
    """
    headers = options['csv']['headers']
    delimiter = options['csv']['delimiter']
    quotechar = options['csv']['quotechar']
    photonameheader = options['csv']['photonameheader']
    logger = logging.getLogger('check_cvs_file')
    logger.debug(_("Init. Checking CSV data with options %s.") % options['csv'])
    if not photonameheader :
        msg = _("CSV photo header key not defined. You need to define it in configuration file."
            " It is usually a column with the jpeg filename.")
        logger.error(msg)
        raise ValueError(msg)
    # format check
    dialet_name = PhotoPlace_name
    sniffer = csv.Sniffer()
    try:
        if delimiter :
            dialect = sniffer.sniff(fd.read(1024), delimiter)
        else:
            dialect = sniffer.sniff(fd.read(1024))
        csv.register_dialect(dialet_name, dialect, quotechar=quotechar)
    except Exception as e:
        msg = _("Cannot read CSV data file: '%s'.") % e
        logger.error(msg)
        raise ValueError(msg)
    fd.seek(0)
    # headers check
    if headers :
        if sniffer.has_header(fd.read(1024)):
            fd.seek(0)
            d_gettext = {}
            file_headers = fd.readline()
            d_gettext['f_headers'] = file_headers
            d_gettext['my_headers'] = headers
            logger.debug(_("File has headers [%(f_headers)s], but we are using %(my_headers)s.") \
                % d_gettext)
        reader = csv.DictReader(fd, fieldnames=headers, restkey=None, restval=None, dialect=dialet_name)
    else:
        if not sniffer.has_header(fd.read(1024)):
            fd.seek(0)
            msg = _("File has no headers and that was not specified into configuration file!")
            logger.error(msg)
            raise NameError(msg)
        fd.seek(0)
        reader = csv.DictReader(fd, fieldnames=None, restkey=None, restval=None, dialect=dialet_name)
    options['csv']['headers'] = reader.fieldnames
    logger.debug(_("Using headers '%s' as CSV keys.") % options['csv']['headers'])
    photolatheader = options['csv']['photolatheader']
    photolonheader = options['csv']['photolonheader']
    photoeleheader = options['csv']['photoeleheader']
    msg = _("Cannot found predefined (in configuration file) header '%s' in csv file.")
    if photonameheader not in reader.fieldnames :
        logger.error(msg % photonameheader)
        raise NameError(msg % photolonheader)
    if photolatheader and photolatheader not in reader.fieldnames :
        logger.error(msg % photolatheader)
        raise NameError(msg % photolonheader)
    if photolonheader and photolonheader not in reader.fieldnames :
        logger.error(msg % photolonheader)
        raise NameError(msg % photolonheader)
    if photoeleheader and photoeleheader not in reader.fieldnames :
        logger.error(msg % photoeleheader)
        raise NameError(msg % photolonheader)
    logger.debug(_("End. Checks for CSV file."))
    return (reader, options)


def load_csv(fd, geophotos, options):
    logger = logging.getLogger('load_cvs')
    logger.debug(_("Init. Processing CSV data from '%s' ...") % options['main']['csvinputfile'])
    (reader, options) = check_cvs(fd, options)
    photonameheader = options['csv']['photonameheader']
    photolatheader = options['csv']['photolatheader']
    photolonheader = options['csv']['photolonheader']
    photoeleheader = options['csv']['photoeleheader']
    forcegeolocation = options['jpg']['exivmode'] != 1
    l_headers = options['csv']['headers']
    l_encodings = options['csv']['encoding']
    n_lines = 0
    n_photos = 0
    photo_counter = 0
    # Process
    for row in reader:
        # utf-8 -> unicode because CSV works in utf-8!!
        lat = 100000.0
        lon = 100000.0
        ele = 100000.0
        name = ''
        for k,v in row.iteritems():
            # try to determine the best csv encoding
            key = k.strip()
            for enc in encodings:
                try:
                    data[key] = unicode(v, enc, "strict")
                    break
                except:
                    pass
            else:
                data[key] = v
            # GeoData from selected columns
            try:
                if key == photonameheader :
                    name = data[key]
                elif key == photolatheader:
                    lat = float(data[key])
                elif key == photolonheader:
                    lon = float(data[key])
                elif key == photoeleheader:
                    ele = float(data[key])
            except ValueError as valerror:
                d_gettext = {"line": n_lines, "error": "%s" % valerror }
                logger.warning(_("Cannot process coordinates from CSV in line number %(line)s: "
                    "'%(error)s'.") % d_gettext)
        found_photo = False
        for photo in geophotos:
            if photo.name == name:
                found_photo = True
                photo.attr.update(data)
                d_gettext = {}
                d_gettext['photo'] = photo.name
                d_gettext['photo_time'] = photo.time
                d_gettext['photo_lon'] = photo.lon
                d_gettext['photo_lat'] = photo.lat
                d_gettext['photo_ele'] = photo.ele
                if photo.isGeoLocated() and not forcegeolocation:
                    logger.debug(_("Photo: '%(photo)s' (%(photo_time)s) is geolocated to "
                        "(lon=%(photo_lon).8f, lat=%(photo_lat).8f, ele=%(photo_ele).8f). "
                        "Calculated coordinates ignored due to no overwrite option.") % d_gettext)
                else:
                    fields = 0
                    if ele != 100000.0:
                        photo.ele = ele
                        fields += 1
                    if lat != 100000.0:
                        photo.lat = lat
                        fields += 1
                    if lon != 100000.0:
                        photo.lon = lon
                        fields += 1
                    if fields != 3 :
                        logger.warning(_("Photo: '%(photo)s' (%(photo_time)s) (lon=%(photo_lon).8f, "
                            "lat=%(photo_lat).8f, ele=%(photo_ele).8f). Some coordinates are wrong.") \
                            % d_gettext)
                    else:
                        logger.debug(_("Photo: '%(photo)s' (%(photo_time)s) was geolocated with "
                            "coordinates (lon=%(photo_lon).8f, lat=%(photo_lat).8f, ele=%(photo_ele).8f).") \
                            % d_gettext)
                    photo_counter += 1
                n_photos = n_photos + 1
                break
        if not found_photo:
            logger.warning(_("Photo name '%s' not found in photo dir.") % name)
        n_lines = n_lines + 1
    d_gettext = {'num_photos': n_photos, 'photo_counter': photo_counter, 'total_photos': len(geophotos) }
    logger.debug(_("End. %(num_photos)s (%(photo_counter)s) of %(total_photos)s photos were geolocated.") \
        % d_gettext)
    return n_photos


if __name__ == "__main__":
    print __doc__

