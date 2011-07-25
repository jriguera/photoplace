#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       stateHandler.py
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
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import os.path
import logging
import tempfile
import shutil
import urlparse
import datetime
import math
import threading
import locale

from userFacade import Error
from definitions import *



def local_utc():
    """
    Try to calcultate delta minutes between local and utc time for current moment.
    """
    same_min = False
    dt_dif = None
    while not same_min:
        dt_utc = datetime.datetime.utcnow()
        dt_now = datetime.datetime.now()
        same_min = dt_utc.minute == dt_now.minute
        if same_min:
            dt_new = datetime.datetime(dt_now.year, dt_now.month, dt_now.day, \
                dt_now.hour, dt_now.minute, dt_utc.second, dt_utc.microsecond)
            dt_dif = dt_new - dt_utc
    return dt_dif


def timedelta_to_minutes(timedelta):
    td = timedelta
    if timedelta.days < 0:
        td = -td
    minutes = td.seconds / 60 + 86400 * td.days
    if timedelta.days < 0:
        return -minutes
    return minutes


def float_to_timefloat(value):
    intval = int(value)
    floval = value - intval
    new_floval = math.fmod(floval * 100, 60.0) / 100
    new_intval = intval + int(floval * 100 / 60.0)
    new_value = new_intval + new_floval
    return new_value


def timefloat_to_minutes(value):
    intval = int(value)
    floval = (value - intval) * 100
    new_value = intval * 60 + int(floval)
    return new_value


def minutes_to_timefloat(value):
    minutes = math.fmod(value, 60.0)/100.0
    hours = int(value/60)
    return minutes + hours



class DSynchronized(object):
    """
    Class enapsulating a lock and a function allowing it to be used as a synchronizing
    decorator making the wrapped function thread-safe
    """
    _debug = False

    def __init__(self, *args):
        object.__init__(self)
        self.lock = threading.Lock()

    def __call__(self, f):
        def lockedfunc(*args, **kwargs):
            try:
                self.lock.acquire()
                if self._debug:
                    sys.stderr.write('DSynchronized(%s): Acquired lock => %s\n' %
                        (f.__name__, threading.currentThread()))
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    raise
            finally:
                self.lock.release()
                if self._debug:
                    sys.stderr.write('DSynchronized(%s): Released lock => %s\n' %
                        (f.__name__, threading.currentThread()))
        return lockedfunc



# #############
# Program state
# #############

