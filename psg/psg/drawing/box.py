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
# $Log: box.py,v $
# Revision 1.11  2006/12/10 22:51:54  diedrich
# Added class to import WMF files (untested so far).
#
# Revision 1.10  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.10  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.9  2006/09/22 17:07:30  t4w00-diedrich
# Typo.
#
# Revision 1.8  2006/09/22 16:27:17  t4w00-diedrich
# - Removed draw() from canvas
# - Set_font() will accept font and font_wrapper objects
#
# Revision 1.7  2006/09/18 09:11:47  t4w00-diedrich
# Added class raster_image which shares a lot of code with eps_image
# through the new _eps_image class.
#
# Revision 1.6  2006/09/11 13:54:52  t4w00-diedrich
# Justified text calculates line_width itself rather than relying on
# stringwidth() to calculate it.
#
# Revision 1.5  2006/08/30 14:17:06  t4w00-diedrich
# Along with numerous fixes and small improvements, added/implemented
# eps_image class.
#
# Revision 1.4  2006/08/30 03:56:11  t4w00-diedrich
# Wrote textbox class.
#
# Revision 1.3  2006/08/29 20:05:58  t4w00-diedrich
# The whole composition and parsing process of the DSC module has been
# changed. Things are a lot more simple now and work much more reliably.
# Documents are encoded in-memory, with imports performed 'lazily', that
# is, on writing. This is a good compromise between speed and memory usage.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1  2006/08/25 13:29:28  t4w00-diedrich
# Initial commit
#
#
#

"""
This module defines a number of very usefull classes to model a 'box'
on a page: canvas, textbox, eps_image and raster_image. Textbox
provides a simple multi-line text layout function.
"""

import sys
from uuid import uuid4 as uuid

from psg.document import document
from psg.exceptions import *
from psg.util import *
from psg import debug
from psg.fonts import font as font_cls

# For car and cdr refer to your favorite introduction to LISP. The
# Lisp Tutorial built in to your copy of Emacs makes a good start.
# I know this may not be everyone's taste in programming. But it's
# *so* elegant... ;-)

