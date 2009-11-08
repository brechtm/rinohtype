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
# $Log: exceptions.py,v $
# Revision 1.8  2006/10/29 13:01:02  diedrich
# Added IllegalPaperSize exception.
#
# Revision 1.7  2006/09/22 16:24:46  t4w00-diedrich
# Added EndOfDocument exception.
#
# Revision 1.6  2006/09/08 12:54:05  t4w00-diedrich
# Added CommentMissing and PFBError
#
# Revision 1.5  2006/08/30 14:15:16  t4w00-diedrich
# Added BoxTooSmall exception.
#
# Revision 1.4  2006/08/30 03:54:05  t4w00-diedrich
# Added EndOfBox
#
# Revision 1.3  2006/08/19 15:41:30  t4w00-diedrich
# Added DSCSyntaxError
#
# Revision 1.2  2006/08/18 17:39:49  t4w00-diedrich
# Initial commit
#
# Revision 1.1.1.1  2006/08/16 20:58:47  t4w00-diedrich
# Initial import
#
#

"""
This module defines psg speficic exceptions. 
"""

class PSGException(Exception): pass

class AFMParseError(PSGException):
    """
    ParseError in an AFM file
    """
    pass

class FontmapParseError(PSGException):
    """
    Parse error while reading Ghostscript's fontmap
    """
    pass

class FontNotFoundError(PSGException): pass
class FileNotFoundError(PSGException): pass
class IllegalFunctionCall(PSGException): pass
class DSCSyntaxError(PSGException): pass
class CommentMissing(PSGException): pass
class PFBError(PSGException): pass

class EndOfBox(PSGException): pass
class BoxTooSmall(PSGException): pass
class EndOfDocument(PSGException): pass
class IllegalPaperSize(PSGException): pass

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

