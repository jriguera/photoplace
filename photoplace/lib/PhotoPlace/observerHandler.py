#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       observerHandler.py
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


import sys
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
        for observer in self._observers.keys():
            for (n, a, k) in self._observers[observer]:
                observer._lock.acquire()
                old_n = observer.notifications
                old_a = observer.args
                old_k = observer.kwargs
                observer.notifications = n
                observer.args = a
                observer.kwargs = k
                observer._event = event
                try:
                    observer(*args, **kwargs)
                except Exception as e:
                    msg = "Notification Exception with %s: %s."
                    print(msg % (str(observer), str(e)))
                observer.notifications = old_n
                observer.args = old_a
                observer.kwargs = old_k
                observer._event = None
                observer._lock.release()


# EOF
