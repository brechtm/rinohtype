##!/usr/bin/python
# -*- coding: utf-8 -*-
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
# $Log: kerning.py,v $
# Revision 1.2  2006/11/04 18:20:11  diedrich
# Fixed encoding
#
# Revision 1.1  2006/08/29 20:03:57  t4w00-diedrich
# Experiments using xshow for text output.
#
# Revision 1.1  2006/08/25 13:29:28  t4w00-diedrich
# Initial commit
#
#
#

"""
This program does kerning by hand. 
"""

import sys

from psg.interpreters import gs as GS
from psg.document.dsc import dsc_document
from psg.util import *
from psg.drawing.box import canvas

class canvas_with_lines(canvas):
    def __init__(self, c, line_height):
        canvas.__init__(self, c.page,
                        c._x, c._y, c._w, c._h,
                        c._border, c._clip)
        self.head = c.head
        self.body = c.body
        self.tail = c.tail

        self.line_height = line_height
        self._line_cursor = self.h()
        self.newline()
        

    def newline(self):
        self._line_cursor -= self.line_height
        
        if self._border:
            print >> self, "gsave"
            print >> self, "newpath"
            print >> self, "0 %f moveto" % self._line_cursor
            print >> self, "%f %f lineto" % ( self.w(), self._line_cursor, )
            print >> self, "[5 5] 0 setdash"
            print >> self, "stroke"
            print >> self, "grestore"
            
        print >> self, "0 %f moveto" % self._line_cursor


def glyph_iterator(font_wrapper, font_size, message):
    font = font_wrapper.font
    message = map(ord, message)
    cpy = message[1:] + [0]
    for char, next in zip(message, cpy):
        glyph_matrics = font.metrics.get(char, None)
        if glyph_matrics is None:
            yield 0
        else:
            metrics = font.metrics[char]
            kerning = font.metrics.kerning_pairs.get( ( char, next, ), 0.0 )

            x_offset = glyph_matrics.width + kerning
            x_offset = x_offset * font_size / 1000

            yield x_offset

def main(argv):
    gs = GS()

    sans = gs.font("FeGWitten-Bold")

    # for u, g in sans.metrics.items():
    #     print u, g.ps_name

    document = dsc_document("Hello, world!")
    page = document.page()
    canvas = page.canvas(margin=mm(18), border=True)
    canvas = canvas_with_lines(canvas, 30.0)

    # The regular say
    print >> canvas, "/%s findfont" % sans.ps_name
    print >> canvas, "20 scalefont"
    print >> canvas, "setfont"
    print >> canvas, ps_escape("Hello, world! (no Kerning at all)"), " show"
    canvas.newline()


    # Kerned say

    message = u"Hello, world! (Pair-wise Kerning on!) €  äöüÄÖÜß" # äöüÄÖÜß

    offsets = []

    sans_wrapper = page.register_font(sans)
    print >> canvas, "/%s findfont" % sans_wrapper.ps_name()
    print >> canvas, "20 scalefont"
    print >> canvas, "setfont"

    for kerning_delta in glyph_iterator(sans_wrapper, 20, message):
        offsets.append(kerning_delta)

    offsets = map(str, offsets)
    tpl = ( sans_wrapper.postscript_representation(message),
            join(offsets, " "), )
    print >> canvas, "(%s) [ %s ] xshow" % tpl

    fp = open("kerning.ps", "w")
    document.write_to(fp)
    fp.close()
        

    
    
main(sys.argv)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

