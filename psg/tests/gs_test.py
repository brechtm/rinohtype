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

"""
This program creates an psg.interpreter.gs instance thereby parsing gs's
Fontmap and reading the .afm files for all available Type1 fonts.
"""


#
# $Log: gs_test.py,v $
# Revision 1.1.1.1  2006/08/16 20:58:54  t4w00-diedrich
# Initial import
#
#

import sys

from psg.interpreters import gs as GS

def main(argv):
    gs = GS()
    ff = gs.font_family("Helvetica")
    print ff
    print ff.regular.full_name
    print ff.italic.full_name
    print ff.bold.full_name
    print ff.bolditalic.full_name
    print
    print ff.fonts()

main(sys.argv)    


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
