#!/usr/bin/python
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log: document.py,v $
# Revision 1.13  2006/11/15 21:51:11  diedrich
# Added stuff for custom_color management, not quite done, yet. Also
# fixed error message in python_representation()
#
# Revision 1.12  2006/10/29 13:01:54  diedrich
# Document.canvas() does not self.append() its return value any more.
#
# Revision 1.11  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.11  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.10  2006/09/22 17:23:25  t4w00-diedrich
# Page.canvas() appends the new canvas to the page.
#
# Revision 1.9  2006/09/22 16:26:05  t4w00-diedrich
# - Removed _boxes from page
# - Added cache for font_wrappers
# - Multiple calls to register_font() for the same font will be ignored now.
#
# Revision 1.8  2006/09/11 13:49:10  t4w00-diedrich
# Octal code escape sequences in PS strings are always three digit now.
#
# Revision 1.7  2006/08/30 14:15:54  t4w00-diedrich
# Fixed canvas' constructor (margin handling)
#
# Revision 1.6  2006/08/30 03:55:15  t4w00-diedrich
# Register_chars() and postscript_representation() accept lists of
# integers as well as strings as arguments.
#
# Revision 1.5  2006/08/29 20:05:58  t4w00-diedrich
# The whole composition and parsing process of the DSC module has been
# changed. Things are a lot more simple now and work much more reliably.
# Documents are encoded in-memory, with imports performed 'lazily', that
# is, on writing. This is a good compromise between speed and memory usage.
#
# Revision 1.4  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.3  2006/08/25 13:33:15  t4w00-diedrich
# - Some definitions have changed. The classes from document.py are more
#   usefull now, providing higher level classes for dsc.py
# - These changes are reflected all over the place, escpecially in psgmerge.
#
# Revision 1.2  2006/08/19 15:41:59  t4w00-diedrich
# Moved utility function and -classes to util submodule.
#
# Revision 1.1  2006/08/18 17:39:49  t4w00-diedrich
# Initial commit
#
#

"""
This module defines a base class for documents and a number of utility
classes.
"""

import sys, os, warnings

from psg.exceptions import *
from psg.util import *
from psg.fonts.encoding_tables import *


class resource:
    """
    A resource. Subclassed by dsc.resource.
    """
    def __init__(self, type, name, version):
        self.type = type
        self.name = name
        self.version = version

    def __equal__(self, other):
        """
        Two resources are condidered equal when their type and names
        (including version) match exactly.
        """
        if self.type == other.type and \
               strip(self.name) == strip(other.name):
            return True
        else:
            return False

    def __repr__(self):
        return "<resource %s %s vers: %s>" % ( self.type,
                                               self.name,
                                               self.version, )


class resource_set(ordered_set):
    def append(self, value):
        if not isinstance(value, resource):
            raise TypeError("A resource_set may only contain "
                            "resource instances, not " + repr(type(resource)))

        for index, a in enumerate(self):
            if a.type == "procset" and \
                   a.procset_name == value.procset_name and \
                   a.version <= value.version:
                self[index] = value
                return
            else:
                if value == a: return


        ordered_set.append(self, value)

    add = append

    def insert(self, *args):
        raise NotImplementedError()


    def union(self, other):
        ret = self.__class__()
        for a in self: ret.add(a)
        for a in other: ret.add(a)
        return ret


# The document class