class box:
    """
    A box is a rectengular area on a page. It has a position on the
    page, a width, and a height. In other words: A bounding box. The
    box class provides a mechanism to store PostScript code: It
    maintinas lists called head, body and tail, which contain
    PostScript statements to draw the box's content. The PosrScript
    you use is arbitrary with one exceptions: code produced by the box
    is supposed to restore the PostScript graphic context to the same
    state it encountered it in. That's why it unconditionally push()es
    a gsave/grestore pair to its buffers.

    A box' coordinates and size are not mutable. They are accessible
    through the x(), y(), w() and h() method returning position, width
    and height respectively.

    The box class provides two alternative constructors: from_bounding_box
    and from_center.
    """
    def __init__(self, parent, x, y, w, h, border=False, clip=False):
        """
        Construct a box with lower left corner (x, y), with w and
        height h.

        @param parent: Either a page or a box object that contains this
           box.
        @param border: Boolean that determines whether the box will draw a
           hair line around its bounding box.
        @param clip: Boolean indicating whether the bounding box shall
           establish a clipping path around its bounding box.
        """
        if isinstance(parent, box):
            self.page = parent.page
            self.document = parent.page.document
        elif isinstance(parent, document.page):
            self.page = parent
            self.document = parent.document
        else:
            self.page = None
            self.document = parent

        self._w = float(w)
        self._h = float(h)
        self._x = float(x)
        self._y = float(y)
        self._border = border
        self._clip = clip

        self.head = file_like_buffer()
        self.body = file_like_buffer()
        self.tail = file_like_buffer()

        self.push("gsave", "grestore")

        if border:
            self.print_bounding_path()
            # Set color to black, line type to solid and width to 'hairline'
            print("0 setgray [] 0 setdash 0 setlinewidth", file=self.head)
            # Draw the line
            print("stroke", file=self.head)

        if clip:
            self.print_bounding_path()
            print("clip", file=self.head)


    def from_bounding_box(cls, parent, bb, border=False, clip=False):
        """
        Initialize a box from its bounding box.

        @param bb: The bounding box.
        @type bb: psg.util.bounding_box instance.
        """
        return cls(parent, bb.llx, bb.lly, bb.width(), bb.height(),
                   border, clip)
    from_bounding_box = classmethod(from_bounding_box)

    def from_center(cls, parent, x, y, w, h, border=False, clip=False):
        """
        For this constructor (x, y) is not the lower left corner of
        the box but its center.
        """
        return cls(parent, x - w/2.0, y - h/2.0, w, h, border, clip)
    from_center = classmethod(from_center)

    def x(self): return self._x
    def y(self): return self._y
    def w(self): return self._w
    def h(self): return self._h

    def bounding_box(self):
        """
        Return the box' bounding box as a util.bounding_box instance.
        """
        return bounding_box(self._x, self._y, self._x+self._w, self._y+self._h)

    def push(self, for_head, for_tail=None):
        """
        Append for_head to head and prepend(!) for_tail to tail. If
        for_head and for_tail do not end in whitespace, push() will
        append a Unix newline to them before adding them to the
        buffer.
        """
        if len(for_head) > 0 and for_head[-1] not in "\n\t\r ":
            for_head += "\n"

        self.head.append(for_head)

        if for_tail is not None:
            if len(for_tail) > 0 and for_tail[-1] not in "\n\t\r ":
                for_tail += "\n"

            self.tail.prepend(for_tail)

    def write(self, what):
        """
        Write to the box' body.
        """
        self.body.write(what)

    append = write

    def add_resource(self, resource, document_level=True):
        """
        Add a resource to the current document (document_level=True,
        the default) or page (document_level=False) using the page's
        add_resource function.
        """
        self.page.add_resource(resource, document_level)

    def write_to(self, fp):
        """
        Write the box' content to file pointer fp.
        """
        self.head.write_to(fp)
        self.body.write_to(fp)
        self.tail.write_to(fp)

    def print_bounding_path(self):
        # Set up a bounding box path
        print("newpath", file=self.head)
        print("%f %f moveto" % ( self.x(), self.y(), ), file=self.head)
        print("%f %f lineto" % ( self.x(), self.y() + self.h(), ), file=self.head)
        print("%f %f lineto" % ( self.x() + self.w(), self.y() + self.h(), ), file=self.head)
        print("%f %f lineto" % ( self.x() + self.w(), self.y(), ), file=self.head)
        print("closepath", file=self.head)

class canvas(box):
    """
    A canvas is a box to draw on. By now the only difference to a box
    is that it has its own coordinate system. PostScript's translate
    operator is used to relocate the canvas' origin to its lower left
    corner.
    """

    def __init__(self, parent, x, y, w, h, border=False, clip=False, **kw):
        box.__init__(self, parent, x, y, w, h, border, clip)

        # Move the origin to the lower left corner of the bounding box
        print("%f %f translate" % ( self.x(), self.y(), ), file=self.head)

