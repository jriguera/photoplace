#!/bin/sh

intltool-extract --type=gettext/glade ../share/gtkui/photoplace.ui
files=$(find ../lib/PhotoPlace -name "*.py" | xargs)
xgettext --language=Python --keyword=_ --keyword=N_ --output=photoplace.pot ../share/gtkui/photoplace.ui.h ../photoplace.py $files
 
