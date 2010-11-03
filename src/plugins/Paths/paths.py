#! /usr/bin/env python


import os.path
import sys
import time
import codecs
import urlparse
import gettext
import locale


# I18N gettext support
__GETTEXT_DOMAIN__ = "photoplace-paths"
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



import DataTypes.kmlData
from Plugins.Interface import *
from definitions import *


# Simbols exported to template
PhotoPlace_PathNAME = "PhotoPlace.PathNAME"
PhotoPlace_PathDESC = "PhotoPlace.PathDESC"
PhotoPlace_PathTINI = "PhotoPlace.PathTINI"
PhotoPlace_PathTEND = "PhotoPlace.PathTEND"
PhotoPlace_PathDRTN = "PhotoPlace.PathDRTN"
PhotoPlace_PathLEN = "PhotoPlace.PathLEN"
PhotoPlace_PathLENMIN = "PhotoPlace.PathLENMIN"
PhotoPlace_PathLENMAX = "PhotoPlace.PathLENMAX"
PhotoPlace_PathSPMIN = "PhotoPlace.PathSPMIN"
PhotoPlace_PathSPMAX = "PhotoPlace.PathSPMAX"
PhotoPlace_PathSPAVG = "PhotoPlace.PathSPAVG"
PhotoPlace_PathNSEG = "PhotoPlace.PathNSEG"
PhotoPlace_PathWPTCOORDS = "PhotoPlace.PathWPTCOORDS"
PhotoPlace_PathNWPT = "PhotoPlace.PathNWPT"

# Configuration keys
_KmlPaths_CONFKEY = "kmlpaths"
_KmlPaths_CONFKEY_KMLPATH_NAME = "pathsfolder"
_KmlPaths_CONFKEY_KMLPATH = "kmlpath"
_KmlPaths_CONFKEY_TEMPLATE = "templatefile"

# Default values
_KmlPaths_KMLPATH_NAME = _("Paths")
_KmlPaths_TEMPLATEDIR = "templates"
_KmlPaths_KMLPATH = ['kml.Document.Placemark']
_KmlPaths_TEMPLATE = os.path.join("templates", "paths.template.kml")
_KmlPaths_KMLDIR_APPEND = ".paths"
_KmlPaths_TEMPLATE_REF = {
    'kml.Document.Placemark.description':
        os.path.join(_KmlPaths_TEMPLATEDIR, "PathDescription.xhtml"),
}



