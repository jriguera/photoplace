Development environment for PhotoPlace
======================================

It is made with python 2.x, to install the dependencies on a 
Linux box, you have to do those things in order to get a development 
environment to test or contrib to PhotoPlace:

1. Install python-pyexiv2
  * `sudo apt-get install python-pyexiv2`

2. Install PIL (Python Image Library, version >= 1.1.7) or Pillow:
  * `sudo apt-get install python-pil`

3. Install pyGTK
  * `sudo apt-get install python-gtk2`

Happy coding!


Making packages
===============

* Source distribution package
  * `python setup.py sdist`

* Debian package:
  * `python setup.py bdist_deb`

* Windows package (on windows environment):
  * `python setup.py py2exe [--full]`

* Windows installable package (on windows environment):
  * `python setup.py nsis`

* Installation from setup (Warning, there is no unistaller!)
```
python setup.py install
# and for addons:
python setup.py install_addons
```
