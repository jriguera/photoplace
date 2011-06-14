
===================
What is PhotoPlace?
===================

It is a multiplatform program (tested on Linux and Windows platforms) 
developed with python 2.x (>= 2.6) to easily geotag your photos. 

Also, with a track log from a GPS device, it can generate a *Google Earth*
/*Maps* layer with your photos. Moreover, the program can be easily adapted 
by editing templates and its functionality can be complemented with plugins, 
for example there is a plugin to generate a music tour that can be used 
to present your photo collection. 


Contact
=======

For more details, visit http://code.google.com/p/photoplace/
As well, you can write suggestions or impressions to 
photoplace-project@googlegroups.com


Donations
=========

The authors and developers hope you like this program. We would really 
appreciate it if you would consider making a small donation: half of the 
money will be donated to a local NGO *Ecodesarrollo Gaia* 
(http://gaiadiaadia.blogspot.com) that helps people in Senegal (Africa), 
with the other half, I would like to visit Australia and,  in connection 
with a geotagging  program, my antipodes in New Zeland, and your coins 
can help me to achieve this goals.


Development
===========

On a Linux box, you have to do those things in order to get a development 
environment to test or contrib to PhotoPlace:

1. Install pyexiv2 (formed python-pyexiv2) version 0.2 (recommended 
   version is 0.2.2) but the latest available version is 0.3 is ok.
   Since pyexiv2 0.2/0.3 is not in the official repositories of Ubuntu/Debian 
   you must download it from https://launchpad.net/~pyexiv2-developers/+archive/ppa/+packages
   and type (for example)::

    $dpkg -i python-pyexiv2_0.3.0-0ubuntu1ppa1~maverick1_i386.deb


2. Install PIL (Python Image Library) version 1.1.7 or superior.
   Since it is in ubuntu repositories, just type::

    $ sudo apt-get install python-imaging


3) Install pyGTK::

    $ sudo apt-get install python-gtk2


Happy coding!


Thanks to
=========

* Noela Sanchez for the idea of this program and translations.
* Vivake Gupta (vivakeATlab49.com) for MP3Info.py (in plugin <tour>)
* Juan Amores, jamores (at) hotmail (dot) com for the suggestions and 
  tests on Windows.




