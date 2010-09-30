#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       loggingHandler.py
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
"""
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.5.0"
__date__ = "September 2010"
__license__ = "GPL (v2 or later)"
__copyright__ ="(c) Jose Riguera, September 2010"


import logging
import sys

import observerHandler



class MessageFilter(logging.Filter):
    """
    A handler class to filter different kind of records
    """
    
    def __init__(self, name="", filters=[]):
        """
        Initialize the handler.
        
        By default, it is a simple way to prevent any messages from getting
        through, because no filters are defined.
        """
        logging.Filter.__init__(self, name)
        self._filters = filters
    
    def setFilter(self, filters=[logging.INFO, logging.ERROR]):
        """
        Sets up default filters. With no args, only logs with severity INFO
        and ERROR are allowed. It is useful for a console command based program.
        """
        self._filters = filters
    
    def filter(self, record):
        """
        Filters all incoming records with an OR operation with all defined
        filters.
        """
        for f in self._filters:
            if record.levelno == f:
                return True
        return False



class LogRedirectHandler(logging.Handler, observerHandler.Observable):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used. Also, it can be used to set messages
    to a gtkTextView and gtkStatusbar in the GUI
    """
    
    def __init__(self, console=sys.stdout, activate=True, notify=True):
        """
        Initialize the handler.

        If strm is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        observerHandler.Observable.__init__(self)
        self._console = console
        self._activate = activate
        self._notify = notify
        self._lfilters = [logging.INFO, logging.ERROR]

    def flush(self):
        """
        Flushes ONLY the console stream.
        """
        if self._activate:
            self._console.flush()

    def setFilter(self, filters=[]):
        """
        Sets up default filters. With no args, no log record are allowed.
        """
        self._lfilters = filters

    def emit(self, record):
        """
        Emits a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline
        [N.B. this may be removed depending on feedback]. If exception
        information is present, it is formatted using
        traceback.print_exception and appended to the stream.
        """
        if self._activate:
            for f in self._lfilters:
                if record.levelno == f:
                    msg = self.format(record)
                    self._console.write("%s\n" % msg)
                    self.flush()
                    break
        if self._notify:
            self.notify(record, record)


# EOF
