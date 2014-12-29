In order to run in windows you have to install:

	1) python-2.7.9.msi 
        2) Pillow-2.6.1.win32-py2.7.exe
        3) pygtk-all-in-one-2.24.2.win32-py2.7.msi
	4) pyexiv2-0.3.2-setup.exe

Then, to run photoplace (the gtk2 theme will not be loaded):
	
	$cmd$ photoplace.py


If you have to compile the installer you also will need:

	1) py2exe-0.6.9.win32-py2.7.exe
	2) gtk2-runtime-2.24.10-2012-10-10-ash.exe
	3) nsis-2.46-setup.exe (all components)

and to build the installer type (in the root project folder):

	$cmd$ setup.py nsis