class document:
    """
    Base class for all document classes.
    """
    def __init__(self, title=None):
        if title is not None: self.title = title
        self._resources = resource_set()
        self._custom_colors = []
        self._required_resources = resource_set()
        self._page_counter = 0

    def add_resource(self, resource):
        self._resources.append(resource)

    def resources(self):
        return self._resources

    def add_required_resource(self, resource):
        self._required_resources.append(resource)

    def page(self, page_size="a4", label=None):
        """
        Return a page object suitable for and connected to this document.
        """
        return page(self, page_size, label)

    def _page__inc_page_counter(self):
        self._page_counter += 1

    def page_counter(self):
        return self._page_counter

    def output_file(self):
        """
        Return a file pointer in write mode for the pages to write their
        output to.
        """
        raise NotImplementedError()

    class custom_color:
        def __init__(self, _document, name, colspec):
            """
            @param name: String indicating the name of the color.
            @param colspec: Tuple of Float values either of length 1
                (Gray), 3 (RGB) or 4 (CMYK)
            """
            self._document = _document
            self.name = name

            try:
                colspec = map(float, colspec)
                if len(colspec) not in (1, 3, 4,):
                    raise ValueError
                else:
                    self.colspec = colspec
            except ValueError:
                raise ValueError("Color specification must be 1, 3 or 4 "
                                 "floats in a tuple.")


        def __str__(self):
            """
            Return a representation of this custom color in a
            document. The default implementation raises
            NotImplementedError()
            """
            raise NotImplementedError()

    def register_custom_color(self, name, colspec):
        """
        Pass the params to the constructor of the custom_color class
        above and return it. The custom colors will be kept treck of
        in the self._custom_colors list.

        @param name: String indicating the name of the color.
        @param colspec: Tuple of Float values either of length 1 (Gray),
            3 (RGB) or 4 (CMYK)
        """
        ret = self.custom_color(self, name, colspec)
        self._custom_colors.append(ret)
        return ret


class font_wrapper:
    """
    A font wrapper keeps track of which glyphs in a font have been
    used on a specific page. This information is then used to
    construct an encoding vector mapping 8bit values to glyphs. This
    imposes a limit: You can only use 255 distinct characters from any
    given font on a single page.
    """
    def __init__(self, page, ordinal, font, document_level):
        self.page = page
        self.ordinal = ordinal
        self.font = font

        self.mapping = {}
        for a in range(32, 127):
            glyph_name = self.font.metrics[a].ps_name
            self.mapping[glyph_name] = a
        self.next = 127

    def register_chars(self, us, ignore_missing=True):
        if type(us) not in (str, list):
            raise TypeError("Please use unicode strings!")
        else:
            if type(us) == str:
                chars = map(ord, us)
            else:
                chars = us

            for char in chars:
                if not self.font.has_char(char):
                    if ignore_missing:
                        if char in unicode_to_glyph_name:
                            tpl = (self.font.ps_name,
                                   "%s (%s)" % (unicode_to_glyph_name[char][-1],
                                                chr(char)))
                        else:
                            try:
                                tpl = (self.font.ps_name, "#%i" % char)
                            except TypeError:
                                tpl = (self.font.ps_name, "'%s'" % char)

                        msg = "%s does not contain needed glyph %s" % tpl
                        warnings.warn(msg)
                        char = 32 # space
                    else:
                        tpl = (char, repr(chr(char)))
                        msg = "No glyph for unicode char %i (%s)" % tpl
                        raise KeyError(msg)

                try:
                    glyph_name = self.font.metrics[char].ps_name
                except KeyError:
                    glyph_name = char

                if glyph_name not in self.mapping:
                    self.next += 1

                    if self.next > 254:
                        # Use the first 31 chars (except \000) last.
                        self.next = -1
                        for b in range(1, 32):
                            if b not in self.mapping.values():
                                self.next = b

                        if next == -1:
                            # If these are exhausted as well, replace
                            # the char by the space character
                            next = 32
                            msg = "character mapping spots are full!"
                            warnings.warn(msg)
                        else:
                            next = self.next
                    else:
                        next = self.next

                    self.mapping[glyph_name] = next

    def postscript_representation(self, us):
        """
        Return a regular 8bit string in this particular encoding
        representing unicode string 'us'. 'us' may also be a list of
        integer unicode char numbers. This function will register all
        characters in us with this page.
        """
        if type(us) not in (str, list):
            raise TypeError("Please use unicode strings!")
        else:
            self.register_chars(us)
            ret = []

            if type(us) == list:
                chars = us
            else:
                chars = map(ord, us)

            for char in chars:
                if type(char) == int:
                    try:
                        glyph_name = self.font.metrics[char].ps_name
                    except KeyError:
                        glyph_name = unicode_to_glyph_name[char][-1]
                else:
                    glyph_name = char
                byte = self.mapping.get(glyph_name, None)
                if byte is None:
                    byte = " "
                else:
                    if byte < 32 or byte > 240 or byte in (40,41,92,):
                        byte = "\%03o" % byte
                    else:
                        byte = chr(byte)

                ret.append(byte)

            return "".join(ret)

    def setup_lines(self):
        """
        Return the PostScript code that goes into the page's setup
        section.
        """
        # turn the mapping around
        mapping = dict(map(lambda tpl: ( tpl[1], tpl[0], ),
                           self.mapping.items()))

        nodefs = 0
        encoding_vector = []
        for a in range(256):
            if a in mapping:
                if nodefs == 1:
                    encoding_vector.append("/.nodef")
                    nodefs = 0
                elif nodefs > 1:
                    encoding_vector.append("%i{/.nodef}repeat" % nodefs)
                    nodefs = 0
                encoding_vector.append("/%s" % mapping[a])
            else:
                nodefs += 1

        if nodefs != 0:
            encoding_vector.append("%i{/.nodef}repeat" % nodefs)

        tpl = ( self.ps_name(), join80(encoding_vector), self.font.ps_name, )
        return "/%s [%s]\n /%s findfont " % tpl + \
               "psg_reencode 2 copy definefont pop def\n"

    __str__ = setup_lines

    def ps_name(self):
        """
        Return the name of the re-encoded font for this page.
        """
        return "%s*%i" % ( self.font.ps_name, self.ordinal, )

