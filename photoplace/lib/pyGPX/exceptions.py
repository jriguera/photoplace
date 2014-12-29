#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
Exceptions for GPX package.
"""
__package_name__ = "gpx"
__package_revision__ = '0'
__package_version__ = '0.1.1'
__package_released__ = "Dec 2014"
__package_author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__package_license__ = "Apache 2.0"
__package_copyright__ ="(c) Jose Riguera"


import os.path
import gettext
import locale

__GETTEXT_DOMAIN__ = "pygpx"
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



# #########################
# Exceptions for GPX module
# #########################

class GPXError(Exception):
    """
    Base class for exceptions in GPX module.
    """
    def __init__(self, msg='GPXPError!'):
        self.value = "%s" % msg
    def __str__(self):
        return repr(self.value)


class GPXErrorTrack(GPXError):
    """
    Exceptions related to error in GPX Track elements
    """
    def __init__(self, msg):
        self.value = _("GPX Track error: '%s'.") % (msg)


class GPXErrorSegment(GPXError):
    """
    Exceptions related to error in GPX TrackSeg elements
    """
    def __init__(self, msg):
        self.value = _("GPX Segment error: '%s'.") % (msg)


class GPXErrorPoint(GPXError):
    """
    Exceptions related to error in GPX wpt elements
    """
    def __init__(self, msg):
        self.value = _("GPX Point element error: '%s'.") % (msg)


class GPXErrorParse(GPXError):
    """
    Exceptions related to XML syntax, correction, well formed ... XML structure.
    """
    def __init__(self, msg):
        self.value = _("Cannot parse GPX data: '%s'.") % (msg)


# EOF
