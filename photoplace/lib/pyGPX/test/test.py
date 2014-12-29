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