class textbox(canvas):
    """
    A rectengular area on the page you can fill with paragraphs of
    text written in a single font.
    """
    def __init__(self, parent, x, y, w, h, border=False, clip=False, **kw):
        canvas.__init__(self, parent, x, y, w, h, border, clip)
        self._line_cursor = h
        self.set_font(None)

    def set_font(self, font, font_size=10, kerning=True,
                 alignment="left",
                 char_spacing=0.0, line_spacing=0, paragraph_spacing=0,
                 tab_stops=()):
        """
        @param font: A psg.font.font or psg.document.font_wrapper instance.
           If a font instance is provided, the font will be registered with
           this box' page and installed at document level
           (see page.register_font() for details).
        @param font_size: Font size in PostScript units. (default 10)
        @param kerning: Boolean indicating whether to make use of kerning
           information from the font metrics if available.
        @param alignment: String, one of 'left', 'right', 'center', 'justify'
        @param char_spacing: Space added between each pair of chars,
           in PostScript units
        @param line_specing: Space between two lines, in PostScript units.
           Line height = font_size + line_spacing.
        @param paragraph_spacing: Distance between two paragraphs.
        @param tab_stops: Collection of pairs as (distance, 'dir') with
           distance the distance from the last tab stop (there is always one on
           0.0) and 'dir' being one of 'l', 'r', 'c' meaning left, right,
           center, respectively. THIS IS NOT IMPLEMENTED, YET!!!
        """
        self.font_size = float(font_size)
        self.kerning = kerning
        assert alignment in ( "left", "right", "center", "justify", )
        self.alignment = alignment
        self.char_spacing = float(char_spacing)
        self.line_spacing = float(line_spacing)
        self.paragraph_spacing = float(paragraph_spacing)
        self.tab_stops = tab_stops

        if font is not None:
            if isinstance(font, font_cls):
                self.font_wrapper = self.page.register_font(font, True)

            elif isinstance(font, document.font_wrapper):
                self.font_wrapper = font

            else:
                raise TypeError("The font must be provided as a "
                                "psg.fonts.font or "
                                "psg.document.font_mapper instance.")

            print("/%s findfont" % self.font_wrapper.ps_name(), file=self)
            print("%f scalefont" % self.font_size, file=self)
            print("setfont", file=self)

            # Cursor
            try:
                if self.font_wrapper is not None: self.newline()
            except EndOfBox:
                raise BoxTooSmall("The box is smaller than the line height.")




    def typeset(self, text):
        r"""
        Typeset the text into the text_box. The text must be provided
        as a Unicode(!) string. Paragraphs are delimited by Unix
        newlines (\n), otherwise any white space is treated as a
        single space (like in HTML or TeX). The function will return
        any text that did not fit the box as a (normalized) Unicode
        string. No hyphanation will be performed.
        """
        if type(text) != str:
            raise TypeError("typeset() only works on unicode strings!")

        if self.font_wrapper is None:
            raise IllegalFunctionCall("You must call set_font() before "
                                      "typesetting any text.")

        paragraphs = text.split("\n")
        paragraphs = filter(lambda a: a.strip() != "", paragraphs)
        paragraphs = [par.split() for par in paragraphs]
        # Paragraphs is now a list of lists containing words (Unicode strings).

        space_width = self.font_wrapper.font.metrics.stringwidth(
            " ", self.font_size)

        try:
            paragraph = []
            while(paragraphs):
                paragraph = car(paragraphs)
                paragraphs = cdr(paragraphs)

                line = []
                line_width = 0
                while(paragraph):
                    word = car(paragraph)

                    word_width = self.font_wrapper.font.metrics.stringwidth(
                        word, self.font_size, self.kerning, self.char_spacing)

                    if line_width + word_width > self.w():
                        self.typeset_line(line)
                        self.newline()
                        line = []
                        line_width = 0
                    else:
                        line.append( (word, word_width,) )
                        line_width += word_width + space_width
                        paragraph = cdr(paragraph)

                if len(line) != 0:
                    self.typeset_line(line, True)
                    self.newline()

                self.advance(self.paragraph_spacing)

        except EndOfBox:
            paragraphs.insert(0, paragraph)
            paragraphs = map(lambda l: " ".join(l), paragraphs)
            paragraphs = filter(lambda a: a != "", paragraphs)
            paragraphs = "\n".join(paragraphs)
            return paragraphs

        return ""

    def typeset_line(self, words, last_line=False):
        """
        Typeset words on the current coordinates. Words is a list of pairs
        as ( 'word', width, ).
        """
        if debug.debug.verbose:
            print("gsave", file=self)
            print("newpath", file=self)
            print("0 %f moveto" % self._line_cursor, file=self)
            print("%f %f lineto" % ( self.w(), self._line_cursor, ), file=self)
            print("0.33 setgray", file=self)
            print("[5 5] 0 setdash", file=self)
            print("stroke", file=self)
            print("grestore", file=self)

        chars = []
        char_widths = []

        font_metrics = self.font_wrapper.font.metrics
        word_count = len(words)

        while(words):
            word, word_width = car(words)
            words = cdr(words)

            for idx in range(len(word)):
                char = ord(word[idx])

                if self.kerning:
                    try:
                        next = ord(word[idx+1])
                    except IndexError:
                        next = 0

                    kerning = font_metrics.get_kerning(char, next)
                    kerning = kerning * self.font_size / 1000.0
                else:
                    kerning = 0.0

                if idx == len(word) - 1:
                    spacing = 0.0
                else:
                    spacing = self.char_spacing

                char_width = (font_metrics.stringwidth(chr(char),
                                                       self.font_size)
                              + kerning + spacing)

                chars.append(char)
                char_widths.append(char_width)

            # The space between...
            if words: # if it's not the last one...
                chars.append(32) # space
                char_widths.append(None)

        line_width = sum(filter(lambda a: a is not None, char_widths))

        if self.alignment in ("left", "center", "right",) or \
               (self.alignment == "justify" and last_line):
            space_width = self.font_wrapper.font.metrics.stringwidth(
                " ", self.font_size)
        else:
            space_width = (self.w() - line_width) / float(word_count-1)


        n = []
        for a in char_widths:
            if a is None:
                n.append(space_width)
            else:
                n.append(a)
        char_widths = n

        # Horizontal displacement
        if self.alignment in ("left", "justify",):
            x = 0.0
        elif self.alignment == "center":
            line_width = sum(char_widths)
            x = (self.w() - line_width) / 2.0
        elif self.alignment == "right":
            line_width = sum(char_widths)
            x = self.w() - line_width

        # Position PostScript's cursor
        print("%f %f moveto" % ( x, self._line_cursor, ), file=self)

        char_widths = map(lambda f: "%.2f" % f, char_widths)
        tpl = ( self.font_wrapper.postscript_representation(chars),
                    " ".join(char_widths), )
        print("(%s) [ %s ] xshow" % tpl, file=self)

    def newline(self):
        """
        Move the cursor downwards one line. In debug mode (psg.debug.debug
        is set to verbose) this function will draw a thin gray line below
        every line. (No PostScript is generated by this function!)
        """
        self.advance(self.line_height())

    def line_height(self):
        """
        Return the height of one line (font_size + line_spacing)
        """
        return self.font_size + self.line_spacing

    def advance(self, space):
        """
        Advance the line cursor downward by space. (No PostScript is
        generated by this function, it only updates an internal
        value!)
        """
        self._line_cursor -= space

        if self._line_cursor < 0:
            raise EndOfBox()

    def text_height(self):
        if self._line_cursor < 0:
            l = 0
        else:
            l = self._line_cursor

        return self.h() - l




