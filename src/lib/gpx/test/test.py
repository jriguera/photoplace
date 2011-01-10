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
import sys
import os.path
sys.path.append(os.path.join("..",".."))

import gpx


# ###############
# Test Code !!!!!
# ###############

def test(f):
    print "\n* GPX TestCase (This is an example!!)\n"

    print "Loading GPX file %s ..." % f
    fd = open(f)
    gpxparse = gpx.GPXParser(fd, f)
    gpxdata = gpxparse.gpx
    print gpxdata
    tracks = gpxdata.tracks
    for track in tracks:
        print "* Length: " 
        print track.lengthMinMaxTotal()
        print "* Times: "
        print track.timeMinMaxDuration()
        print "* Speed: " 
        print track.speedMinAvgMax()
        
    
    print "\n* End Tests!\n"


if __name__ == "__main__":
    test(sys.argv[1])

#EOF
