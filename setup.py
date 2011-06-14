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
#
# http://wiki.maemo.org/Internationalize_a_Python_application
# http://wiki.maemo.org/User:Mohammad7410/Packaging
# http://www.learningpython.com/2006/12/03/translating-your-pythonpygtk-application/
"""
PhotoPlace Setup Script

 USAGE:
 
 * To see all available commands:
    - python setup.py --help-commands

 * Make a source distribution file
    - python setup.py sdist

 * Make a debian/ubuntu package:
    - python setup.py bdist_deb

 * Make for windows (on windows):
    - python setup.py py2exe [--full]
   
 * Create an installer (for windows)
    - python setup.py bdist_wininst

 * Install
     - python setup.py install
     # and plugins!
     - python setup.py install_plugins

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

import msgfmt

from distutils.core import setup
from distutils import cmd
from distutils import log
from distutils.spawn import spawn
from distutils.errors import DistutilsError
from distutils.dir_util import remove_tree as _remove_tree
from distutils.dir_util import copy_tree as _copy_tree
from distutils.command.install_data import install_data as _install_data
from distutils.command.install import install as _install
from distutils.command.install_lib import install_lib as _install_lib
from distutils.command.build_py import build_py as _build_py
from distutils.command.build import build as _build
from distutils.command.sdist import sdist as _sdist
from distutils.command.clean import clean as _clean
__WIN_PLATFORM__ = False
try:
    import py2exe
    from py2exe.build_exe import py2exe as _py2exe 
    __WIN_PLATFORM__ = True
except ImportError:
    if sys.platform.startswith('win'):
        print "\n!! You do not have py2exe installed. !!\n"


PLATFORM = os.sys.platform
SRC_DIR = 'photoplace'
PROGRAM = 'photoplace/photoplace.py'
VERSION = '0.5.0'
DATE = datetime.datetime.now().strftime("%B %Y")
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Information Technology',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Natural Language :: Spanish',
    'Operating System :: Microsoft :: Windows :: Windows NT/2000',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering :: GIS',
    'Topic :: Utilities',
]
ICON = { 
    'win32' : os.path.join("logos", "photoplace.ico"),
    'other' : os.path.join("logos", "photoplace.png"),
}
PLUGINSDIR = '_plugins_'


# ########################
# Generic helper functions
# ########################

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


def get_files(base, dir, dst, baddirs=['.*'], goodfiles=['*.*'], badfiles=['*.*~']):
    def walker(base, dir, dst, contents=[]):
        for baddir in baddirs:
            if fnmatch.fnmatch(os.path.basename(dir), baddir):
                return contents
        realdir = os.path.join(base, dir)
        try:
            list_contents = os.listdir(realdir)
        except:
            return contents
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
            contents.append((dst, files))
        for f in list_contents:
            if os.path.isdir(os.path.join(realdir, f)):
                contents = walker(base, os.path.join(dir, f), os.path.join(dst, f), contents)
        return contents
    return walker(base, dir, dst)


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



# #########################
#  Custom distutils classes
# #########################

class build_trans(cmd.Command):
    description = 'compile .po files into .mo files'
    user_options = [
        ('trans-base=', 'b', "base directory of locales"),
        ('trans-dir=', None, "base directory of locales"),
        ('trans-dist=', 'd', "base directory for build locales"),
        ('trans-domain=', None, "base directory for build locales"),
    ]

    def initialize_options(self):
        self.trans_base = None
        self.trans_dist = None
        self.trans_domain = None
        self.trans_dir = None
    
    def finalize_options(self):
        if self.trans_base == None:
            self.trans_base = ''
        if self.trans_dist == None:
            self.trans_dist = 'locale'
        if self.trans_domain == None:
            self.trans_domain = 'domain.mo'
        if self.trans_dir == None:
            self.trans_dir = 'po'
    
    def run(self):
        po_dir = os.path.join(self.trans_base, self.trans_dir)
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join(self.trans_dist, lang, 'LC_MESSAGES')
                    dest = os.path.join(dest_path, self.trans_domain)
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        print 'Compiling locale %s to %s' % (src, dest)
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            print 'Compiling locale %s to %s' % (src, dest)
                            msgfmt.make(src, dest)



class build(_build):
    sub_commands = _build.sub_commands + [('build_trans', None)]

    def initialize_options(self):
        _build.initialize_options(self)

    def finalize_options(self):
        _build.finalize_options(self)

    def run(self):
        return _build.run(self)



class install(_install):
    #sub_commands = _install.sub_commands + [('install_plugins', None)]
    
    def initialize_options(self):
        _install.initialize_options(self)

    def finalize_options(self):
        _install.finalize_options(self)

    def run(self):
        return _install.run(self)



class install_plugins(cmd.Command):
    description = 'install plugins'
    user_options = [
        ('plugins-dir=', None, "base directory of plugins"),
        ('plugins-dist=', 'd', "base directory to install plugins"),
    ]

    def initialize_options(self):
        self.plugins_dist = None
        self.plugins_dir = None
    
    def finalize_options(self):
        if self.plugins_dist == None:
            install = self.get_finalized_command('install')
            self.plugins_dist = os.path.join(install.install_data,'share', 'photoplace')
        if self.plugins_dir == None:
            install = self.get_finalized_command('install')
            self.plugins_dir = os.path.join(install.install_lib, 'PhotoPlace', PLUGINSDIR)
    
    def run(self):
        destination = os.path.join(self.plugins_dist, 'plugins')
        try:
            print "Creating symlink " + destination
            os.symlink(self.plugins_dir, destination)
        except:
            print "Cannot create symlink, copying plugins to " + destination
            _copy_tree(self.plugins_dir, destination, preserve_symlinks=1, update=1, verbose=1)



class clean(_clean):

    def run(self):
        _clean.run(self)
        dist_dir = ['bdist', 'build', 'dist']
        full_name = self.distribution.get_fullname()
        for dist in dist_dir:
            if os.path.isdir(dist):
                _remove_tree(dist, dry_run=self.dry_run)



if __WIN_PLATFORM__:
    # Extend the py2exe command, to also include data files required by gtk+ and
    # enable the "MS-Windows" theme. In order to make gtk+ find the data files
    # we also ensure that the gtk+ libraries are not bundled.
    
    class py2exe(_py2exe):
        description = "make a windows executable"
        keyfile = 'libgtk-win32-2.0-0.dll'
        gtkthemes = None
        gtktheme = None
        gtkdata = True
        gtkdir = None
        plugins = None
        plugindir = ''
        languages = ['en', 'en_GB', 'es', 'gl']
        
        def initialize_options(self):
            _py2exe.initialize_options(self)
        
        def create_binaries(self, py_files, extensions, dlls):
            if self.gtkdir == None:
                gtkdir = None
                # Fetchs gtk2 path from registry
                import _winreg
                import msvcrt
                try:
                    k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\GTK\\2.0")
                except EnvironmentError:
                    raise DistutilsError('Could not find gtk+ 2.2 Runtime Environmet to copy libraries and data files.')
                else:
                    dir = _winreg.QueryValueEx(k, "Path")
                    os.environ['PATH'] += ";%s/lib;%s/bin" % (dir[0], dir[0])
                    gtkdir = dir[0]
            else:
                gtkdir = self.gtkdir
            _py2exe.create_binaries(self, py_files, extensions, dlls)
            if self.gtkdata:
                for f in find_files(gtkdir, 'lib', ['*.dll.a', '*.def', '*.lib'], ['pkgconfig', 'glib-2.0']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                for f in find_files(gtkdir, 'etc', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                # GTK locales
                for lang in self.languages:
                    glob_dir = os.path.join(gtkdir, 'share\\locale', lang, 'LC_MESSAGES\\*.mo')
                    for f in glob.glob(glob_dir):
                        for llang in glob.glob(os.path.join(gtkdir, 'share\\locale', lang)):
                            country = os.path.basename(llang)
                            dest_dir = os.path.join(self.exe_dir, 'share\\locale', country, 'LC_MESSAGES')
                            if not os.path.exists(dest_dir):
                                os.makedirs(dest_dir)
                            self.copy_file(f, dest_dir)
                self.copy_file(os.path.join(gtkdir, 'share\\locale\\locale.alias'), 
                    os.path.join(self.exe_dir, 'share\\locale'), preserve_mode=0)
                # GTK Themes
                for f in find_files(gtkdir, 'share\\themes', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(gtkdir, f), os.path.join(self.exe_dir, f), preserve_mode=0)
            if self.gtktheme != None:
                print("*** Enabling additional themes for gtk+ ***")
                for f in find_files(self.gtkthemes, 'share\\themes', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(self.gtkthemes, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                for f in find_files(self.gtkthemes, 'lib\\gtk-2.0', ['*.*~']):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(self.gtkthemes, f), os.path.join(self.exe_dir, f), preserve_mode=0)
                gtktheme_dir = os.path.join(self.exe_dir, 'etc', 'gtk-2.0')
                if not os.path.exists(gtktheme_dir):
                    os.makedirs(gtktheme_dir)
                file = open(os.path.join(gtktheme_dir, 'gtkrc'), 'w')
                file.write("# Generated from setup.py\n")
                file.write('gtk-theme-name = "%s"\n' % self.gtktheme)
                file.close()
            # Plugins
            if self.plugins != None:
                print("*** Copying core plugins ***")
                build = self.get_finalized_command('build')
                orig_plugin_dir = os.path.join(build.build_base, self.plugins)
                for f in find_files(orig_plugin_dir, ''):
                    dest_dir = os.path.dirname(os.path.join(self.exe_dir, self.plugindir, f))
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    self.copy_file(os.path.join(orig_plugin_dir, f), dest_dir, preserve_mode=0)


    class bdist_win(cmd.Command):
        description = "make an instalable with NSIS on windows platforms"
        user_options =  py2exe.user_options +  [
            ('nsis=', 'n', "nsis script"),
        ]
        
        def initialize_options(self):
            self.verbose = 3
            self.nsis = None
        
        def finalize_options(self):
            self.verbose = 3
            if self.nsis == None:
                self.nsis = 'setup.nsi'

        def run(self):
            self.run_command('py2exe')
            self.make_nsis()
        
        def make_nsis(self):
            try:
                import _winreg
                # Get the path of the NSIS compiler
                key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, 'NSIS.Script\\shell\\compile\\command')
                compilerPath = _winreg.QueryValueEx(key, '')[0]
                secondQuote = compilerPath.find('"', 1)
                compilerPath = compilerPath[1:secondQuote]
                compilerPath = compilerPath.replace('makensisw', 'makensis') 
            except:
                print 'Error: could not find registry entry for NSIS!'
                print 'Using sytem Path ....'
                compilerPath = 'makensis.exe'
            cmd = [compilerPath, '/V%d' % self.verbose, self.nsis]
            try:
                spawn(cmd, verbose=1)
            except DistutilsError as e:
                print ("Execution failed: %s" % str(e))
else:
    # Not a windows platform
    
    class bdist_deb(_sdist):
        description = "make an instalable for debian/ubuntu platforms"
        user_options =  _sdist.user_options +  [
            ('debian=', None, "debian dir"),
        ]
        
        def initialize_options(self):
            _sdist.initialize_options(self)
            self.debian = None
            self.dist_dir = None
            self.keep_temp = True
            self.format = None
            self.buildcmd = None
            self.buildargs = [] 
        
        def finalize_options(self):
            _sdist.finalize_options(self)
            if self.debian == None:
                self.debian = 'debian'
            self.dist_dir = 'bdist'
            self.keep_temp = True
            self.format = 'gztar'
            self.buildcmd = 'dpkg-buildpackage'
            self.buildargs = ['-uc', '-us'] 
        
        def get_file_list(self):
            _sdist.get_file_list(self)
            for f in find_files('.', self.debian):
                self.filelist.append(f)
        
        def make_release_tree(self, base_dir, files):
            if os.path.isdir(base_dir):
                _remove_tree(base_dir, dry_run=self.dry_run)
            _sdist.make_release_tree(self, base_dir, files)
        
        def make_distribution(self):
            full_name = self.distribution.get_fullname()
            base_dir = os.path.join(self.dist_dir, full_name)
            self.make_release_tree(base_dir, self.filelist.files)
            archive_files = []
            name = self.distribution.get_name()
            version = self.distribution.get_version()
            base_name = os.path.join(self.dist_dir, name + '_' + version + '.orig')
            filename = self.make_archive(base_name, self.format, self.dist_dir, full_name)
            archive_files.append(filename)
            self.distribution.dist_files.append((self.dist_dir, '', filename))
            filename = self.make_debian(base_dir)
            self.archive_files = archive_files
            if not self.keep_temp:
                _remove_tree(base_dir, dry_run=self.dry_run)
        
        def make_debian(self, base_dir):
            cmd = [self.buildcmd] + self.buildargs
            try:
                os.chdir(base_dir)
                spawn(cmd, verbose=1)
            except DistutilsError as e:
                print ("Execution failed: %s" % str(e))
                return None
            name = self.distribution.get_name()
            version = self.distribution.get_version()
            return name + '_' + version + '-1_all.deb'



# ######################
# setup helper functions
# ######################

def get_program_libs(base, directory='lib', plugin_dir=PLUGINSDIR):
    """
    Generate the list of packages in lib directory
    """
    libs = get_packages(base, directory)
    
    libs_photoplace = get_packages(os.path.join(base, directory), 'PhotoPlace')
    for lib in libs_photoplace['packages']:
        libs['packages'].append('PhotoPlace.' + lib)
        for key, data in libs_photoplace['package_data'].iteritems():
            libs['package_data']['PhotoPlace.' + key] = data
        for key, data in libs_photoplace['package_dir'].iteritems():
            libs['package_dir']['PhotoPlace.' + key] = data
    
    plugins_photoplace = get_packages(base, 'plugins')
    for lib in plugins_photoplace['packages']:
        libs['packages'].append('PhotoPlace.' + plugin_dir + '.' + lib)
        for key, data in plugins_photoplace['package_data'].iteritems():
            libs['package_data']['PhotoPlace.' + plugin_dir + '.' + key] = data
        for key, data in plugins_photoplace['package_dir'].iteritems():
            libs['package_dir']['PhotoPlace.' + plugin_dir + '.' + key] = data
    
    return libs


# #####
# setup
# #####

if __name__ == '__main__':
    sys.path.append(os.path.join(SRC_DIR, 'lib'))
    kwargs = {}
    kwargs['cmdclass'] = {}
    kwargs['options'] = {}
    data_files = get_files(SRC_DIR, 'share', os.path.join('share', 'photoplace'))
    if PLATFORM == "win32":
        if '--full' in sys.argv:
            sys.argv.remove('--full')
            extra_dir = os.path.join('include', os.sys.platform)
            if os.path.exists(extra_dir):
                data_files += get_files(os.path.join('include', os.sys.platform), '', '')
        py2exe.gtktheme = 'Human'
        py2exe.gtkthemes = "include\\GTKThemes\\"
        py2exe.plugins = os.path.join('lib', 'PhotoPlace', PLUGINSDIR)
        py2exe.plugindir = os.path.join('share', 'photoplace', 'plugins')
        kwargs['windows'] = [{
            'script':PROGRAM, 
            'icon_resources':[(1, ICON['win32'])]
        }]
        kwargs['options']['py2exe'] = {
            'includes': ['encodings', 'gobject', 'glib', 'gio', 'gtk', 'cairo', 'pango', 'pangocairo', 'atk'],
            'excludes': ['_ssl', '_scproxy', 'ICCProfile', 'bsddb', 'curses', 'tcl', 'Tkconstants', 'Tkinter'],
            'dll_excludes': ['libglade-2.0-0.dll', 'w9xpopen.exe', 'tcl84.dll', 'tk84.dll'], 
            'bundle_files': 3,
            'optimize': 2,
            'compressed': 1,
            'ascii': False,
            'dist_dir': os.path.join('bdist', 'photoplace-' + VERSION)
        }
        kwargs['zipfile'] = os.path.join('lib', 'shared.zip')
        kwargs['cmdclass']['py2exe'] = py2exe
        data_files += [('.', glob.glob(os.path.join(SRC_DIR, "*.txt")))]
        data_files += get_files(SRC_DIR, 'locale', 'locale')
        kwargs['cmdclass']['nsis'] = bdist_win
        kwargs['cmdclass']['bdist_wininst'] = bdist_win
    elif PLATFORM == "darwin" and 'py2app' in sys.argv:
        print "TODO ..."
        sys.exit()
    else:
        data_files += get_files(SRC_DIR, 'locale', os.path.join('share', 'locale'), goodfiles=['*.mo'])
        data_files += [(os.path.join('share','doc','photoplace'), glob.glob(os.path.join(SRC_DIR, "*.txt")))]
        kwargs['cmdclass']['bdist_deb'] = bdist_deb
    kwargs.update(get_program_libs(SRC_DIR))
    kwargs['cmdclass']['build'] = build
    kwargs['cmdclass']['clean'] = clean
    kwargs['cmdclass']['install'] = install
    kwargs['cmdclass']['install_plugins'] = install_plugins
    kwargs['cmdclass']['build_trans'] = build_trans
    kwargs['options']['build_trans'] = { 
        'trans_base': SRC_DIR, 
        'trans_dist': os.path.join(SRC_DIR, 'locale'),
        'trans_domain': "photoplace.mo",
    }
    setup(name='photoplace',
        version=VERSION,
        license='GNU General Public License v3',
        description='A tool for geotagging your photos and ... much more!',
        long_description=open(os.path.join(SRC_DIR, 'README.txt')).read(),
        author='Jose Riguera Lopez',
        author_email='jriguera@gmail.com',
        classifiers=CLASSIFIERS,
        platforms="Python 2.6 and superior",
        url='http://code.google.com/p/photoplace/',
        scripts=[PROGRAM],
        data_files=data_files,
        **kwargs)

# EOF
