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
# $Log: embed_eps.py,v $
# Revision 1.2  2006/09/18 09:05:35  t4w00-diedrich
# Get eps file to embed from the command line.
#
# Revision 1.1  2006/08/30 14:14:52  t4w00-diedrich
# Initial commit
#
#
#

"""
This program embeds an eps image into a DSC document.
"""

import sys

from psg.interpreters import gs as GS
from psg.document.dsc import dsc_document
from psg.util import *
from psg.drawing.box import canvas, eps_image


def main(argv):

    document = dsc_document("EPS Demo")
    page = document.page()
    canvas = page.canvas(margin=mm(18), border=True)

    eps = eps_image(canvas, open(sys.argv[1]),
                    border=True, document_level=True)
    page.append(eps)

    fp = open(sys.argv[1] + ".ps", "w")
    document.write_to(fp)
    fp.close()
        

    
    
main(sys.argv)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