class State(object):

    def __init__(self, resourcedir, options={}, resourcedir_user=None):
        object.__init__(self)
        self.__logger = logging.getLogger(self.__class__.__name__)
        #
        self.resourcedir = resourcedir
        self.resourcedir_user = resourcedir_user
        self._utczoneminutes = 0
        self._templateseparatorkey = PhotoPlace_Cfg_main_templateseparatorkey
        self._templatedefaultvalue = PhotoPlace_Cfg_main_templatedefaultvalue
        self._templateseparatornodes = PhotoPlace_Cfg_main_templateseparatornodes
        self._templatedeltag = PhotoPlace_Cfg_main_templatedeltag
        self._kmltemplate = os.path.join(resourcedir, PhotoPlace_Cfg_main_kmltemplate)
        self._quality = PhotoPlace_Cfg_main_quality
        self._jpgzoom = PhotoPlace_Cfg_main_jpgzoom
        self._jpgsize = PhotoPlace_Cfg_main_jpgsize
        self._maxdeltaseconds = PhotoPlace_Cfg_main_maxdeltaseconds
        self._timeoffsetseconds = PhotoPlace_Cfg_main_timeoffsetseconds
        self._exifmode = PhotoPlace_Cfg_main_exifmode
        self._copyonlygeolocated = PhotoPlace_Cfg_main_copyonlygeolocated
        self._version = PhotoPlace_Cfg_version
        self._photoinputdir = u''
        self._gpxinputfile = u''
        self._outputfile = u''
        self._photouri = u''
        #
        self.status = 1
        #
        self.slock = threading.Lock()
        self.lock_geophotos = threading.Lock()
        self.lock_gpxdata = threading.Lock()
        self.lock_kmldata = threading.Lock()
        #
        self.quality = {}
        self.tmpdir = None
        self.outputdir = None
        self.outputkmz = None
        self.outputkml = None
        self.options = options
        self.geophotos = []
        self.gpxdata = None
        self.kmldata = None
        #
        self.initial()


    def __getitem__(self, key):
        k = str(key)
        keys = [
            "version",
            "kmltemplate",
            "exifmode",
            "utczoneminutes",
            "maxdeltaseconds",
            "timeoffsetseconds",
            "gpxinputfile",
            "photoinputdir",
            "photouri",
            "outputfile",
            "jpgsize",
            "quality",
            "jpgzoom",
            "copyonlygeolocated",
        ]
        if k in keys:
            return getattr(self, '_' + k)
        else:
            if k == 'logfile' or k == 'loglevel':
                return self.options[k]
            else:
                raise AttributeError(k)


    def __setitem__(self, key, value):
        k = str(key)
        if k == "version":
            pass
        elif k == "kmltemplate":
            self.set_kmltemplate(value)
        elif k == "exifmode":
            self.set_exifmode(value)
        elif k == "utczoneminutes":
            self.set_utczoneminutes(value)
        elif k == "maxdeltaseconds":
            self.set_maxdeltaseconds(value)
        elif k == "timeoffsetseconds":
            self.set_timeoffsetseconds(value)
        elif k == "gpxinputfile":
            self.set_gpxinputfile(value)
        elif k == "photoinputdir":
            self.set_photoinputdir(value)
        elif k == "photouri":
            self._set_photouri(value)
        elif k == "outputfile":
            self.set_outputfile(value)
        elif k == "jpgsize":
            self.set_jpgsize(value)
        elif k == "quality":
            self.set_quality(value)
        elif k == "jpgzoom":
            self.set_jpgzoom(value)
        elif k == "copyonlygeolocated":
            self.set_copyonlygeolocated(value)
        elif k == 'logfile' or k == 'loglevel':
            self.options[k] = value
        else:
            raise AttributeError(k)


    @DSynchronized()
    def clear(self):
        self.__logger.info(_("Reseting state data ... "))
        self.slock.acquire()
        self.lock_geophotos.acquire()
        self.lock_gpxdata.acquire()
        self.lock_kmldata.acquire()
        self._photoinputdir = u''
        self._gpxinputfile = u''
        self._outputfile = u''
        self._photouri = u''
        self.geophotos = []
        self.gpxdata = None
        self.kmldata = None
        self.tmpdir = None
        self.outputdir = None
        self.outputkmz = None
        self.outputkml = None
        self.lock_geophotos.release()
        self.lock_gpxdata.release()
        self.lock_kmldata.release()
        self.slock.release()


    def initial(self):
        self._photoinputdir = u''
        self._gpxinputfile = u''
        self._outputfile = u''
        self._photouri = u''
        self.geophotos = []
        self.gpxdata = None
        self.kmldata = None
        self.tmpdir = None
        self.outputdir = None
        self.outputkmz = None
        self.outputkml = None
        self.set_jpgsize()
        self.set_quality()
        self.set_jpgzoom()
        self.set_exifmode()
        self.set_maxdeltaseconds()
        self.set_timeoffsetseconds()
        self.set_utczoneminutes()
        self._set_kmltemplate()
        try:
            self.set_gpxinputfile(None, False)
        except:
            pass
        try:
            self.set_photoinputdir(None, False)
        except:
            pass
        try:
            self.set_outputfile(None, False)
        except:
            pass


    @DSynchronized()
    def set_quality(self, value=None):
        quality = PhotoPlace_Cfg_main_quality
        try:
            if value != None:
                quality = int(value)
            else:
                quality = int(self.options["quality"])
            if quality >= len(PhotoPlace_Cfg_quality) \
                or quality < 0:
                raise ValueError("0 <= quality < %" % len(PhotoPlace_Cfg_quality))
        except KeyError:
            quality = PhotoPlace_Cfg_main_quality
            self.__logger.warning(_("Value of 'quality' not defined "
            "in the configuration file. Setting default value '%s'.") % quality)
        except ValueError as valueerror:
            msg = _("Value of 'quality' incorrect: %s. ") % str(valueerror)
            self.__logger.error(msg)
            tip = _("Set a correct value of 'quality'.")
            raise Error(msg, tip, "ValueError")
        self._quality = quality
        self.quality = PhotoPlace_Cfg_quality[quality]


    @DSynchronized()
    def set_jpgzoom(self, value=None):
        try:
            if value != None:
                jpgzoom = float(value)
            else:
                jpgzoom = float(self.options["jpgzoom"])
        except KeyError:
            jpgzoom = PhotoPlace_Cfg_main_jpgzoom
            self.__logger.warning(_("Value of 'jpgzoom' not defined "
            "in the configuration file. Setting default value '%s'.") % jpgzoom)
        except ValueError as valueerror:
            msg = _("Value of 'JPGZoom' incorrect: %s. ") % str(valueerror)
            self.__logger.error(msg)
            tip = _("Set a correct value of 'JPGZoom'.")
            raise Error(msg, tip, "ValueError")
        self._jpgzoom = jpgzoom


    @DSynchronized()
    def set_jpgsize(self, size=None):
        try:
            if size != None:
                (width, height) = size
                w = int(width)
                h = int(height)
            else:
                (w, h) = tuple(
                    int(s) for s in self.options["jpgsize"][1:-1].split(','))
        except KeyError:
            (w, h) = PhotoPlace_Cfg_main_jpgsize
            self.__logger.warning(_("Value of 'jpgwidth' and/or 'jpgheight' not defined "
            "in the configuration file. Setting default value '%s'.") % str((w,h)))
        except (TypeError, ValueError) as error:
            msg = _("Value of 'JPGWidth' and/or 'JPGHeight' incorrect: %s. ") % str(error)
            self.__logger.error(msg)
            tip = _("Set a correct value of 'JPGWidth' and/or 'JPGHeight'.")
            raise Error(msg, tip, error.__class__.__name__)
        self._jpgsize = (w, h)


    @DSynchronized()
    def set_outputfile(self, value=None, log=True):
        dgettext = {}
        if value != None:
            outputfile = os.path.expandvars(value)
        else:
            if not self.options.has_key('outputfile'):
                if self._photoinputdir:
                    outputfile = self._photoinputdir + u".kmz"
                else:
                    try:
                        outputfile = self.options['photoinputdir'] + u".kmz"
                        outputfile = os.path.expandvars(outputfile)
                    except:
                        msg = _("Output file not selected!")
                        if log:
                            self.__logger.error(msg)
                        tip = _("Choose an output file to continue!")
                        raise Error(msg, tip, e.__class__.__name__)
            else:
                outputfile = os.path.expandvars(self.options['outputfile'])
        self._outputfile = os.path.normpath(outputfile)
        if not isinstance(self._outputfile, unicode):
            try:
                self._outputfile = unicode(self._outputfile, PLATFORMENCODING)
            except:
                pass
        self.tmpdir = None
        self.outputkmz = None
        self.outputkml = None
        self.outputdir = os.path.dirname(self._outputfile)
        outputfile = os.path.basename(self._outputfile)
        (outputfilebase, outpufileext) = os.path.splitext(outputfile)
        dgettext['output_dir'] = self.outputdir.encode(PLATFORMENCODING)
        if outpufileext == '.kmz':
            try:
                deletedir = tempfile.mkdtemp(u"_tmp", PhotoPlace_name + u"-", self.outputdir)
                shutil.rmtree(deletedir)
            except Exception as e:
                self._outputfile = None
                self.outputdir = None
                dgettext['error'] = str(e)
                msg = _("Cannot create temporary directory in '%(output_dir)s': %(error)s.")
                msg = msg % dgettext
                self.__logger.error(msg)
                tip = _("Check output directory write permissions")
                raise Error(msg, tip, e.__class__.__name__)
            self.outputdir = deletedir
            self.tmpdir = deletedir
            self.outputkmz = self._outputfile
            self.outputkml = os.path.join(deletedir, outputfilebase + u".kml")
        elif outpufileext == '.kml':
            try:
                # Write test
                testfile = tempfile.NamedTemporaryFile(dir=self.outputdir, delete=True)
            except Exception as e:
                self._outputfile = None
                self.outputdir = None
                dgettext['error'] = str(e)
                msg = _("Cannot create files in '%(output_dir)s': %(error)s.") % dgettext
                self.__logger.error(msg)
                tip = _("Check output directory write permissions")
                raise Error(msg, tip, e.__class__.__name__)
            finally:
                try:
                    testfile.close()
                except:
                    pass
            self.outputkml = self._outputfile
        else:
            self._outputfile = None
            self.outputdir = None
            msg = _("Unknown extension of output file '%s'.") % self._outputfile
            tip = _("The extension of output file determines the program mode")
            self.__logger.error(msg)
            raise Error(msg, tip, "NameError")
        self._set_photouri()


    @DSynchronized()
    def _set_photouri(self, value=None):
        if value != None:
            photouri = value
        else:
            if not self.options.has_key('photouri'):
                if self._photoinputdir != None:
                    photouri = os.path.split(self._photoinputdir)[1]
                    if not photouri:
                        photouri = os.path.split(os.path.split(self._photoinputdir)[0])[1]
                    photouri = photouri + u'/'
                else:
                    try:
                        photouri = os.path.split(self.options['photoinputdir'])[1]
                        if not photouri:
                            photouri = os.path.split(self.options['photoinputdir'])[0]
                            photouri = os.path.split(photouri)[1]
                        photouri = photouri + u'/'
                    except:
                        photouri = PhotoPlace_Cfg_main_photouri
            else:
                photouri = self.options['photouri']
        self._photouri = photouri
        if not isinstance(self._photouri, unicode):
            try:
                self._photouri = unicode(self._photouri, PLATFORMENCODING)
            except:
                pass
        if self._outputfile != None:
            outputfile = os.path.basename(self._outputfile)
            if self.tmpdir:
                outputdir = self.tmpdir
            else:
                outputdir = os.path.dirname(self._outputfile)
            (outputfilebase, outpufileext) = os.path.splitext(outputfile)
            photouri = urlparse.urlsplit(self._photouri)
            scheme = photouri.scheme
            if os.path.splitdrive(self._photouri)[0]:
                 scheme = ''
            if scheme != '' and scheme != 'file':
                # URL
                self.outputdir = os.path.join(outputdir, outputfilebase)
            else:
                self.outputdir = os.path.join(outputdir, os.path.normcase(photouri.path))


    @DSynchronized()
    def set_photoinputdir(self, value=None, log=True):
        if value != None:
            photoinputdir = os.path.normpath(os.path.expandvars(value))
        else:
            if self.options.has_key('photoinputdir'):
                photoinputdir = os.path.expandvars(self.options['photoinputdir'])
            else:
                msg = _("Directory with input photos not defined ... Nothing to do!")
                if log:
                    self.__logger.error(msg)
                tip = _("Select a input photos directory to continue!")
                raise Error(msg, tip)
        if not isinstance(photoinputdir, unicode):
            try:
                photoinputdir = unicode(photoinputdir, PLATFORMENCODING)
            except:
                pass
        if not os.path.isdir(photoinputdir):
            msg = _("Photo input directory '%s' not found!.") % \
                photoinputdir.encode(PLATFORMENCODING)
            self.__logger.error(msg)
            tip = _("Check if the selected directory exist.")
            raise Error(msg, tip)
        self._photoinputdir = photoinputdir
        self._set_photouri()


    @DSynchronized()
    def set_gpxinputfile(self, value=None, log=True):
        if value != None:
            gpxinputfile = os.path.normpath(os.path.expandvars(value))
        else:
            if self.options.has_key('gpxinputfile'):
                gpxinputfile = os.path.expandvars(self.options['gpxinputfile'])
            else:
                msg = _("GPX file not defined ... Nothing to do!")
                if log:
                    self.__logger.error(msg)
                tip = _("Select a GPX input file to continue!")
                raise Error(msg, tip)
        if not isinstance(gpxinputfile, unicode):
            try:
                gpxinputfile = unicode(gpxinputfile, PLATFORMENCODING)
            except:
                pass
        if not os.path.isfile(gpxinputfile):
            msg = _("GPX input file '%s' not found!.") % \
                gpxinputfile.encode(PLATFORMENCODING)
            self.__logger.error(msg)
            tip = _("Check the selected GPX input file to continue.")
            raise Error(msg, tip)
        self._gpxinputfile = gpxinputfile


    @DSynchronized()
    def set_utczoneminutes(self, value=None):
        utczoneminutes = timedelta_to_minutes(local_utc())
        try:
            if value != None:
                utczoneminutes = int(value)
            else:
                utczoneminutes = int(self.options["utczoneminutes"])
        except KeyError:
            self.__logger.warning(_("Value of 'utczoneminutes' not defined in the "
            "configuration file. Estimated local value is '%s'.") % utczoneminutes)
        except ValueError as valueerror:
            dgettext = {'error': str(valueerror), 'value': utczoneminutes }
            msg = _("Value of 'utczoneminutes' incorrect: %(error)s. "
                "Setting default value '%(value)s'.") % dgettext
            self.__logger.error(msg)
            tip = _("Set the value of UTC Time Zone to continue. The value may "
                "be positive or negative.")
            raise Error(msg, tip, "ValueError")
        self._utczoneminutes = utczoneminutes


    @DSynchronized()
    def set_maxdeltaseconds(self, value=None):
        maxdeltaseconds = PhotoPlace_Cfg_main_maxdeltaseconds
        try:
            if value != None:
                maxdeltaseconds = int(value)
            else:
                maxdeltaseconds = int(self.options["maxdeltaseconds"])
        except KeyError:
            self.__logger.warning(_("Value of 'maxdeltaseconds' not defined in the "
            "configuration file. Setting default value '%s'.") % maxdeltaseconds)
        except ValueError as valueerror:
            dgettext = {'error': str(valueerror), 'value': maxdeltaseconds }
            self.__logger.warning(_("Value of 'maxdeltaseconds' incorrect: %(error)s. "
                "Setting default value '%(value)s'.") % dgettext)
        self._maxdeltaseconds = maxdeltaseconds


    @DSynchronized()
    def set_timeoffsetseconds(self, value=None):
        timeoffsetseconds = PhotoPlace_Cfg_main_timeoffsetseconds
        try:
            if value != None:
                timeoffsetseconds = int(value)
            else:
                timeoffsetseconds = int(self.options["timeoffsetseconds"])
        except KeyError:
            self.__logger.warning(_("Value of 'timeoffsetseconds' not defined in the "
            "configuration file. Setting default value '%s'.") % timeoffsetseconds)
        except ValueError as valueerror:
            dgettext = {'error': str(valueerror), 'value': timeoffsetseconds }
            self.__logger.warning(_("Value of 'timeoffsetseconds' incorrect: %(error)s. "
                "Setting default value '%(value)s'.") % dgettext)
        self._timeoffsetseconds = timeoffsetseconds


    @DSynchronized()
    def set_exifmode(self, value=None):
        exifmode = PhotoPlace_Cfg_main_exifmode
        try:
            if value != None:
                exifmode = int(value)
            else:
                exifmode = int(self.options["exifmode"])
        except KeyError:
            self.__logger.warning(_("Value of 'exifmode' not defined in the "
            "configuration file. Setting default value '%s'.") % exifmode)
        except ValueError as valueerror:
            dgettext = {'error': str(valueerror), 'value': exifmode }
            self.__logger.warning(_("Value of 'exifmode' incorrect: %(error)s. "
            "Setting default value '%(value)s'.") % dgettext)
        self._exifmode = exifmode


    @DSynchronized()
    def _set_kmltemplate(self):
        if self.options.has_key('kmltemplate'):
            templatedir = self.options['kmltemplate']
            if not isinstance(templatedir, unicode):
                try:
                    templatedir = unicode(templatedir, PLATFORMENCODING)
                except:
                    pass
        else:
            msg = _("Main KML template not defined. Setting default KML template file '%s'.")
            self.__logger.warning(msg % PhotoPlace_Cfg_main_kmltemplate)
            templatedir = os.path.join(self.resourcedir, PhotoPlace_Cfg_main_kmltemplate)
        self.set_kmltemplate(templatedir)
        msg = _("Value of '%(key)s' incorrect. Setting to default value '%(value)s'.")
        templateseparatorkey = PhotoPlace_Cfg_main_templateseparatorkey
        try:
            templateseparatorkey = self.options['templateseparatorkey']
        except:
            dgettext = {'key': 'templateseparatorkey', 'value': templateseparatorkey }
            self.__logger.warning(msg % dgettext)
        self._templateseparatorkey = templateseparatorkey
        templatedefaultvalue = self._templatedefaultvalue
        try:
            templatedefaultvalue = self.options['templatedefaultvalue']
        except:
            dgettext = {'key': 'templatedefaultvalue', 'value': templatedefaultvalue }
            self.__logger.warning(msg % dgettext)
        self._templatedefaultvalue = templatedefaultvalue
        templateseparatornodes = self._templateseparatornodes
        try:
            templateseparatornodes = self.options['templateseparatornodes']
        except:
            dgettext = {'key': 'templateseparatornodes', 'value': templateseparatornodes }
            self.__logger.warning(msg % dgettext)
        self._templateseparatornodes = templateseparatornodes
        templatedeltag = self._templatedeltag
        try:
            templatedeltag = self.options['templatedeltag']
        except:
            dgettext = {'key': 'templatedeltag', 'value': templatedeltag }
            self.__logger.warning(msg % dgettext)
        self._templatedeltag = templatedeltag


    @DSynchronized()
    def set_kmltemplate(self, value):
        kmltemplate = os.path.normpath(os.path.expandvars(value))
        if not isinstance(kmltemplate, unicode):
            try:
                kmltemplate = unicode(kmltemplate, PLATFORMENCODING)
            except:
                pass
        if not os.path.isfile(kmltemplate):
            kmltemplate_orig = kmltemplate
            kmltemplate = os.path.join(self.resourcedir_user, kmltemplate)
            templates_key = u'templates'
            if not os.path.isfile(kmltemplate):
                language = locale.getdefaultlocale()[0]
                kmltemplate = os.path.join(self.resourcedir, templates_key, language, kmltemplate_orig)
                if not os.path.isfile(kmltemplate):
                    language = language.split('_')[0]
                    kmltemplate = os.path.join(self.resourcedir, templates_key, language, kmltemplate_orig)
                    if not os.path.isfile(kmltemplate):
                        kmltemplate = os.path.join(self.resourcedir, templates_key, kmltemplate_orig)
                if not os.path.isfile(kmltemplate):
                    msg = _("Main KML template file '%s' not found!.")
                    self.__logger.error(msg % kmltemplate.encode(PLATFORMENCODING))
                    tip = _("Check if it is defined properly in the configuration file.")
                    raise Error(msg, tip)
        self._kmltemplate = kmltemplate


    @DSynchronized()
    def set_copyonlygeolocated(self, value=None):
        copyonlygeolocated = PhotoPlace_Cfg_main_copyonlygeolocated
        try:
            if value != None:
                copyonlygeolocated = value
            else:
                copyonlygeolocated = bool(int(self.options["copyonlygeolocated"]))
        except KeyError:
            self.__logger.warning(_("Value of 'copyonlygeolocated' not defined in the "
            "configuration file. Setting default value '%s'.") % copyonlygeolocated)
        except ValueError as valueerror:
            dgettext = {'error': str(valueerror), 'value': copyonlygeolocated }
            self.__logger.warning(_("Value of 'copyonlygeolocated' incorrect: %(error)s. "
            "Setting default value '%(value)s'.") % dgettext)
        self._copyonlygeolocated = copyonlygeolocated


# EOF
