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
# $Log: interpreter.py,v $
# Revision 1.3  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.3  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1.1.1  2006/08/16 20:58:54  t4w00-diedrich
# Initial import
#
#

"""
An interpreter is a PostScript runtime environment. These classes are
ment to manage resident fonts and enable PostScript generation for
specific devices. Right now (2006-8-16) the only actual 'device'
supported is Ghostscript. This classes might also be subclassed to
model a printer (maybe a generic PPD reder?) or the like.
"""

import sys, os.path
from string import *
from types import *

from psg.exceptions import *
from psg.fonts import font_family, type1

class interpreter:
    """
    @ivar fonts: dictionary as {'Font Name': Font Object or Font Alias}
       or fonts stored in the interpreter (not those that need to be embedded!)
       Font Name is the PostScript name (identifyer) for the font.
       Font Object are instances of psg.fonts.font or plain strings indicating
       aliases. Font names are case sensitive.
    @ivar fontpath: a list of strings, each a filesystem path to a
       directory where fonts are stored. 
    """
    def __init__(self, fontpath=[], fonts={}):
        """
        @param fontpath: A list of strings, each an operating system path
           to a font directory.
        """
        self.fonts = fonts
        self.fontpath = fontpath
        

    def font(self, name):
        """
        Return a font object for font named 'name'. This function
        resolves font aliases recursively.

        @param name: Python string object containing a font name
        @raises FontNotFoundError: if there is no such font. 
        """
        if self.fonts.has_key(name):
            ret = self.fonts.get(name)
            if type(ret) == StringType:
                return self.font(ret)
            
            if type(ret) == TupleType:
                # A tuple means the font has yet to be instantiated
                # and the metrics to be parsed. (Created with lazy=True)
                font_cls, init_args = ret
                font = font_cls(*init_args)
                self.fonts[name] = font
                return font
            
            else:
                return ret
        else:
            raise FontNotFoundError(name)
        
    def font_family(self, family_name):
        """
        Return a psg.fonts.font_family instance for the font family of the
        specified name. Names are case sensitive. The function will first
        check the font's family_name attributes. If a search through these
        yields no result it will search the font table for a font by that
        name and if there is one use its family.
        """
        fonts = filter(lambda font: getattr(font, "family_name",
                                            None) == family_name,
                       self.fonts.values())

        if len(fonts) == 0:
            for name in self.fonts.keys():
                if name.startswith(family_name):
                    fonts.append(self.font(name))

            if len(fonts) == 0:
                msg = "There is no %s font family." % family_name 
                raise FontNotFoundError(msg)
        
        return font_family(fonts)
    
    def font_from_filename(self, main_font_file,
                           resident=False, lazy=False):
        """
        Return a psg.font.font instance representing the font whoes
        main file name is passed as argument, if psg knows how to
        handle that font.

        Currently (2006-8-16) this only works for PostScript Type1
        fonts provided in either the .pfa or .pfb format *and* a
        metrics file with the same file name and the .afm ending.

        @param main_font_file: String containing the full path to a
           main font file (.pfa/b)
        @param resident: Indicates whether this font is pre-loaded in the
           interpreter's memory. In fact, if present, the function will not
           search for a .pfa/b file, but only for a .afm file.
        @param lazy: This is a specialty ment to be used by interpreter
           classes: If lazy is True, this function will return a pair as
           (font_class, init_args) that can be used to instantiate the
           actual font class only when needed. See font() above.

        @raises FileNotFoundError: if .afm file can't be found
        @returns: psg.font.font instance
        """
        suffix = lower(main_font_file[-3:])
        if suffix in ("pfa", "pfb",):

            filename = main_font_file[:-3]         
            path = os.path.dirname(filename)
            filename = os.path.basename(filename)
            
            if path == "":
                path = "."
            files = os.listdir(path)            

            afm_file = None
            for a in files:
                if a.startswith(filename) and len(a) > 3:
                    suffix = lower(a[-3:])

                    if suffix == "afm":
                        afm_file = os.path.join(path, a)
                        break

            if afm_file is None:
                msg = "Can't use a font without a .afm file! %s"%main_font_file
                raise FileNotFoundError(msg)

            if resident:
                main_font_file = None
            
            font_class = type1
            init_args = ( main_font_file, afm_file, )

        if lazy:
            return ( font_class, init_args, )
        else:
            return font_class(*init_args)
            
                        
            


        
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:






