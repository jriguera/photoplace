#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
Exceptions for SXMLTemplate package.
"""
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.4.0"
__date__ = "December 2010"
__license__ = "GPL (v3 or later)"
__copyright__ ="(c) Jose Riguera"


import os.path
import gettext
import locale

__GETTEXT_DOMAIN__ = "sxmltemplate"
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)


# ###################################
# Exceptions for SXMLTemplate package
# ###################################

class SXMLTemplateError(Exception):
    """
    Base class for exceptions of SXMLTemplate package.
    """
    def __init__(self, msg='SXMLTemplateError!'):
        self.value = msg
    def __str__(self):
        return repr(self.value)


class SXMLTemplateErrorLoad(SXMLTemplateError):
    """
    Exceptions trying to load file, URL, ...
    """
    def __init__(self, file, errno, strerror):
        d = {'file': file, 'errno': errno, 'strerror': strerror }
        self.value = _("Cannot open XML template file '%(file)s' for reading: I/O error (%(errno)s): %(strerror)s.") % d


class SXMLTemplateErrorParse(SXMLTemplateError):
    """
    Exceptions related to XML syntax, correction, well formed ... XML structure.
    """
    def __init__(self, msg):
        self.value = _("Cannot parse XML: %s.") % (msg)


class SXMLTemplateErrorRedo(SXMLTemplateError):
    """
    Exceptions setting a XML node for repeat it ...
    """
    def __init__(self, msg):
        self.value = _("Cannot set element '%s' in template.") % (msg)

# EOF
