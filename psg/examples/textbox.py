#!/usr/bin/python
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
# $Log: textbox.py,v $
# Revision 1.1  2006/08/30 14:14:52  t4w00-diedrich
# Initial commit
#
#
#

"""
This program uses psg.drawing.textbox to typeset text.
"""

import sys

from psg.interpreters import gs as GS
from psg.document.dsc import dsc_document
from psg.util import *
from psg.drawing.box import box, textbox
from psg.fonts.type1 import type1

from psg import debug
debug.debug.verbose = True

from texts import *

def box0(gs, box, tr, **kw):
    box.set_font(tr, font_size=11, paragraph_spacing=5.5)
    box.typeset(two_paragraphs)

def box1(gs, box, tr, **kw):
    box.set_font(tr, font_size=11, paragraph_spacing=5.5,
                     alignment="justify", kerning=True)
    box.typeset(two_paragraphs)

def box2(gs, box, tr, **kw):
    box.set_font(tr, font_size=11, paragraph_spacing=5.5,
                     alignment="right", kerning=True)
    box.typeset(two_paragraphs)

def box3(gs, box, tr, **kw):
    box.set_font(tr, font_size=11, paragraph_spacing=5.5,
                     alignment="center", kerning=True)
    box.typeset(two_paragraphs)

def box4(gs, box, al, **kw):
    box.set_font(al, font_size=11, paragraph_spacing=5.5,
                     alignment="justify", kerning=True)
    box.typeset(two_paragraphs_greek)

def box5(gs, box, tr, **kw):
    box.set_font(tr, font_size=11, paragraph_spacing=5.5,
                     alignment="left", kerning=True)
    box.typeset(special_characters)

def box6(gs, box, ba, **kw):
    box.set_font(ba, font_size=11, paragraph_spacing=5.5,
                     alignment="left", kerning=True)
    box.typeset(two_paragraphs)

def box7(gs, box, he, **kw):
    box.set_font(he, font_size=10, paragraph_spacing=5.5,
                 line_spacing=2, alignment="left", kerning=True)
    box.typeset(two_paragraphs)

def main(argv):
    gs = GS()

    document = dsc_document("My first textbox example and testbed")
    page = document.page()
    canvas = page.canvas(margin=mm(18), border=False)

    tr = gs.font("Times-Roman")
    tr = page.register_font(tr)

    he = gs.font("Helvetica")
    he = page.register_font(he)

    al = type1("Kerkis.pfa", "Kerkis.afm")
    al = page.register_font(al)

    ba = type1("BlackadderITC-Regular.pfa", "BlackadderITC-Regular.afm")
    ba = page.register_font(ba)
    
    for counter, bb in enumerate(eight_squares(canvas)):        
        func = globals().get("box%i" % counter, None)
        
        if func is None:
            break
        else:
            box = textbox.from_bounding_box(canvas, bb, border=True)
            canvas.append(box)
            func(**locals())

    fp = open(sys.argv[0] + ".ps", "w")
    document.write_to(fp)
    fp.close()
        

    
    
main(sys.argv)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

