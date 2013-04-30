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
This program reads an Adobe Font Metrics (AFM) file and parses it into a
memory representation using the psg.afm.parser module. Tested on the font
matrics files for the 14 PDF standard fonts provided by Adobe at

   http://partners.adobe.com/public/developer/font/index.html
   
"""


#
# $Log: afm_parser_test.py,v $
# Revision 1.4  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.3  2006/08/18 22:58:50  t4w00-diedrich
# Use universion newline.
#
# Revision 1.2  2006/08/18 17:39:49  t4w00-diedrich
# Initial commit
#
# Revision 1.1.1.1  2006/08/16 20:58:54  t4w00-diedrich
# Initial import
#
#

import sys

from psg.fonts.afm_parser import parse_afm

def main(argv):
    filename = argv[1]
    fp = open(filename, "r")
    afm = parse_afm(fp)

    print afm.items()
    
    fp.close()

main(sys.argv)    


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
