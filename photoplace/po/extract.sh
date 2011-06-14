#!/bin/sh

intltool-extract --type=gettext/glade ../share/gtkui/photoplace.ui
files=$(find ../lib/PhotoPlace -name "*.py" | xargs)
xgettext --language=Python --keyword=_ --keyword=N_ --from-code=UTF-8 --output=photoplace.pot ../share/gtkui/photoplace.ui.h ../photoplace.py $files

msginit --input=photoplace.pot --locale=en --output-file=../locale/en/LC_MESSAGES/photoplace.mo 