class KmlPaths(Plugin):

    description = _("A plugin to generate paths from GPX tracks in "
        "order to show them in KML layer.")
    version = "0.1.0"
    author = "Jose Riguera Lopez"
    email = "<jriguera@gmail.com>"
    url = "http://code.google.com/p/photoplace/"
    copyright = "(c) Jose Riguera"
    date = "Sep 2010"
    license = "GPLv3"
    capabilities = {
        'GUI' : PLUGIN_GUI_NO,
        'NeedGUI' : False,
    }
    
    def init(self, options, widget=None):
        self.options = options
        if not self.options.has_key(_KmlPaths_CONFKEY):
            self.options[_KmlPaths_CONFKEY] = dict()
        self.name = self.options[_KmlPaths_CONFKEY].setdefault(
            _KmlPaths_CONFKEY_KMLPATH_NAME, _KmlPaths_KMLPATH_NAME)
        self.template = self.options[_KmlPaths_CONFKEY].setdefault(
            _KmlPaths_CONFKEY_TEMPLATE, _KmlPaths_TEMPLATE)
        self.template = os.path.expandvars(os.path.expanduser(self.template))
        if not os.path.isfile(self.template):
            self.template = os.path.join(self.state.resourcedir, self.template)
            if not os.path.isfile(self.template):
                msg = _("Main template file '%s' does not exist!.") % self.template
                self.logger.error(msg)
                raise ValueError(msg)
        items = [
            _KmlPaths_CONFKEY_KMLPATH_NAME,
            _KmlPaths_CONFKEY_TEMPLATE,
        ]
        self.templates = dict()
        for k,v in _KmlPaths_TEMPLATE_REF.iteritems():
            if not k in self.options[_KmlPaths_CONFKEY]:
                self.options[_KmlPaths_CONFKEY][k] = v
        for k,v in self.options[_KmlPaths_CONFKEY].iteritems():
            if k not in items:
                file_exist = True
                filename = os.path.expandvars(os.path.expanduser(v))
                if not os.path.isfile(filename):
                    filename = os.path.join(self.state.resourcedir, filename)
                    if not os.path.isfile(filename):
                        msg = _("Template file '%s' does not exist!.") % filename
                        self.logger.warning(msg)
                        file_exist = False
                if file_exist:
                    self.templates[k] = filename
        self.xmlnodes_sep = self.state._templateseparatornodes
        self.delete_tag = self.state._templatedeltag
        self.separator_key  = self.state._templateseparatorkey
        self.default_value = self.state._templatedefaultvalue
        xmlinfo = " XML generated with %s on %s" % (PhotoPlace_name, time.asctime())
        try:
            self.kmldata = DataTypes.kmlData.KmlData(
                self.template, _KmlPaths_KMLPATH, xmlinfo,
                self.xmlnodes_sep,
                self.default_value,
                self.separator_key,
                self.delete_tag)
        except DataTypes.kmlData.KmlDataError as kmldataerror:
            msg = str(kmldataerror)
            self.logger.error(msg)
            raise
        try:
            self.kmldata.setTemplates(self.templates)
        except DataTypes.kmlData.KmlDataError as kmldataerror:
            msg = str(kmldataerror)
            self.logger.error(msg)
            raise
        self.ready = 1


    @DRegister("MakeKML:finish")
    def generate(self, *args, **kwargs):
        if not self.ready or not self.state.gpxdata or not self.state.outputkml:
            return
        self.outputfile = None
        self.outputdir = None
        self.outputuri = None
        try:
            self.rootdata = self.options['defaults']
        except:
            self.rootdata = dict()
        try:
            self.outputfile = os.path.basename(self.state.outputkml)
            if self.state.tmpdir:
                # it is a KMZ, only one kml is allowed ...
                # so we change the extension
                self.outputfile += ".xml"
            outputdir = os.path.split(self.state.outputdir)
            self.outputdir = os.path.join(outputdir[0], outputdir[1])
            self.outputdir += _KmlPaths_KMLDIR_APPEND
            state_photouri = self.state['photouri']
            photouri = urlparse.urlsplit(state_photouri)
            scheme = photouri.scheme 
            if os.path.splitdrive(state_photouri)[0]:
                 scheme = ''
            if scheme:
                # URL
                if '%(' in state_photouri:
                    data = {'PhotoPlace.PhotoNAME': self.outputfile}
                    self.outputuri = state_photouri % data
                elif '%s' in state_photouri:
                    self.outputuri = state_photouri % self.outputfile
                else:
                    self.outputuri = state_photouri + self.outputfile
            else:
                self.outputuri = os.path.basename(self.outputdir) + '/' + self.outputfile
            if not os.path.isdir(self.outputdir):
                os.mkdir(self.outputdir)
            self.outputfile = os.path.join(self.outputdir, self.outputfile)
        except Exception as exception:
            self.logger.error(_("Cannot set outputfile: %s.") % str(exception))
            return
        self.logger.debug(_("Processing all tracks (paths) from GPX data ... "))
        num_tracks = 0
        dgettext = dict()
        for track in self.state.gpxdata.tracks:
            pathdata = track.attr
            pathdata[PhotoPlace_PathNAME] = track.name
            pathdata[PhotoPlace_PathDESC] = track.desc
            dgettext['path'] = track.name
            dgettext['path_desc'] = track.desc
            try:
                (tmin, tmax, duration) = track.timeMinMaxDuration()
                pathdata[PhotoPlace_PathTINI] = "%s" % tmin
                pathdata[PhotoPlace_PathTEND] = "%s" % tmax
                pathdata[PhotoPlace_PathDRTN] = "%s" % duration
                (lmin, lmax, length) = track.lengthMinMaxTotal()
                pathdata[PhotoPlace_PathLEN] = "%.3f" % length
                pathdata[PhotoPlace_PathLENMIN] = "%.3f" % lmin
                pathdata[PhotoPlace_PathLENMAX] = "%.3f" % lmax
                (smin, savg, smax) = track.speedMinAvgMax()
                pathdata[PhotoPlace_PathSPMIN] = "%.3f" % smin
                pathdata[PhotoPlace_PathSPMAX] = "%.3f" % smax
                pathdata[PhotoPlace_PathSPAVG] = "%.3f" % savg
                pathdata[PhotoPlace_PathNSEG] = "%s" % len(track.ltrkseg)
                pathdata[PhotoPlace_PathWPTCOORDS] = ''
                num_points = 0
                for point in track.listpoints():
                    pathdata[PhotoPlace_PathWPTCOORDS] += " %.8f, %.8f, %.8f " % \
                        (point.lon, point.lat, point.ele)
                    num_points = num_points + 1
                pathdata[PhotoPlace_PathNWPT] = num_points
                # Set data
                self.kmldata.setData(pathdata)
                # write all data to log
                dgettext['path_npoints'] = num_points
                dgettext['path_nsegments'] = len(track.ltrkseg)
                dgettext['path_len'] = length
                dgettext['path_avgsp'] = savg
                dgettext['path_time'] = duration
                self.logger.debug(_("Path '%(path)s', ('%(path_desc)s'): "
                    "points=%(path_npoints)d, segments=%(path_nsegments)d, "
                    "length=%(path_len)s, avgspeed=%(path_avgsp).3f, "
                    "time='%(path_time)s'") % dgettext)
                num_tracks += 1
            except Exception as e:
                dgettext["error"] = str(e)
                msg = _("Error when track (path) '%(path)s' was being "
                    "processed: %(error)s.") % dgettext
                self.logger.error(msg)
        dgettext['num_tracks'] = num_tracks
        msg = _("%(num_tracks)s have been generated for KML data.") % dgettext
        self.kmldata.close(self.rootdata)
        # set up a reference to file in main kml dom
        doc = self.state.kmldata.getKml()
        networkLink = doc.createElement("NetworkLink")
        name = doc.createElement("name")
        nameid = doc.createTextNode(str(self.name))
        name.appendChild(nameid)
        networkLink.appendChild(name)
        link = doc.createElement("Link")
        networkLink.appendChild(link)
        href = doc.createElement("href")
        uri = doc.createTextNode(str(self.outputuri))
        href.appendChild(uri)
        link.appendChild(href)
        document = doc.getElementsByTagName("Document")[0]
        document.appendChild(networkLink)


    @DRegister("SaveFiles:startgo")
    def save(self, *args, **kwargs):
        if not self.ready:
            return
        dgettext = dict()
        dgettext['outputfile'] = self.outputfile
        try:
            #return open(source, 'wb')
            fd = codecs.open(self.outputfile, "wb", encoding="utf-8")
        except Exception as exception:
            dgettext['error'] = str(exception)
            msg = _("Cannot open '%(outputfile)s' for writing: %(error)s.")
            self.logger.error(msg % dgettext)
            raise
        else:
            msg = _("Generating output file in '%(outputfile)s' ...")
            self.logger.debug(msg % dgettext)
            try:
                kmldom = self.kmldata.getKml()
                kmldom.writexml(fd, "", "   ","\n", "utf-8")
            except Exception as exception:
                dgettext['error'] = str(exception)
                msg = _("Cannot write to file '%(outputfile)s': %(error)s.")
                self.logger.error(msg % dgettext)
            finally:
                fd.close()


    def end(self, options):
        self.ready = 0
        self.options = None
        self.name = None
        self.template = None
        self.templates = None
        self.xmlnodes_sep = None
        self.delete_tag = None
        self.separator_key = None
        self.default_value = None
        self.template = None
        self.kmldata = None
        self.rootdata = None


# EOF

