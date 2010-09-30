#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# __init__.py:  defines this directory as the 'gpx' package.
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
GPX Module
More information, see test code.
"""
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.1.0"
__date__ = "April 2010"
__license__ = "GPL (v3 or later)"
__copyright__ ="(c) Jose Riguera"


__package_name__ = "gpx"
__package_revision__ = '0'
__package_version__ = '0.1.0'
__package_released__ = "April 2010"
__package_author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__package_license__ = "GPL (v3 or later)"
__package_copyright__ ="(c) Jose Riguera, April 2010"


__all__ = ["gpxdata", "geomath", "gpxparser", "exceptions"]
from exceptions import *
from geomath import *
from gpxdata import *
from gpxparser import *


# EOF
