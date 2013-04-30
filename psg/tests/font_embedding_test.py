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
# $Log: font_embedding_test.py,v $
# Revision 1.1  2006/09/08 12:55:38  t4w00-diedrich
# Initial commit
#
#
#

"""
Print the full name of a font into an EPS file. You'll need to supply
an outline and a metrics file on the command line. The resulting ps
will be written to stdout.
"""

import sys
from psg.document.dsc import eps_document
from psg.drawing.box import *
from psg.fonts.type1 import type1
from psg.util import *

def main():
    if len(sys.argv) < 3:
        print "Usage: %s <outline file> <metrics file>" % sys.argv[0]
        sys.exit(-1)


    margin = mm(3)
    font_size = 20
    
    outline_file = open(sys.argv[1])
    metrics_file = open(sys.argv[2])

    # Load the font
    font = type1(outline_file, metrics_file)

    # The text to be set
    # text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text = font.full_name

    # Create the EPS document
    eps = eps_document(title=font.full_name)
    page = eps.page
    
    # Register the font with the document
    font_wrapper = page.register_font(font)
    
    # The actual string sits in its own textbox

    # width = the width of the string
    width = font.metrics.stringwidth(text, font_size)
    
    tb = textbox(page, margin, margin, width, font_size)
    tb.set_font(font_wrapper, font_size)
    tb.typeset(unicode(text, "iso-8859-1"))

    page.append(tb)
    
    # Page height = the height of the largest character (=font bbox height).
    fontbb = font.metrics.font_bounding_box()
    page_height = fontbb.ury * float(font_size) # scale to font size, too
    page_bb = bounding_box(0, 0, tb.w() + 2*margin, page_height + 2*margin)
    eps.header.bounding_box = page_bb.as_tuple()
    eps.header.hires_bounding_box = page_bb.as_tuple()

    eps.write_to(sys.stdout)

main()    



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

