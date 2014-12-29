#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# __init__.py:  defines this directory as the 'gpx' package.
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
GPX Module
More information, see test code.
"""
__package_name__ = "gpx"
__package_revision__ = '0'
__package_version__ = '0.1.1'
__package_released__ = "Dec 2014"
__package_author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__package_license__ = "Apache 2.0"
__package_copyright__ ="(c) Jose Riguera"


__all__ = ["gpxdata", "geomath", "gpxparser", "exceptions"]
from exceptions import *
from geomath import *
from gpxdata import *
from gpxparser import *


# EOF