class page:
    """
    Model a page in a document.

    @ivar setup: File-like buffer to hold page initialisation code.
    @ivar _font_wrappers: Mapping of PostScript font names to font_wrapper
       instances for all the fonts registered with this page
    """

    def __init__(self, document, page_size="a4", label=None):
        """
        Model a page in a document. A page knows about its resources,
        either on page or on document level.

        @param document: A psg.document instance.
        @param page_size: Either a string key for the PAPERSIZES dict
           above a pair of numerical values indicating the page's size
           in pt. Defaults to 'a4'. Note that opposed to the dict, the order
           of the tuple's elements is (width, height)
        @param label: A string label for this page (goes into the %%Page
           comment, defaults to a string representation of the page's ordinal,
           that is its one-based index within the document.)
        @raises KeyError: if the page_size is not known.
        """
        self.document = document

        if type(page_size) == tuple:
            self._w, self._h = page_size
        else:
            self._w, self._h = PAPERSIZES[page_size]

        self.label = label

        self._resources = resource_set()

        document.__inc_page_counter()

        self._number_of_fonts = 0
        self._font_wrappers = {}

    def w(self): return self._w
    def h(self): return self._h

    def add_resource(self, resource, document_level=True):
        """
        Add a resource to this page or to this page's document (the default).
        """
        if document_level:
            self.document.add_resource(resource)
        else:
            self._resources.append(resource)

    def resources(self):
        return self._resources

    def canvas(self, margin=0, border=False, clip=False):
        """
        Return a canvas object for the whole page except a predefined
        set of margins.

        The margin parameter may be either:

          - an integer - all four margins the same
          - a pair - ( horizontal, vertical, )
          - a 4-tuple - ( left, top, right, bottom, )

        """

        if type(margin) == tuple:
            if len(margin) == 2:
                h, v = margin
                margin = ( h, v, h, v, )
        else:
            m = float(margin)
            margin = ( m, m, m, m, )

        l, t, r, b = margin

        from psg.drawing.box import canvas
        ret = canvas(self, l, b,
                     self.w() - r - l, self.h() - t - b,
                     border, clip)

        return ret

    def register_font(self, font, document_level=True):
        """
        This function will register a font with this page and return a
        font_wrapper object, see above. The boolean document_level
        parameter determines whether the font will be a document
        resource or a page resource.

        The page will keep track which fonts have been registered with
        it and cache wrapper objects. The document_level parameter is
        only meaningfull for the first call to register_font() with
        any given font. Fonts are keyed by their PostScript name, not
        the font objects.
        """
        if font.ps_name not in self._font_wrappers:
            number_of_fonts = len(self._font_wrappers)
            wrapper = font_wrapper(self, number_of_fonts,
                                   font, document_level)
            self.pagesetup.append(wrapper)
            self._font_wrappers[font.ps_name] = wrapper

        return self._font_wrappers[font.ps_name]




# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

