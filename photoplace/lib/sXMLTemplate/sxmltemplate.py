#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright © 2008 Jose Riguera Lopez <jriguera@gmail.com>
#
"""
Main implementation for SXMLTemplate module.
"""
__author__ = "Jose Riguera Lopez <jriguera@gmail.com>"
__version__ = "0.4.0"
__date__ = "December 2010"
__license__ = "GPL (v3 or later)"
__copyright__ ="(c) Jose Riguera"


import xml.dom.minidom
import string
import os.path
import gettext
import locale

__GETTEXT_DOMAIN__ = "sxmltemplate"
__PACKAGE_DIR__ = os.path.abspath(os.path.dirname(__file__))
__LOCALE_DIR__ = os.path.join(__PACKAGE_DIR__, "locale")

try:
    if not os.path.isdir(__LOCALE_DIR__):
        print ("Error: Cannot locate default locale dir: '%s'." % (__LOCALE_DIR__))
        __LOCALE_DIR__ = None
    locale.setlocale(locale.LC_ALL,"")
    t = gettext.translation(__GETTEXT_DOMAIN__, __LOCALE_DIR__, fallback=False)
    _ = t.ugettext
except Exception as e:
    print ("Error setting up the translations: %s" % (str(e)))
    _ = lambda s: unicode(s)

import exceptions


# ###################################
# SXMLTemplate implementation package
# ###################################

