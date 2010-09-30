#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       setup.py
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
PhotoPlace Setup Script

 USAGE:

   1) Windows:
      - python setup.py py2exe

   2) MacOSX:
      - python setup.py py2app

   3) Boil an Egg
      - python setup.py bdist_egg

   4) Install as a python package
      - python setup.py install
            - '--no-clean' can be specified to skip old file cleanup

 @summary: Used for building the editra distribution files and installations

"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import os
import sys
import glob
import shutil
import zipfile
import time


__platform__ = os.sys.platform


PROGRAM = ['PhotoPlace.py']
AUTHORS = {
    'Jose Riguera': "jriguera@gmail.com"
}
DATE = "September 2010"
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved',
    'Natural Language :: English',
    'Natural Language :: Spanish',
    'Natural Language :: Swedish',
    'Natural Language :: Turkish',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Programming Language :: Python',
]
ICON = { 
    'win32' : os.path.join("images","photoplace.ico"),
    'darwin' : os.path.join("images","photoplace.icns"),
    'other' : os.path.join("images","photoplace.png"),
}


def GenerateBinPackageFiles():
    """
    Generate the list of files needed for py2exe/py2app package files
    """
    files = [ 
        "readme.txt", 
        "license.txt", 
        "thanks.txt", 
        "install.txt", 
        "todo.txt" 
    ]
    files =["photoplace.ui"]
    
    includes = []
    include_dir = os.path.join("include", os.sys.platform)
    if os.path.exists(include_dir):
        include_dir = os.path.join(include_dir, "*")
        includes.append(("include", glob.glob(include_dir)))
    
    templates = [
        ("templates", glob.glob(os.path.join("templates","*.*"))),
    ]
    
    pixmaps = [
        ("pixmaps", glob.glob(os.path.join("include","*.*"))),
    ]
    
    locales = []
    for locale_dir in os.listdir("locale"):
        tmp_dir = os.path.join(os.path.join(locale, locale_dir), "LC_MESSAGES")
        if os.path.isdir(tmp_dir):
            locales.append((tmp_dir, glob.glob(os.path.join(tmp_dir,"*.mo"))))
    
    return includes + pixmaps + files + locales


def GeneratePluginPackageFiles():
    plugins = [
        ("plugins", glob.glob(os.path.join("plugins","*"))),
    ]
    return plugins


def BuildPy2Exe():
    """
    Generate the Py2exe files
    """
    from distutils.core import setup
    try:
        import py2exe
    except ImportError:
        print "\n!! You dont have py2exe installed. !!\n"
        sys.exit(1)

    # put package on path for py2exe
    sys.path.append(os.path.abspath('dist/'))
    sys.path.append(os.path.abspath('dist/extern'))

    sys.path.append('modules')
    sys.path.append('lib')

    DATA_FILES = GenerateBinPackageFiles()

    opts = {
        'py2exe': {
            'packages': ['encodings', 'gtk', 'cairo', 'gobject', 'gio', 'pango', 'pangocairo', 'atk' ],
            #'includes': ['gpx', 'toolbox', 'xmltemplate'],
            'excludes': [
                # silence some warnings of missing modules
                '_scproxy',
                'email',
                'email.utils',
                'email.Utils',
                'ICCProfile',

                # filter out unused .pyd files

                # filter out unused .pyo files in library.zip

                
            ],
            'dll_excludes': ["libglade-2.0-0.dll", "w9xpopen.exe"],
            'bundle_files': 3,
            'optimize': 2,
            'compressed': 1,
            'dist_dir': 'dist',
        }
    }

    setup(
        name = "PhotoPlace",
        version = "0.5.0",
        options = opts,
        windows = [{
            "script": "photoplace.py",
            #"icon_resources": [(1, ICON['win32'])],
        }],
        description = "PhotoPlace",
        author = "Jose Riguera",
        author_email = "jriguera@gmail.com",
        license = "licencia",
        url = "http://",
        data_files = DATA_FILES,
    )


if __name__ == '__main__':
    if __platform__ == "win32" and 'py2exe' in sys.argv:
        BuildPy2Exe()
    elif __platform__ == "darwin" and 'py2app' in sys.argv:
        print "TODO"
    elif 'eclib' in sys.argv:
        print "TODO"
    elif 'clean' in sys.argv:
        print "CLEAN"
    else:
        print "do source"


