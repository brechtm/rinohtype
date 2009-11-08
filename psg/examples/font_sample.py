#!/usr/bin/python
# -*- coding: utf-8 -*_-
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
# $Log: font_sample.py,v $
# Revision 1.2  2006/09/22 16:23:55  t4w00-diedrich
# Lines are printed in reverse the same order as in the source.
#
# Revision 1.1  2006/09/18 12:44:00  t4w00-diedrich
# Initial commitI
#
#
#

"""
This program creates a table containing a set of glyphs from the font
provided on the command line (as pfb/afm file pair) and create a
PostScript document on stdout. 
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


    cellpadding = mm(1)
    page_margin = mm(16)
    
    font_size = 10
    chars = u"""ABCDEFGHIJKLMNOPQRSTUVWXYZ
                abcdefghijklmnopqrstuvwxyz
                äöüÄÖÜß 0123456789
                !\"§$%&/()=?€@ „“ “” »«"""

    
    outline_file = open(sys.argv[1])
    metrics_file = open(sys.argv[2])

    # Load the font
    font = type1(outline_file, metrics_file)

    # Create the EPS document
    eps = eps_document(title=font.full_name)
    page = eps.page
    
    # Register the font with the document
    font_wrapper = page.register_font(font)

    # Ok, we got to find out a number of things: Dimensions of the cells,
    # dimensions of the table
    m = 0
    for char in chars:
        m = max(m, font.metrics.stringwidth(char, font_size))

    td_width = m + 2*cellpadding
    td_height = font_size + 2*cellpadding

    lines = map(strip, split(chars, "\n"))
    lines.reverse()

    m = 0
    for line in lines:
        m = max(m, len(line))

    cols = m
    rows = len(lines)

    table_width = cols * td_width
    table_height = rows * td_height

    # Create a canvas at the coordinates of the page_margins and width
    # the table's size.
    table = canvas(page, page_margin, page_margin, table_width, table_height,
                   border=True)

    # Draw the table grid by drawing row and column boundaries.
    print >> table, "gsave"
    print >> table, "0.4 setgray [] 0.5 setdash"
    for a in range(1, cols):
        print >> table, "newpath"
        print >> table, "%f %f moveto" % ( a * td_width, 0, )
        print >> table, "%f %f lineto" % ( a * td_width, table_height, )
        print >> table, "stroke"

    for a in range(1, rows):
        print >> table, "newpath"
        print >> table, "%f %f moveto" % ( 0, a * td_height, )
        print >> table, "%f %f lineto" % ( table_width, a * td_height, )
        print >> table, "stroke"
        
    print >> table, "grestore"

    print >> table, "/%s findfont" % font_wrapper.ps_name()
    print >> table, "%f scalefont" % font_size
    print >> table, "setfont"
    
    for lc, line in enumerate(lines):
        for cc, char in enumerate(line):
            x = cc * td_width + cellpadding
            y = lc * td_height + cellpadding
            psrep = font_wrapper.postscript_representation(char)
            
            print >> table, "%f %f moveto" % ( x, y, )
            print >> table, "(%s) show" % psrep

    page.append(table)

    page_bb = table.bounding_box()
    eps.header.bounding_box = page_bb.as_tuple()
    eps.header.hires_bounding_box = page_bb.as_tuple()

    eps.write_to(sys.stdout)
    
        

main()    
