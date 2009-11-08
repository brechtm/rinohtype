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
# $Log: metrics.py,v $
# Revision 1.5  2006/09/19 14:09:14  t4w00-diedrich
# Fixed typo in bounding_box
#
# Revision 1.4  2006/09/11 13:50:38  t4w00-diedrich
# Changed stringwidth()
#
# Revision 1.3  2006/08/30 03:56:28  t4w00-diedrich
# Added stringwidth() function.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1.1.1  2006/08/16 20:58:53  t4w00-diedrich
# Initial import
#
#


"""
This module defines a generic class for font metrics.
"""

from types import *

class glyph_metric:
    def __init__(self, font_character_code, 
                 width, ps_name, bounding_box):
        """
        @param font_character_code: 8Bit character code of the glyph in the
           font's encoding
        @param width: Character width
        @param ps_name: PostScript character name. May be None.
        @param bounding_box: Charachter bounding box in 1/1000th unit
        """
        self.font_character_code = font_character_code
        self.width = width
        self.ps_name = ps_name
        self.bounding_box = bounding_box

class metrics(dict):
    """
    Base class for font metric calculaions. Metrics objects are dict
    that map unicode character codes (integers) to glyph_metric
    objects. The class provides a special mechanism for accessing
    calculated attributes, see __getattr__() below.

    @ivar kerning_pairs: Dict object mapping tuples of integer (unicode
      codes) to floats (kerning value for that pair).
    """
    def __init__(self):
        self.kerning_pairs = {}
        self.kerning_pairs.setdefault(0.0)
    
    def __getattr__(self, name):
        """
        The getattr will check, if there's a method called _name(). If
        so it will be invoked and the result stored as an attribute
        called name for later usage. This may copy the entire metrics
        from the parsed representation into this object's namespace.
        """
        
        if hasattr(self, "_" + name):
            method = getattr(self, "_" + name)
            ret = method()
            setattr(self, name, ret)
            return ret

        #if self.__class__.__dict__.has_key(name):
        #    prop = self.__class__.__dict__[name]
        #    
        #    if isinstance(prop, property):
        #        return prop.__get__(self)
            
        raise AttributeError(name)

    def unicode_character_codes(self):
        """
        Return a list of available character codes in unicode encoding.        
        """
        return self.keys()

    def stringwidth(self, s, font_size, kerning=True, char_spacing=0.0):
        """
        Return the width of s when rendered in the current font in
        regular PostScript units. The boolean parameter kerning
        indicates whether the font's pair-wise kerning information
        will be taken into account, if available. The char_spacing
        parameter is in regular PostScript units, too.
        """
        if len(s) == 1:
            return self.get(ord(s), self[32]).width * font_size / 1000.0
        else:
            width = sum(map(lambda char: self.get(ord(char), self[32]).width,
                            s)) * font_size
            
            if kerning:
                for a in range(len(s)-1):
                    char = s[a]
                    next = s[a+1]
                    kerning = self.kerning_pairs.get( (char, next,), 0.0 )
                    width += kerning * font_size
            else:
                kerning = 0.0

            if char_spacing > 0:
                width += (len(s) - 1) * char_spacing * 1000.0

            return width / 1000.0
        

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