class _eps_image(box):
    """
    This is the base class for eps_image and raster_image below, which
    both embed external images into the target document as a Document
    section.
    """
    def __init__(self, parent, subfile, bb, document_level, border, clip):
        box.__init__(self, parent, bb.llx, bb.lly, bb.width(), bb.height(),
                     border, clip)

        if document_level:
            # If the EPS file is supposed to live at document level,
            # we create a file resource in its prolog.

            # The mechanism was written and excellently explained by
            # Thomas D. Greer at http://www.tgreer.com/eps_vdp2.html .
            identifyer = "psg_eps_file*%i" % self.document.embed_counter()
            file_resource = self.document.file_resource(str(uuid())+".eps")
            print("/%sImageData currentfile" % identifyer, file=file_resource)
            print("<< /Filter /SubFileDecode", file=file_resource)
            print("   /DecodeParms << /EODCount", file=file_resource)
            print("       0 /EODString (***EOD***) >>", file=file_resource)
            print(">> /ReusableStreamDecode filter", file=file_resource)
            file_resource.append(subfile)
            print("***EOD***", file=file_resource)
            print("def", file=file_resource)

            print("/%s " % identifyer, file=file_resource)
            print("<< /FormType 1", file=file_resource)
            print("   /BBox [%f %f %f %f]" % bb.as_tuple(), file=file_resource)
            print("   /Matrix [ 1 0 0 1 0 0]", file=file_resource)
            print("   /PaintProc", file=file_resource)
            print("   { pop", file=file_resource)
            print("       /ostate save def", file=file_resource)
            print("         /showpage {} def", file=file_resource)
            print("         /setpagedevice /pop load def", file=file_resource)
            print("         %sImageData 0 setfileposition"%\
                                                                     identifyer, file=file_resource)
            print("            %sImageData cvx exec"%\
                                                                     identifyer, file=file_resource)
            print("       ostate restore", file=file_resource)
            print("   } bind", file=file_resource)
            print(">> def", file=file_resource)

            # Store the ps code to use the eps file in self
            print("%s execform" % identifyer, file=self)
        else:
            from psg import procsets
            self.add_resource(procsets.dsc_eps)
            print("psg_begin_epsf", file=self)
            print("%%BeginDocument", file=self)
            self.append(subfile)
            print(file=self)
            print("%%EndDocument", file=self)
            print("psg_end_epsf", file=self)


