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
# $Log: raster_image.py,v $
# Revision 1.1  2006/09/18 09:06:55  t4w00-diedrich
# Initial commit
#
# Revision 1.1  2006/08/30 14:14:52  t4w00-diedrich
# Initial commit
#
#
#

"""
This program embeds a PIL loadable raster image into a DSC document.
"""

import sys

from psg.interpreters import gs as GS
from psg.document.dsc import dsc_document
from psg.util import *
from psg.drawing.box import canvas, raster_image

from PIL import Image

def main(argv):
    img = Image.open(argv[1])
    
    document = dsc_document("Raster Image Demo")
    page = document.page()
    canvas = page.canvas(margin=mm(18), border=True)

    eps = raster_image(canvas, img, document_level=False,
                       border=True)
    page.append(eps)

    fp = open(sys.argv[1] + ".ps", "w")
    document.write_to(fp)
    fp.close()
        

    
    
main(sys.argv)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

