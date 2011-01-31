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
      - python setup.py [--full]

   3) Boil an Egg
      - python setup.py bdist_egg

   4) Install as a python package
      - python setup.py install
            - '--no-clean' can be specified to skip old file cleanup

 @summary: Used for building the photoplace distribution files and installations
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "January 2011"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"

import os
import sys
import glob
import shutil
import zipfile
import time
import fnmatch
import datetime
from distutils.core import setup
from distutils import cmd
from distutils import log
from distutils.errors import DistutilsError
from distutils.command.install_data import install_data as _install_data
from distutils.command.build_py import build_py as _build_py
from distutils.command.build import build as _build
from distutils.file_util import copy_file as _copy_file
from distutils.util import byte_compile as _byte_compile

import msgfmt


#http://wiki.maemo.org/Internationalize_a_Python_application
#http://wiki.maemo.org/User:Mohammad7410/Packaging
#http://www.learningpython.com/2006/12/03/translating-your-pythonpygtk-application/


PLATFORM = os.sys.platform
SRC_DIR = 'src'
PROGRAM = 'src/photoplace.py'
VERSION = '0.5.0'
DIST_LIB = 'lib/shared.zip'
DIST_DIR = 'photoplace-' + VERSION
DATE = datetime.datetime.now().strftime("%B %Y")
LANGUAGES = ['en*', 'es*', 'pt'] 
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
    'win32' : os.path.join("logos", "photoplace.ico"),
    'other' : os.path.join("logos", "photoplace.png"),
}


def find_files(base, dir, badfiles=['*.*~'], baddirs=['.*'], goodfiles=['*']):
    def walker(base, dir, files=[]):
        for baddir in baddirs:
            if fnmatch.fnmatch(os.path.basename(dir), baddir):
                return files
        realdir = os.path.join(base, dir)
        list_contents = os.listdir(realdir)
        for f in list_contents:
            if os.path.isfile(os.path.join(realdir, f)):                
                for badfile in badfiles:
                    if fnmatch.fnmatch(f, badfile):
                        break
                else:
                    for goodfile in goodfiles:
                        if fnmatch.fnmatch(f, goodfile):
                            files.append(os.path.join(dir, f))
        for f in list_contents:
            if os.path.isdir(os.path.join(realdir, f)):
                files = walker(base, os.path.join(dir, f), files)
        return files
    return walker(base, dir)

    
def get_files(base, dir, baddirs=['.*'], goodfiles=['*.*'], badfiles=['*.*~']):
    def walker(base, dir, contents=[]):
        for baddir in baddirs:
            if fnmatch.fnmatch(os.path.basename(dir), baddir):
                return contents
        realdir = os.path.join(base, dir)
        list_contents = os.listdir(realdir)
        files = []
        for f in list_contents:
            if os.path.isfile(os.path.join(realdir, f)):
                for badfile in badfiles:
                    if fnmatch.fnmatch(f, badfile):
                        break
                else:
                    for goodfile in goodfiles:
                        if fnmatch.fnmatch(f, goodfile):
                            files.append(os.path.join(realdir, f))
        if files:
            contents.append((dir, files))
        for f in list_contents:
            if os.path.isdir(os.path.join(realdir, f)):
                contents = walker(base, os.path.join(dir, f), contents)
        return contents
    return walker(base, dir)

    
def get_plugins(base, directory):
    lib_dir = os.path.join(base, directory)
    packages = [f for f in os.listdir(lib_dir) 
        if os.path.isdir(os.path.join(lib_dir, f)) and not f.startswith('.')]
    plugins = dict()
    for package in packages:
        data_dir = os.path.join(lib_dir, package)
        package_files = find_files(lib_dir, package, ['*.*~'], ['.*'], ['*.py'])
        package_data = find_files(lib_dir, package, ['*.*~', '*.py*', '*.po'])
        plugins[package] = (data_dir, package_files, package_data)
    return plugins

    
def get_packages(base, directory):
    lib_dir = os.path.join(base, directory)
    packages = [f for f in os.listdir(lib_dir) 
        if os.path.isdir(os.path.join(lib_dir, f)) and not f.startswith('.')]
    package_dir = dict()
    package_data = dict()
    for package in packages:
        data_dir = os.path.join(lib_dir, package)
        package_dir[package] = data_dir
        pkg_data = []
        # No data files allowed at this level dir
        for f in os.listdir(data_dir):
            if os.path.isdir(os.path.join(data_dir, f)):
                pkg_data += find_files(data_dir, f, 
                    ['*.*~', '*.py*', '*.po*'], ['.*', 'test'])
        package_data[package] = pkg_data
    kwargs = dict(packages=packages, package_dir=package_dir, package_data=package_data)
    return kwargs



