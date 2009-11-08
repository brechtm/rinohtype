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
# $Log: font.py,v $
# Revision 1.3  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.3  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1.1.1  2006/08/16 20:58:53  t4w00-diedrich
# Initial import
#
#


"""
Implement higher level classes to handle fonts and font families.
"""

from string import *

class font:
    """
    Abstract base class for a font.
    """
    def __init__(self, ps_name, full_name, family_name,
                 weight, italic, fixed_width, metrics):
        """
        All these params become instance variables.
        
        @param ps_name: PostscriptIdentifyer for this font
        @param full_name: Human readable name
        @param family_name: The font family's name
        @param weight: Font weight as a string (Regular, Bold, SemiBold etc)
        @param italic: Boolean indicating whether this font is italic
        @param fixed_width: Boolean indicating whether this font has a fixed
           character width
        @param matrics: An instance of psg.font.metrics containing the font
           metrics.
        """
        self.ps_name = ps_name
        self.full_name = full_name
        self.family_name = family_name
        self.weight = weight
        self.italic = italic
        self.fixed_width = fixed_width

        self.metrics = metrics



class font_family:
    """
    A font family is a set of matching fonts with differnet weights
    and slant. A font family will have:

       - One attribute for each font, named without like the font with the
         family name removed and spaces and -s removed. These will usually be
         mixed case as the font names.
       - Four attributes in lower case regular, italic, bold, bolditalic which
         will always return a font, may be the default font, if the others
         couldn't be determined

    @ivar family_name: Full name of the family

    @ivar regular: Regular version of the font
    @ivar italic: Italic version of the font
    @ivar bold: Bold version of the font
    @ivar bolditalic: Version of the font that's both bold and italic
    """
    def __init__(self, fonts):
        self.family_name = fonts[0].family_name
        self._fonts = fonts
        
        for font in fonts:
            full_name = font.full_name
            family_name = font.family_name
            
            if len(full_name) < len(family_name):
                raise ValueError("There's something wrong with that font "+\
                                 "file: full name should be longer than "+\
                                 "family name")
            
            reminder = strip(full_name[len(family_name):])
            reminder = replace(reminder, "-", " ")
            reminder = splitfields(reminder)
            reminder = join(reminder)
            setattr(self, reminder, font)

            if font.italic:
                italic = True
            else:
                if "italic" in lower(full_name):
                    italic = True
                else:
                    italic = False
            
            if lower(font.weight) in ("regular", "book", "roman",):
                if italic:
                    self.italic = font
                else:
                    self.regular = font
                    
            elif lower(font.weight) in ("bold", "demi", "medium",):
                if italic:
                    self.bolditalic = font
                else:
                    self.bold = font

        if not hasattr(self, "regular"): # ouch...
            self.regular = fonts[0]
            
        for a in ("bold", "italic", "bolditalic",):
            if not hasattr(self, a):
                setattr(self, a, self.regular)

    def get(self, full_name):
        """
        Return font by full name.

        @raises FontNotFoundError:
        """
        for a in self._fonts:
            if a.full_name == full_name: return a

        raise FontNotFoundError(full_name)

    def fonts(self):
        """
        Returns a list of fonts in this family
        """
        return self._fonts


        

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

