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
import sys
import os.path
sys.path.append(os.path.join("..", ".."))

import sxmltemplate

# ###############
# Test Code !!!!!
# ###############

def test():
    print "\n* SXMLTemplate TestCase (This is an example!!)\n"
    template = """\
    <slideshow>
        <author>%(AUTHOR)s</author>
        <title>%(TITLE|Titulo de la obra)s</title>
        <slide number="%(NUMBER|0)s">
            <title>%(SLIDE)s</title>
            <point p="punto">El contenido del "%(POINT|punto sin determinar)s" esta bien</point>
	    <desc>%(DESC|)s</desc>
	    <desc2>%(DESCC|)s</desc2>
        </slide>
    </slideshow>"""
    template = sxmltemplate.SXMLTemplate(template)
    print "* Template :"
    print template

    redoelements = ["slideshow.slide"]
    template.setTemplates(redoelements)
    basic = {"AUTHOR": "Fulanito y menganito"}
    template.setRootInfo(basic)
    dom = template.getDom()
    print "* Template with basic info :"
    print dom.toprettyxml()

    data = {"NUMBER": 1, "SLIDE": "Transparencia 1", "POINT": "primer punto"}
    template.setData(data)
    data = {"NUMBER": 2, "SLIDE": "Transparencia final", "POINT": "ultimo punto"}
    template.setData(data)
    dom = template.getDom()
    print "* XML document:"
    print dom.toprettyxml()

    print "\n* End Tests!\n"


if __name__ == "__main__":
    test()

#EOF
