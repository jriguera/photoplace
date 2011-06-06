#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       geoPhotoData.py
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
A module for geolocating images. It can read/write exif and exif.gps data
thanks to pyexiv2 0.2 module.
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "May 2010"
__license__ = "GPL (v3 or later)"
__copyright__ ="(c) Jose Riguera, May 2010"


import os
import time
import datetime
import fractions
try:
    import Image
except ImportError:
    print "Sorry, you don't have the Image (PIL) module installed, and this"
    print "script relies on it. Please install Image (PIL) module to continue."
try:
    import pyexiv2
    version_pyexiv2 = pyexiv2.__version__
except ImportError:
    print "Sorry, you don't have the pyexiv2 >= 0.2 module installed, and this"
    print "script relies on it. Please install pyexiv2 >= 0.2v module and "
    print "Exiv2 library."

from pyGPX import geomath



# ##############################
# Exceptions for GeoPhoto module
# ##############################

class GeoPhotoError(Exception):
    """
    Base class for exceptions in GeoPhoto module.
    """
    def __init__(self, msg='GeoPhotoError!'):
        self.value = msg

    def __str__(self):
        return self.value



# #######################
# GeoPhoto implementation
# #######################

# Default values
_GeoPhoto_DEFAULT_LAT = 0.00001                 # default latitue value
_GeoPhoto_DEFAULT_LON = 0.00001                 # longitude
_GeoPhoto_DEFAULT_ELE = 0.00001                 # elevation
_GeoPhoto_DEFAULT_AZI = 0.0                     # azimut or heading
_GeoPhoto_DEFAULT_TILT = 90.0                   # default tilt with vertical
_GeoPhoto_DEFAULT_TIME = datetime.datetime.min  # time