class eps_image(_eps_image):
    """
    Include a EPS complient PostScript document into the target
    PostScript file.
    """
    def __init__(self, parent, fp, document_level=False,
                 border=False, clip=False):
        """
        @param fp: File pointer opened for reading of the EPS file to be
           included
        @param document_level: Boolean indicating whether the EPS file shall
           be part of the document prolog and be referenced several times from
           within the document or if it shall be included where it is used
           for a single usage.
        """

        if isinstance(parent, document.document):
            document_level = True

        # Skip forward in the input file seeking for the %PS.
        # This is in case the file starts with garbage.
        lines = line_iterator(fp)
        line = ""
        for line in lines:
            if "%!PS" in line:
                break

        lines.rewind()

        begin = lines.fp.tell()
        bb = None
        hrbb = None
        for line in lines:
            if line.startswith("%%BoundingBox:"):
                bb = line
            elif line.startswith("%%HiResBoundingBox:"):
                hrbb = line
            elif line.startswith("%%EndComments"):
                break

        if hrbb is not None: bb = hrbb

        if bb is None:
            raise Exception("Not a valid EPS file (no bounding box!)")

        parts = bb.split(":")
        numbers = parts[1]
        bb = bounding_box.from_string(numbers)

        fp.seek(0, 2)
        length = fp.tell()

        fp = subfile(fp, begin, length-begin)

        _eps_image.__init__(self, parent, fp, bb, document_level,
                            border, clip)


class raster_image(_eps_image):
    """
    This class creates a box from a raster image. Any image format
    supported by the Python Image Library is supported. The class uses
    PIL's EPS writer to create a PostScript representation of the
    image, which is much easier to program and much faster than
    anything I could have come up with, and uses PIL's output with the
    _eps_image class above. Of course, as any other part of psg, this
    is a lazy peration. When opening an image with it, PIL only reads
    the image header to determine its size and color depth. Conversion
    of the image takes place on writing.
    """
    class raster_image_buffer:
        def __init__(self, pil_image):
            self.pil_image = pil_image

        def write_to(self, fp):
            self.pil_image.save(fp, "EPS")

    def __init__(self, parent, pil_image, document_level=False,
                 border=False, clip=False):
        """
        @param pil_image: Instance of PIL's image class
        @param document_level: Boolean indicating whether the EPS file shall
           be part of the document prolog and be referenced several times from
           within the document or if it shall be included where it is used
           for a single usage.
        """
        width, height = pil_image.size
        bb = bounding_box(0, 0, width, height)

        fp = self.raster_image_buffer(pil_image)

        _eps_image.__init__(self, parent, fp, bb, document_level, border, clip)

class wmf_file(_eps_image):
    """
    This class creates a box from a Windows Meta File.
    """
    def __init__(self, parent, wmf_fp, document_level=False,
                 border=False, clip=False):

        eps = wmf2eps(wmf_fp)

        bb = eps.bounding_box
        bb = bounding_box.from_tuple(bb)

        _eps_image.__init__(self, parent, eps, bb, document_level,
                            border, clip)



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