class build_plugins(cmd.Command):
    description = 'Create core plugins'
    
    def initialize_options(self):
        self.optimize = 1
        self.verbose = 1
        self.base = SRC_DIR
        self.dir = 'plugins'
        self.dist_dir = DIST_DIR
    
    def finalize_options(self):
        pass
    
    def run(self):
        print "*** creating core plugins ***"
        plugins = get_plugins(self.base, self.dir)
        compile_names = list()
        for k, v in plugins.iteritems():
            src, pfiles, pdata = v
            compile_names = []
            for f in pfiles:
                dest = os.path.join(self.dist_dir, self.dir, f)
                dest_dir = os.path.dirname(dest)
                f = os.path.join(self.base, self.dir, f)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                _copy_file(f, dest, preserve_mode=0)
                compile_names.append(dest)
            _byte_compile(compile_names, self.optimize, 1, None, None, self.verbose)
            for f in compile_names:
                os.remove(f)
            for f in pdata:
                dest_dir = os.path.dirname(os.path.join(self.dist_dir, self.dir, f))
                f = os.path.join(self.base, self.dir, f)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                _copy_file(f, dest_dir)


class build_trans(cmd.Command):
    description = 'Compile .po files into .mo files'
    
    def initialize_options(self):
        self.base = SRC_DIR
        self.dist_dir = DIST_DIR
    
    def finalize_options(self):
        pass
    
    def run(self):
        po_dir = os.path.join(os.path.dirname(os.curdir), 'po')
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join('build', 'locale', lang, 'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'mussorgsky.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        print 'Compiling %s' % src
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            print 'Compiling %s' % src
                            msgfmt.make(src, dest)
                            
class build(_build):
    sub_commands = _build.sub_commands + [('build_plugins', None)]
    def run(self):
        _build.run(self)


def get_program_libs(base=SRC_DIR, directory='lib'):
    """
    Generate the list of packages in lib directory
    """
    kwargs = get_packages(base, directory)
    return kwargs

def get_program_plugins(base=SRC_DIR, directory='plugins'):
    """
    Generate the list of plugins
    """
    kwargs = get_packages(base, directory)
    return kwargs
    
def get_data_files(base=SRC_DIR, dirs=['share', 'locale']):
    """
    Generate the list of files for package
    """
    includes = [('.', glob.glob(os.path.join(base, "*.txt")))]
    for directory in dirs:
        includes += get_files(base, directory)
    return includes

def get_bin_files(base='', dirs=['include']):
    includes = []
    for directory in dirs:
        extra_dir = os.path.join(base, directory, os.sys.platform)
        if os.path.exists(extra_dir):
            includes += get_files(os.path.join(directory, os.sys.platform), '')
    return includes



# ##########
# platform builders
# ##########

def build4win(program, icon=None, generatezip=None, data=True, destination=DIST_DIR):
    """
    Generate the list of files needed for pygtk package files
    """
    try:
        import py2exe
    except ImportError:
        print "\n!! You dont have py2exe installed. !!\n"
        sys.exit(1)
    from py2exe.build_exe import py2exe as _py2exe 
    base = os.path.dirname(program)
    # Extend the py2exe command, to also include data files required by gtk+ and
    # enable the "MS-Windows" theme. In order to make gtk+ find the data files
    # we also ensure that the gtk+ libraries are not bundled.
    class py2exe(_py2exe):
        keyfile = 'libgtk-win32-2.0-0.dll'
        gtkthemes = None
        gtktheme = None
        gtkdata = True
        gtkdir = None
        def create_binaries(self, py_files, extensions, dlls):            
            if not self.gtkdir:
                gtkdir = None
                for libdir in os.environ['PATH'].split(os.path.pathsep):
                    test_path = os.path.join(libdir, self.keyfile)
                    if os.path.exists(test_path):
                        gtkdir = os.path.dirname(os.path.dirname(libdir))
                        break
                else:
                    raise DistutilsError('Could not find gtk+ to copy libraries and data files.')
            else:
                gtkdir = self.gtkdir
            _py2exe.create_binaries(self, py_files, extensions, dlls)
            if self.gtkdata:
                for f in find_files(gtkdir, 'lib', ['*.*~'], ['pkgconfig', 'glib-2.0']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    _copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                for f in find_files(gtkdir, 'share', ['*.*~'], 
                    ['gtk-doc', 'aclocal', 'doc', 'man', 'themes', 'locale', 'gtk-2.0', 'glib-2.0']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    _copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                for f in find_files(gtkdir, 'etc', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)                    
                    _copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                # GTK locales
                for lang in LANGUAGES:
                    glob_dir = os.path.join(gtkdir, 'share\\locale', lang, 'LC_MESSAGES\\*.mo')
                    for f in glob.glob(glob_dir):
                        for llang in glob.glob(os.path.join(gtkdir, 'share\\locale', lang)):
                            country = os.path.basename(llang)
                            dest_dir = os.path.join(self.exe_dir, 'share\\locale', country, 'LC_MESSAGES')
                            if not os.path.exists(dest_dir):
                                os.makedirs(dest_dir)
                            _copy_file(f, dest_dir)
                _copy_file(os.path.join(gtkdir, 'share\\locale\\locale.alias'), 
                    os.path.join(self.exe_dir, 'share\\locale'), preserve_mode=0)
            else:
                for f in find_files(gtkdir, 'lib\\gtk-2.0', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    _copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
            if self.gtktheme:
                print "*** Enabling theme for gtk+ ***"
                for f in find_files(self.gtkthemes, os.path.join('share', 'themes'), ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)                    
                    _copy_file(os.path.join(self.gtkthemes, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                gtktheme_dir = os.path.join(self.exe_dir, 'etc', 'gtk-2.0')
                if not os.path.exists(gtktheme_dir):
                    os.makedirs(gtktheme_dir)
                file = open(os.path.join(gtktheme_dir, 'gtkrc'), 'w')
                print >>file, 'gtk-theme-name = "%s"' % self.gtktheme
                file.close()
    
    windows = dict(script=program, icon_resources=[(1, icon)])
    options = dict(
        includes=['encodings', 'gobject', 'glib', 'gio', 'gtk', 'cairo', 'pango', 'pangocairo', 'atk'],
        excludes=['_ssl', '_scproxy', 'ICCProfile', 'bsddb', 'curses', 'tcl', 'Tkconstants', 'Tkinter'],
        dll_excludes=['libglade-2.0-0.dll', 'w9xpopen.exe', 'tcl84.dll', 'tk84.dll'],
        bundle_files=3,
        optimize=2,
        compressed=1,
        ascii=False,
        dist_dir=destination)
    py2exe.gtkdata = data
    py2exe.gtkdir = 'C:\\gtk\\'
    py2exe.gtktheme = "MS-Windows"
    py2exe.gtkthemes = "include\\GTKTheme\\"
    kwargs = dict(
        zipfile=generatezip, 
        windows=[windows], 
        options={'py2exe': options}, 
        cmdclass={'py2exe': py2exe})
    return kwargs

    
def build4pkg(program):
    base = os.path.dirname(program)
    kwargs = dict(scripts=program)
    return kwargs



# ###
# setup
# ###

if __name__ == '__main__':
    sys.path.append(os.path.join(SRC_DIR, 'modules'))
    sys.path.append(os.path.join(SRC_DIR, 'lib'))
    kwargs = {}
    data_files = []
    if PLATFORM == "win32" and 'py2exe' in sys.argv:
        if '--full' in sys.argv:
            sys.argv.remove('--full')
            kwargs = build4win(PROGRAM, ICON['win32'], DIST_LIB)
            data_files = get_bin_files()
        else:
            kwargs = build4win(PROGRAM, ICON['win32'], DIST_LIB, False)
    elif PLATFORM == "darwin" and 'py2app' in sys.argv:
        print "TODO"
    elif 'clean' in sys.argv:
        print "CLEAN"
    kwargs.update(get_program_libs())
    data_files += get_data_files()
    kwargs['cmdclass']['build'] = build
    kwargs['cmdclass']['build_plugins'] = build_plugins
    setup(name='photoplace',
        version=VERSION,
        license='GNU General Public License v3',
        description='A tool for geotagging your photos and ... much more!',
        long_description=open(os.path.join(SRC_DIR, 'readme.txt')).read(),
        author='Jose Riguera Lopez',
        author_email='jriguera@gmail.com',
        classifiers=CLASSIFIERS,
        url='http://code.google.com/p/photoplace/',
        data_files=data_files,
        **kwargs)

# EOF