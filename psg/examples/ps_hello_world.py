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
# $Log: ps_hello_world.py,v $
# Revision 1.3  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.3  2006/10/14 22:24:59  t4w00-diedrich
# Removed write_to_document()
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
psg printing the old line on a sheet of paper. The text drawing
functions are not written, yet, so I type in the PostScript directly.
"""

import sys

from psg.document.dsc import dsc_document
from psg.util import *

def main():

    document = dsc_document("Hello, world!")
    page = document.page()
    canvas = page.canvas(margin=mm(18))

    print("/Helvetica findfont", file=canvas)
    print("20 scalefont", file=canvas)
    print( "setfont", file=canvas)
    print("0 0 moveto", file=canvas)
    print(ps_escape("Hello, world!"), " show", file=canvas)

    fp = open("ps_hello_world.ps", "w")
    document.write_to(fp)
    fp.close()

main()


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

