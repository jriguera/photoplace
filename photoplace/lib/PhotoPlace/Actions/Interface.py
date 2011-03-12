#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Interface.py
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


import sys
import threading
import logging

import PhotoPlace.observerHandler as observerHandler



class Action(observerHandler.Observable):
    """
    'Abstract' class for implementing an observable action. It inherits from 'Observable'
    and is ready for threading purposes. The subclasses can overwrite 3 methods: 'ini', 'go'
    and 'end'.
    """
    separator_event_class = ':'
    tag_ini_event = "ini"
    tag_end_event = "end"
    tag_run_event = "run"
    tag_start_event = "start"
    tag_startgo_event = "startgo"
    tag_finishgo_event = "finishgo"
    tag_finish_event = "finish"

    def __init__(self, state, locks=[]):
        observerHandler.Observable.__init__(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dgettext = {}
        self.state = state
        self.locks = locks

    def ini(self, *args, **kwargs):
        self._notify_ini(None)
        self.logger.debug(_("Starting ..."))
        return None

    def go(self, rini):
        self._notify_run(None)
        return None

    def end(self, rgo):
        self.logger.debug(_("Finished ..."))
        self._notify_end(None)
        return rgo

    @classmethod
    def action_ini_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_ini_event
        return e

    @classmethod
    def action_end_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_end_event
        return e

    @classmethod
    def action_run_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_run_event
        return e

    @classmethod
    def action_start_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_start_event
        return e

    @classmethod
    def action_startgo_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_startgo_event
        return e

    @classmethod
    def action_finishgo_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_finishgo_event
        return e

    @classmethod
    def action_finish_event(cls, e=None):
        if not e:
            return cls.__name__ + cls.separator_event_class + cls.tag_finish_event
        return e


    def _notify_ini(self, *args, **kwargs):
        self.notify(self.__class__.action_ini_event(), *args, **kwargs)

    def _notify_run(self, *args, **kwargs):
        self.notify(self.__class__.action_run_event(), *args, **kwargs)

    def _notify_end(self, *args, **kwargs):
        self.notify(self.__class__.action_end_event(), *args, **kwargs)

    def run(self, *args, **kwargs):
        self.state.slock.acquire()
        for lock in self.locks:
            lock.acquire()
        self.state.slock.release()
        try:
            self.notify(self.__class__.action_start_event(), self.state, *args, **kwargs)
            rini = self.ini(*args, **kwargs)
            self.notify(self.__class__.action_startgo_event(), rini)
            rgo = self.go(rini)
            self.notify(self.__class__.action_finishgo_event(), rgo)
            rend = self.end(rgo)
            self.notify(self.__class__.action_finish_event(), rend)
        except:
            raise
        finally:
            for lock in self.locks:
                lock.release()
        return rgo


# EOF
