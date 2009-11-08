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
# $Log: type1.py,v $
# Revision 1.3  2006/09/06 23:23:45  t4w00-diedrich
# type1.__init__() accepts both, file pointers and file names as arguments.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1.1.1  2006/08/16 20:58:53  t4w00-diedrich
# Initial import
#
#


"""
This module contains code to handle PostScript Type1 fonts.
"""
from .font import font
from .afm_metrics import afm_metrics

class type1(font):
    """
    Model a PostScript Type1 font.

    @ivar charmap: Dictionary with unicode character codes as keys and
      the coresponding char (glyph) code as values.
    """
    def __init__(self, main_font_file, afm_file):
        """
        @param main_font: Filepointer of a .pfa/b file. This may be
           None for resident fonts.
        @param afm_file: File pointer of the corresponding .afm file
        """
        if type(main_font_file) == str:
            main_font_file = open(main_font_file, 'rb')

        if type(afm_file) == str:
            afm_file = open(afm_file, 'rb')

        self._main_font_file = main_font_file
        self._afm_file = afm_file

        metrics = afm_metrics(afm_file)

        font.__init__(self,
                      metrics.ps_name,
                      metrics.full_name,
                      metrics.family_name,
                      metrics.weight,
                      metrics.italic,
                      metrics.fixed_width,
                      metrics)

    def has_char(self, unicode_char_code):
        return unicode_char_code in self.metrics


    def main_font_file(self):
        return self._main_font_file

    def afm_file(self):
        return self._afm_file



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