class SXMLTemplate:
    """
    Base class for Simple XML Templates

    It generates a XML DOM document that is based on a xml template source (file, string ...) 
    that will be filled with external data by appending the selected new xml elements with  
    data. Into XML input template, it changes all keys with the format $(key|defautlvalue)s 
    into the data of "key" from the param dictionary, "defaultvalue" if key is not found 
    in dictionary or "deletetag" to remove tag (and children). 
    
    Public Attibutes:

        :param sizeLimit: = 1024 -> (bytes) max size of template source.
        :param separatorKey: = "|" -> separator for default key values.
        :param separatorXml: = "." -> separator to indicates repeateable elements.
        :param defaultValue: = "NULL" -> default value for keys without default values.
        :param deletetag: = "" -> with this value, a key will be deleted if not exists.
    """
    sizeLimit = 1048576 
    separatorKey = "|"
    separatorXml = "."
    defaultValue = " "
    deletetag = ""
    magic = "-#_---__-"


    class TemplateDict(dict):
        """
        Class for string templates with dictionaries objects and operator %

        This class inherits all attributes, methods, ... from dict and redefines "__getitem__"
        in order to return a default value when an element is not found. The format 
        "key<separator>defaultvalue" indicates that if "key" is not found, then "defaultvalue" 
        will be returned. It is like an OR: returns value or "defaultvalue". 
        It is possible to define a global default value for all keys.
        """
        def __getitem__(self, key):
            try:
                k, default = key.split(SXMLTemplate.separatorKey, 1)
            except ValueError:
                k = key.split(SXMLTemplate.separatorKey, 1)[0]
                default = SXMLTemplate.defaultValue
            random = SXMLTemplate.magic
            value = self.get(k, default + random)
            if value == SXMLTemplate.deletetag + random:
                raise UserWarning
            return self.get(k, default)


    def __init__(self, source, redoelements=[]):
        """
        SXMLTemplate class constructor
        
        :Parameters:
            -`source`: URI, filename, or string of XML template.
            -`redoelements`: list of XML nodes to repeat into XML with data.
        """
        self.dom = None
        self.parents = []
        self.templatecounter = 0
        self.templates = []
        self.templatedom = None
        self.rawtemplate = None
        self.redoelements = redoelements
        # Open stream (file, string ...) and read it
        fd = None
        try: 
            fd = self._open(source)
            self.rawtemplate = fd.read(self.sizeLimit)
        except IOError as (errno, strerror):
            raise exceptions.SXMLTemplateErrorLoad(file, errno, strerror)
        else:
            if fd:
                fd.close()
        # Parse XML and checks that it is correct, well formed ...
        try:
            self.dom = xml.dom.minidom.parseString(self.rawtemplate)
            self._delWhiteNodes(self.dom.documentElement)
        except Exception as msg:
            raise exceptions.SXMLTemplateErrorParse(msg)
        self._checkNodeTemplate()
        self.templatedom = self.dom.documentElement.cloneNode(True)
        self.setTemplates(redoelements)


    def __str__(self):
        """
        Dumps the XML DOM structure from memory with indent like "toprettyxml" function
        from  "xml.dom.minidom" module.
        """
        return self.dom.toprettyxml()


    def setTemplates(self, redoelements=[]):
        """
        Sets up the list of nodes of template to be repeated with new data. 
        With each value, these nodes will be created with new data.
        Each node is indicated with the format: "xmlrootnode.subnode---subnode.node"
        
        :Parameters:
            -`redoelements`: list of XML nodes to repeat into XML.
        """
        self.parents = []
        self.templatecounter = 0
        self.templates = []
        self.redoelements = redoelements
        for element in redoelements:
            # split nodes to repeat
            listelement = element.split(self.separatorXml)
            # if xml root element is not the first, error
            if listelement[0] != self.dom.documentElement.nodeName:
                raise SXMLTemplateErrorRedo(element)
            oldcounter = self.templatecounter
            listelement.reverse()
            for node in self.dom.getElementsByTagName(listelement[0]):
                # test if this is the correct node
                parent = node.parentNode
                for xmlelement in listelement[1:]:
                    if parent.nodeName != xmlelement: 
                        # element does not exists!!
                        break
                    parent = parent.parentNode
                else:
                    # element exists, extract the node from template 
                    # for cloning
                    parent = node.parentNode
                    self.parents.append(parent)
                    self.templates.append(parent.removeChild(node))
                    self.templatecounter = self.templatecounter + 1
                    break
            if oldcounter == self.templatecounter:
                raise exceptions.SXMLTemplateErrorRedo(element)


    def setRootInfo(self, data):
        """
        It sets up basic data for not "repeatable" nodes (root XML elements) of template.

        :Parameters:
            -`data`: dictionary with data for base nodes of template.
        """
        dictionary = self.TemplateDict(data)
        delete, lnodes = self._fillNodeTemplate(self.dom.documentElement, dictionary)


    def setData(self, data, lwhere=[]):
        """
        It sets up data for "repeatable" nodes of template.
        This function clones the "repeatable" nodes from template and fills it with data
        from the dictionary.

        :Parameters:
            -`data`: dictionary with data for new XML nodes.
            -`lwhere`: list of nodes which will be filled with data.
        """
        if not lwhere:
            lwhere = list(self.templates)
        dictionary = self.TemplateDict(data)
        for counter in xrange(0, self.templatecounter):
            if self.templates[counter] not in lwhere:
                continue
            newnode = self.templates[counter].cloneNode(True)
            delete, lnodes = self._fillNodeTemplate(newnode, dictionary)
            if not delete :
                self.parents[counter].appendChild(newnode)


    def getDom(self, template=False):
        """
        Get a DOM object.

        :Parameters:
            -`template`: "True" returns original template. "False" returns current XML with data.
        """
        if template:
            return self.templatedom
        else:
            return self.dom


    def _open(self, source):
        """
        URI, filename, or string --> stream

        This function lets you define parsers that take any input source (URL, pathname
        to local or network file, or actual data as a string) and deal with it in a 
        uniform manner.  Returned object is guaranteed to have all the basic stdio read 
        methods (read, readline, readlines). Just .close() the object when you are done 
        with it.
        """
        if hasattr(source, "read"):
            return source
        # try to open with urllib (if source is http, ftp, or file URL)
        try:
            import urllib
            return urllib.urlopen(source)
        except:
            pass
        # try to open with native open function (if source is pathname)
        try:
            return open(source, 'r')
        except (IOError, OSError):
            pass
        # treat source as string
        import StringIO
        return StringIO.StringIO(str(source))


    def _checkNodeTemplate(self):
        """
        It checks the template structure and "%(KEY|defaultvalue)s" format.
        """
        dictionary = self.TemplateDict()
        try:
            tmpdom = self.dom.documentElement.cloneNode(True)
            self._fillNodeTemplate(tmpdom, dictionary)
        except Exception as e:
            raise exceptions.SXMLTemplateErrorParse(_("Template format incorrect!, maybe you have to check it (%s).") % (e))


    def _fillNodeTemplate(self, node, dictionary):
        """
        It fills all gaps from XML Node (attributes, data, subnodes) with data from a dictionary.

        This is the main function for this class, it changes all keys for a node with the format 
        "%(key|defautlvalue)s" into the data of "key" from the dictionary, or "defaultvalue" 
        if key is not found in dictionary. This is a recursive method for all node childrens.
        """
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            if node.hasAttributes():
                for attribute in node.attributes.keys():
                    try:
                        value = node.getAttribute(attribute) % dictionary
                    except UserWarning:
                        node.removeAttribute(attribute)
                    else:
                        node.setAttribute(attribute, value)
        if node.hasChildNodes():
            delnodes = False
            lnodes = []
            remnodes = []
            for child in node.childNodes:
                delnode, lnode = self._fillNodeTemplate(child, dictionary)
                if delnode and lnode:
                    remnodes += lnode
                    delnodes = False
                    lnodes = []
                elif delnode:
                    lnodes.append(node)
                    delnodes = True
            for child in remnodes:
                node.removeChild(child)
            return delnodes, lnodes
        else:
            if node.nodeType == xml.dom.minidom.Node.TEXT_NODE \
                or node.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE \
                or node.nodeType == xml.dom.minidom.Node.COMMENT_NODE :
                try:
                    value = node.data % dictionary
                    node.data = value
                except UserWarning:
                    return True, []
                except:
                    pass
            return False, []


    def _delWhiteNodes(self, node):
        """
        It removes all of the whitespace-only text decendants of a DOM node.
    
        When creating a DOM from an XML source, XML parsers are required to consider 
        several conditions when deciding whether to include whitespace-only text 
        nodes. This function ignores all of those conditions and removes all 
        whitespace-only text decendants of the specified node. If the unlink flag is 
        specified, the removed text nodes are unlinked so that their storage can be 
        reclaimed. If the specified node is a whitespace-only text node then it is 
        left unmodified.
        """
        removelist = []
        for child in node.childNodes:
            if child.nodeType == xml.dom.minidom.Node.TEXT_NODE and not child.data.strip():
                removelist.append(child)
            elif child.hasChildNodes():
                self._delWhiteNodes(child)
        for node in removelist:
            node.parentNode.removeChild(node)
            node.unlink()


# EOF
