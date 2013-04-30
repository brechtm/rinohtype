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
#
#

import sys
from cStringIO import StringIO

from psg.document.document import subfile

def main(argv):
    parent = open("subfile_test.py")

    s1 = subfile(StringIO(parent.read()), 18, 977)
    #s1.readline()

    s1.seek(4, 1)
    # s1.seek(4, 1)
    
    # From the second line up last line of the GPL header, without "gpl.txt"

    result = s1.read()
    print result
    print
    print len(result)
    
main(sys.argv)    


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
