#!/usr/bin/env python
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
# $Log: wmfutil.py,v $
# Revision 1.2  2006/12/10 01:11:15  diedrich
# Bugfixing
#
# Revision 1.1  2006/12/09 21:34:17  diedrich
# Initial commit
#
#

import struct

class struct_stream:
    """
    This class is meant to make reading files that consist of C
    structs (like WMF files) easier. Data can be read just like from a
    regular file, but the class allows for two special things: (1) You
    can 'rewind' the last read() operation, so that the next reading
    will seem to start at the same file position as the previous
    one. This works even if the input file does not support
    seeking. (2) This class provides the read_fmt() function which
    takes a format string for the struct module's unpack() function as
    an argument and returnes the resulting Python tuple.
    """
    def __init__(self, fp):
        """
        @param fp: A regular file pointer opened for reading.
        """
        self.fp = fp
        self.last = None
        self._rewound = False
        
    def read(self, bytes):
        """
        @param bytes: Number of bytes to read from the file. This
           parameter is mandetory.
        @returns: A string of bytes read from the file, just like
           file.read()   
        """
        if not self._rewound:
            self.last = self.fp.read(bytes)            
            return self.last
        else:
            self._rewound = False
            if len(self.last) == bytes:
                return self.last
            elif len(self.last) > bytes:
                ret = self.last[:bytes]
                self.last = self.last[:bytes]
                return ret
            else:
                ret = self.last + self.fp.read(bytes - len(self.last))
                self.last = ret
                return ret

    def read_fmt(self, format):
        """
        This function uses struct.calcsize() on the format, reads the
        appropriate number of bytes and struct.unpack()s them, returning
        the resulting tuple.
        """
        data = self.read(struct.calcsize(format))
        return struct.unpack(format, data)

    def rewind(self):
        """
        'Virtually' return the file pointer to the position it was at
        on the last call to read() or read_fmt(). (No actual seek()ing
        is done, though. This works with a memory buffer).
        """
        if last is not None:
            self._rewound = True


    def skip(self, bytes):
        """
        Skip 'bytes' number of bytes in the input stream. This is done 
        using seek() and if that fails, by reading and discarding the 
        appropriate number of bytes. 
        """
        try:
            self.fp.seek(bytes, 1)
        except IOError:
            self.read(bytes)

def getcolor(one, two):
    """
    Takes two 16bit unsigned integers (as regular Python integer, of
    course) and interprets them as a Windows COLORREF for an RGB color.
    It will always return a three tuple of integers. 
    """
    # From libwmf's Xwmfapi.c
    red = (one & 0x00FF) * 65535 / 255 % 256
    green = ((one & 0xFF00) >> 8) * 65535 / 255 % 256
    blue = (two & 0x00FF) * 65535 / 255 % 256

    return ( red / 2.56, green / 2.56, blue / 2.56, )
    
