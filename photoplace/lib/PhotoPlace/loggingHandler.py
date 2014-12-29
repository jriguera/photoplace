#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       loggingHandler.py
#
#   Copyright 2010-2015 Jose Riguera Lopez <jriguera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
__program__ = "photoplace"
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.6.1"
__date__ = "Dec 2014"
__license__ = "Apache 2.0"
__copyright__ ="(c) Jose Riguera"


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
