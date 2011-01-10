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
# Copyright © 2010 Jose Riguera Lopez <jriguera@gmail.com>
#
"""
Exceptions for GPX package.
"""

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