class GeoPhoto(object):
    """
    Base class geolocalized images (jpeg photos)

    It can read/write (GPSInfo) Exif data from/to jpeg files thanks to the pyexiv2
    implementacion. Moreover, it does not touch jpeg data so, the quality of photos
    is the original. More info about pyexiv2: http://tilloy.net/dev/pyexiv2/
    """
    def __init__(self, path, name='-',
        lat = _GeoPhoto_DEFAULT_LAT,
        lon = _GeoPhoto_DEFAULT_LON,
        ele = _GeoPhoto_DEFAULT_ELE,
        time = _GeoPhoto_DEFAULT_TIME,
        azi = _GeoPhoto_DEFAULT_AZI,
        tilt = _GeoPhoto_DEFAULT_TILT,
        loadexif = True):
        """
        GeoPhoto class constructor. It represents a geolocalized image with
        coordinates and time. Other attributes are allowed in attr internal
        dictionary. Exif data is a object of type pyexiv2.Image.

        :Parameters:
            -`path`: path of the jpeg file.
            -`name`: id name of the photo. $basename(path) if omited.
            -`lat`: The latitude of the photo. Decimal degrees, WGS84 datum.
            -`lon`: The longitude of the photo. Decimal degrees, WGS84 datum.
            -`ele`: Elevation of the photo. Meters.
            -`time`: Time. 'datetime.datetime' class
            -`loadexif`: if true, exif data will be read/written
        """
        object.__init__(self)
        self.path = path
        self.name = name
        self.status = 0
        self.toffset = 0
        if name == "-":
            self.name = os.path.basename(self.path)
        self.exif = None
        self.attr = {}
        self.loadexif = False
        self.ptime = None
        self.time = _GeoPhoto_DEFAULT_TIME
        self.lat = _GeoPhoto_DEFAULT_LAT
        self.lon = _GeoPhoto_DEFAULT_LON
        self.ele = _GeoPhoto_DEFAULT_ELE
        self.azi = _GeoPhoto_DEFAULT_AZI
        self.tilt = _GeoPhoto_DEFAULT_TILT
        self.dgettext = dict(image = self.name)
        self.dgettext['image_path'] = self.path
        if loadexif :
            self.readExif()
        # Args take preference over exif
        if time != _GeoPhoto_DEFAULT_TIME:
            self["time"] = time
        if lat != _GeoPhoto_DEFAULT_LAT:
            self["lat"] = lat
        if lon != _GeoPhoto_DEFAULT_LON:
            self["lon"] = lon
        if ele != _GeoPhoto_DEFAULT_ELE:
            self["ele"] = ele
        if azi != _GeoPhoto_DEFAULT_AZI:
            self["azi"] = azi
        if tilt != _GeoPhoto_DEFAULT_TILT:
            self["tilt"] = tilt


    def __getitem__(self, key):
        k = str(key)
        keys = [
            "name",
            "lat",
            "lon",
            "ele",
            "time",
            "azi",
            "tilt",
            "status",
            "toffset"
            "ptime"
        ]
        if k in keys:
            return getattr(self, key)
        else:
            if self.loadexif and k in self.exif.exif_keys:
                data = self.exif[k]
                return data.value
            else:
                return self.attr[k]


    def __setitem__(self, key, value):
        k = str(key)
        if k == "name":
            self.name = value
        elif k == "lat":
            if value < -90.0 or value > 90.0:
                msg = _("latitude = '%f', value not in [-90.0..90.0] range")
                raise ValueError(msg % value)
            self.lat = value
        elif k == "lon":
            if value < -180.0 or value > 180.0:
                msg = _("longitude = '%f', value not in [-180.0..180.0] range")
                raise ValueError(msg % value)
            self.lon = value
        elif k == "ele":
            self.ele = value
        elif k == "time":
            self.time = value
        elif k == "azi":
            if value < 0.0 or value > 360.0:
                msg = _("azimut = '%f', value not in [0.0..360.0] range")
                raise ValueError(msg % value)
            self.azi = value
        elif k == "tilt":
            if value < 0.0 or value > 360.0:
                msg = _("tilt = '%f', value not in [-180.0..180.0] range")
                raise ValueError(msg % value)
            self.tilt = value
        elif k == "status":
            self.status = value
        elif k == "toffset":
            self.toffset = value
        elif k == "ptime":
            self.ptime = value
        else:
            if self.loadexif and k in self.exif.exif_keys:
                self.exif[k] = value
            else:
                self.attr[k] = value


    def readExif(self, gpsinfo=True, force=False):
        """
        Get the Exif tags of file.
        Optional GPSInfo tags will be read if 'gpsinfo' parameter is 'True'.

        :Parameters:
            -`gpsinfo`: if true, GPSInfo Exif data will be read.
        """
        lat = _GeoPhoto_DEFAULT_LAT
        lon = _GeoPhoto_DEFAULT_LON
        ele = _GeoPhoto_DEFAULT_ELE
        self.loadexif = False
        try:
            image = pyexiv2.metadata.ImageMetadata(self.path)
            image.read()
        except Exception as e:
            self.dgettext['error'] = str(e)
            msg = _("Cannot read image file '%(image_path)s': %(error)s.")
            raise GeoPhotoError(msg % self.dgettext)
        if gpsinfo:
            try:
                if 'Exif.GPSInfo.GPSLatitude' in image.exif_keys:
                    (g, m, s) = image['Exif.GPSInfo.GPSLatitude'].value
                    fr_g = fractions.Fraction("%s" % g)
                    gg = float(fr_g.numerator)/float(fr_g.denominator)
                    fr_m = fractions.Fraction("%s" % m)
                    mm = float(fr_m.numerator)/float(fr_m.denominator)
                    fr_s = fractions.Fraction("%s" % s)
                    ss = float(fr_s.numerator)/float(fr_s.denominator)
                    lat = geomath.DMStoN(gg, mm, ss)
                    if image['Exif.GPSInfo.GPSLatitudeRef'].value.upper() == 'S':
                        lat = -lat
                    (g, m, s) = image['Exif.GPSInfo.GPSLongitude'].value
                    fr_g = fractions.Fraction("%s" % g)
                    gg = float(fr_g.numerator)/float(fr_g.denominator)
                    fr_m = fractions.Fraction("%s" % m)
                    mm = float(fr_m.numerator)/float(fr_m.denominator)
                    fr_s = fractions.Fraction("%s" % s)
                    ss = float(fr_s.numerator)/float(fr_s.denominator)
                    lon = geomath.DMStoN(gg, mm, ss)
                    if image['Exif.GPSInfo.GPSLongitudeRef'].value.upper() == 'W':
                        lon = -lon
                if 'Exif.GPSInfo.GPSAltitude' in image.exif_keys:
                    Rn = image['Exif.GPSInfo.GPSAltitude'].value
                    fr_n = fractions.Fraction("%s" % Rn)
                    ele = float(fr_n.numerator)/float(fr_n.denominator)
                    try:
                        if int(image['Exif.GPSInfo.GPSAltitudeRef'].value) == 1:
                            ele = -ele
                    except:
                        pass
            except Exception as e:
                self.dgettext['error'] = str(e)
                msg = _("Cannot read GPS metadata of '%(image_path)s': %(error)s")
                if not force:
                    raise GeoPhotoError(msg % self.dgettext)
        self.lat = lat
        self.lon = lon
        self.ele = ele
        try:
            self.time = image['Exif.Image.DateTime'].value
        except:
            pass
        self.exif = image
        self.loadexif = True
        return True


    def writeExif(self, gpsinfo=True):
        """
        Write the Exif tags to file only if exif data were read previously.
        Optional GPSInfo tags will be written if 'gpsinfo' parameter is 'True'
        and exif was read before.
        Return value is 'True' if tags were written.

        :Parameters:
            -`gpsinfo`: if true, GPSInfo Exif data will be written.
        """
        if self.loadexif:
            try:
                self.attrToExif(gpsinfo)
                self.exif.write()
            except Exception as e:
                self.dgettext['error'] = str(e)
                msg = _("Cannot write metadata of '%(image_path)s': %(error)s.")
                raise GeoPhotoError(msg % self.dgettext)
            return True
        else:
            return False


    def attrToExif(self, gpsinfo=True):
        """
        It sets up the Exif tags to metadata image (but no saved).
        Optional GPSInfo tags will be set up if 'gpsinfo' parameter is 'True'
        and exif was read before.
        Return value is 'True' if the tags were set up.

        :Parameters:
            -`gpsinfo`: if true, GPSInfo Exif data will be set up.
        """
        if not self.loadexif:
            return False
        if gpsinfo:
            latRef = 'N'
            lonRef = 'E'
            eleRef = '0'
            lat = self.lat
            lon = self.lon
            ele = self.ele
            if lat < 0:
                lat = -lat
                latRef = 'S'
            if lon < 0:
                lon = -lon
                lonRef = 'W'
            if ele < 0:
                ele = -ele
                eleRef = '1'
            self.exif['Exif.GPSInfo.GPSAltitude'] = \
                [pyexiv2.utils.Rational(int(ele * 100.0), 100)]
            self.exif['Exif.GPSInfo.GPSAltitudeRef'] = eleRef
            (d, m, s) = geomath.NtoDMS(lat)
            fr_d = fractions.Fraction.from_float(float(d))
            Rd = pyexiv2.utils.Rational(int(fr_d.numerator),int(fr_d.denominator))
            fr_m = fractions.Fraction.from_float(float(m))
            Rm = pyexiv2.utils.Rational(int(fr_m.numerator),int(fr_m.denominator))
            fr_s = fractions.Fraction("%.2f" % s)
            Rs = pyexiv2.utils.Rational(int(fr_s.numerator),int(fr_s.denominator))
            self.exif['Exif.GPSInfo.GPSLatitude'] = [Rd, Rm, Rs]
            self.exif['Exif.GPSInfo.GPSLatitudeRef'] = latRef
            (d, m, s) = geomath.NtoDMS(lon)
            fr_d = fractions.Fraction.from_float(float(d))
            Rd = pyexiv2.utils.Rational(int(fr_d.numerator),int(fr_d.denominator))
            fr_m = fractions.Fraction.from_float(float(m))
            Rm = pyexiv2.utils.Rational(int(fr_m.numerator),int(fr_m.denominator))
            fr_s = fractions.Fraction("%.2f" % s)
            Rs = pyexiv2.utils.Rational(int(fr_s.numerator),int(fr_s.denominator))
            self.exif['Exif.GPSInfo.GPSLongitude'] = [Rd, Rm, Rs]
            self.exif['Exif.GPSInfo.GPSLongitudeRef'] = lonRef
            self.exif['Exif.GPSInfo.GPSDateStamp'] = self.time.isoformat()
            self.exif['Exif.GPSInfo.GPSMapDatum'] = 'WGS-84'
            self.exif['Exif.GPSInfo.GPSVersionID'] = '2 2 0 0'
            #self.exif['Exif.GPSInfo.GPSProcessingMethod'] = ' PhotoPlace'
        self.exif['Exif.Image.DateTime'] = self.time
        #for key, value in self.attr.iteritems():
        #    if key.startswith('Exif.'):
        #        if not key.startswith('Exif.GPSInfo.'):
        #            self.exif[key] = value
        return True


    def copy(self, dst, copyexif=True, zoom=1.0, size=(0,0), quality=Image.ANTIALIAS, maxsize=0):
        """
        It copies (or overwrites) the image file to `dst` and resizes it if it is necessary.
        The ANTIALIAS mode of PIL pacakge is used for copying and the image will be rotated
        according with Exif orientation. As an option `copyexif` indicates if exif data
        will be copied as well.

        :Parameters:
            -`dst`: Image file destination.
            -`copyexif`: if true, Exif data will be copied.
            -`maxsize`: max size of any side of new image.
            -`width` : new image width.
            -`height` : new image height.
        """
        try:
            im = Image.open(self.path)
            (im_width, im_height) = im.size
            # Size transformations
            (width, height) = size
            if zoom < 1:
                mirror = im.resize((int(im_width * zoom), int(im_height * zoom)), quality)
            elif width != 0 and height != 0:
                mirror = im.resize((width, height), quality)
            elif maxsize != 0:
                msize = im_height
                if im_width > im_height:
                    msize = im_width
                zoom = float(maxsize) / float(msize)
                mirror = im.resize((int(im_width * zoom), int(im_height * zoom)), quality)
            else:
                mirror = im.copy()
            # Orientation
            if 'Exif.Image.Orientation' in self.exif.exif_keys:
                orientation = self.exif['Exif.Image.Orientation'].value
                if orientation == 1:
                    # Nothing
                    pass
                elif orientation == 2:
                    # Vertical Mirror
                    mirror = mirror.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    # Rotation 180°
                    mirror = mirror.transpose(Image.ROTATE_180)
                elif orientation == 4:
                    # Horizontal Mirror
                    mirror = mirror.transpose(Image.FLIP_TOP_BOTTOM)
                elif orientation == 5:
                    # Horizontal Mirror + Rotation 270°
                    mirror = mirror.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_270)
                elif orientation == 6:
                    # Rotation 270°
                    mirror = mirror.transpose(Image.ROTATE_270)
                elif orientation == 7:
                    # Vertical Mirror + Rotation 270°
                    mirror = mirror.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
                elif orientation == 8:
                    # Rotation 90°
                    mirror = mirror.transpose(Image.ROTATE_90)
            if os.path.isfile(dst):
                os.unlink(dst)
            mirror.save(dst)
        except Exception as e:
            self.dgettext['error'] = str(e)
            self.dgettext['image_dst'] = dst
            msg = _("Cannot copy '%(image_path)s' to '%(image_dst)s': %(error)s.")
            raise GeoPhotoError(msg % self.dgettext)
        if copyexif :
            try:
                imexiv2 = pyexiv2.metadata.ImageMetadata(dst)
                imexiv2.read()
                #self.attrToExif()
                self.exif.copy(imexiv2, True, False, False)
                imexiv2.write()
            except Exception as e:
                self.dgettext['error'] = str(e)
                self.dgettext['image_dst'] = dst
                msg = _("Cannot copy image metadata from '%(image_path)s' "
                    "to '%(image_dst)s': %(error)s.")
                raise GeoPhotoError(msg % self.dgettext)


    def isGeoLocated(self):
        """
        It determines if a object is geolocated. Returns True is object have not
        default coordinate values.
        """
        if self.lat == _GeoPhoto_DEFAULT_LAT \
            and self.lon == _GeoPhoto_DEFAULT_LON \
            and self.ele == _GeoPhoto_DEFAULT_ELE:
            return False
        return True


    def __cmp__(self, photo):
        if photo == None:
            return False
        if os.path.realpath(self.path) == os.path.realpath(photo.path):
            return True
        return False


    def __repr__(self):
        return "(%s, %s),(%f, %f, %f, %f, %f, %s, %s)" % \
            (self.name, self.path,
                self.lat, self.lon, self.ele, self.azi, self.tilt, self.time, self.ptime)


    def __str__(self):
        s1 = "[(name= %s, path=%s, attr=%s)\
            (lat=%f, lon=%f, ele=%f, azi=%f, tilt=%f, time=%s, toffset=%d, ptime=%s)]\n" % \
            (self.name, self.path, self.attr,
            self.lat, self.lon, self.ele, self.azi, self.tilt, self.time, self.toffset, self.ptime)
        s2 = "EXIF => %s" % self.exif
        return s1 + s2


# EOF
