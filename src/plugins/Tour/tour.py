#! /usr/bin/env python

import sys

from Plugins.Interface import *


try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except:
    print "No hay X"



class KmlTour(Plugin):

    capabilities = { 
        'GTK': True,
    }
    
    def __init__(self, logger, args, argfiles=[], gtkbuilder=None):
        Plugin.__init__(self, logger, args, argfiles, gtkbuilder)
        print "Iniciando el plugin++++++++++++",
        #self.gtkbuilder.add_from_file("/opt/riguera/devel/trunk/plugins/tour.xml")
        self.frame = None
    
    def prueba(self, msg="jaaaaa"):
        print "+ESTO ES UNA FUNCION DEL PLUGIN+%s" % msg

    @DRegister("Faa_ACTIVE")
    def print_data(self, *args, **kwargs):
        if "data" in kwargs:
            print "Received the following: %s" % kwargs["data"]
        else:
            print "Didn't receive any data."

    def init(self, state, widget_container):
        print "cargando init!"
        #        if not self.frame:
        #            self.frame = self.gtkbuilder.get_object("vbox-plugin")
        #            self.frame.unparent()
        #            widget_container.add(self.frame)
        #            widget_container.show_all()
        #            checkbutton_mp3mix = self.gtkbuilder.get_object("checkbutton-mp3mix")
        #            checkbutton_mp3mix.connect('toggled', self.prueba)
        print "cargado!"

    def end(self, state):
        print "ending"
        self.logger.info("end")
        #self.frame.destroy()
        #self.frame = None
        pass

