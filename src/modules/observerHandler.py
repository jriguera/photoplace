#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       observerHandler.py
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
import logging
import threading



class DObserver(object):
    """
    Class decorator to transform an function/method into a observer.
    """
    _debug = False

    def __init__(self, function):
        object.__init__(self)
        self._function = function
        self._lock = threading.Lock()
        self.notifications = None
        self._event = None
        self.args = ()
        self.kwargs = {}
        self._calls = 0
        self.filters = [
            lambda event, notification: event in notification,
            lambda event, notification: event == notification,
            lambda event, notification: notification is None,
        ]

    def __call__(self, *args, **kwargs):
        localkwargs = {}
        localkwargs.update(kwargs)
        localkwargs.update(self.kwargs)
        ret = None
        if self._event:
            for lambda_filter in self.filters:
                try:
                    value_filter = lambda_filter(self._event, self.notifications)
                    #print "Value Filter = %s : %s : %s" % (value_filter, self._event, self.notifications)
                except:
                    pass
                else:
                    if value_filter:
                        self._calls += 1
                        ret = self._function(*(tuple(self.args) + args), **localkwargs)
                        if self._debug:
                            sys.stderr.write('DObserver(%s:%s): %s\n' % \
                                (self._function.__name__, self.args + args ,str(ret)))
                        break
        else:
            ret = self._function(*(tuple(self.args) + args), **localkwargs)
        return ret

    def __repr__(self):
        return "%s(%s)@(%s:%s)" % \
            (self._function.func_name, self.args, self.notifications, self.filters)

    def __str__(self):
        args = self.args
        if not self.args:
            args = ["..."]
        return "%s(%s) @ (%s |=| %s)" % \
            (self._function.func_name, args, self.notifications, self.filters)



class Observer(object):
    """
    Observer superclass for making an observable class.
    """

    def __init__(self, notifications=None, filters=[]):
        object.__init__(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setNotifications(notifications, filters)
        self._setArgs()

    def _setNotifications(self, notifications=None, filters=[]):
        self.update.filters = filters
        self.update.notifications = notifications

    def _setArgs(self, *args, **kwargs):
        self.update.args = tuple(self,) + args
        self.update.kwargs = kwargs

    @DObserver
    def update(self, *args, **kwargs):
        pass

    def _calls(self):
        return self.update._calls



class Observable(object):

    def __init__(self):
        object.__init__(self)
        self._observers = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def addObserver(self, observer, notifications=None, *args, **kwargs):
        if callable(observer):
            if not observer in self._observers.keys():
                self._observers[observer] = [(notifications, args, kwargs)]
            else:
                for (n, a, k) in self._observers[observer]:
                    if not n:
                        n = notifications
                        break
                    else:
                        # !!!!!!!!
                        if isinstance(n, list):
                            if not notifications in n:
                                n.append(notifications)
                            break
                else:
                    self._observers[observer].append((notifications, args, kwargs))
        else:
            raise TypeError('Object is not a valid observer.')

    def delObserver(self, observer):
        if observer in self._observers.keys():
            del self._observers[observer]

    def listObservers(self):
        return self._observers

    def hasObserver(self, observer):
        try:
            return self._observers[observer]
        except:
            return None

    def notify(self, event=None, *args, **kwargs):
        #print "EVENTI  ------------------------------------>", event
        #print "OBSERVERKEYS: > %s <" % self._observers
        for observer in self._observers.keys():
            #print "*******", observer
            for (n, a, k) in self._observers[observer]:
                #print "@@ %s, %s, %s" % (n,a,k)
                observer._lock.acquire()
                old_n = observer.notifications
                old_a = observer.args
                old_k = observer.kwargs
                observer.notifications = n
                observer.args = a
                observer.kwargs = k
                observer._event = event
                #print "OBSERVER: ", observer
                try:
                    observer(*args, **kwargs)
                except Exception as e:
                    msg = "Notification Exception with %s: %s."
                    self.logger.error(msg % (str(observer), str(e)))
                observer.notifications = old_n
                observer.args = old_a
                observer.kwargs = old_k
                observer._event = None
                observer._lock.release()


# EOF
