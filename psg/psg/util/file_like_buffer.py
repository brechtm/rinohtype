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
# $Log: file_like_buffer.py,v $
# Revision 1.9  2006/09/08 12:54:59  t4w00-diedrich
# Import copy_linewise() during runtime to prevent recursive import.
#
# Revision 1.8  2006/08/30 14:17:41  t4w00-diedrich
# file_like_buffers ignore None values that are added to them
#
# Revision 1.7  2006/08/30 03:56:46  t4w00-diedrich
# Added file_as_buffer class.
#
# Revision 1.6  2006/08/29 20:05:59  t4w00-diedrich
# The whole composition and parsing process of the DSC module has been
# changed. Things are a lot more simple now and work much more reliably.
# Documents are encoded in-memory, with imports performed 'lazily', that
# is, on writing. This is a good compromise between speed and memory usage.
#
# Revision 1.5  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.4  2006/08/25 13:34:14  t4w00-diedrich
# Added prepend() to file_like_buffer and changed
# composition_buffer.append() to work more reliable.
#
# Revision 1.3  2006/08/23 12:39:28  t4w00-diedrich
# Merge actually works pretty well now.
#
# Revision 1.2  2006/08/21 18:59:18  t4w00-diedrich
# Bug fixing.
#
# Revision 1.1  2006/08/19 15:42:59  t4w00-diedrich
# Initial commit (as util)
#
#
#

"""
Buffers for output file generation
"""

import sys, os
from types import *
from io import StringIO

from ..exceptions import *

# Utilities for creating files

class file_like_buffer(list):
    """
    This class provides a minimal subset of a writable file: the
    write() and the writelines() method. It will store any string
    passed to these methods in an ordinary Python list. It provides
    two methods to acces its content (besides being the list of
    strings itself): as_string() returning the 'file's' content as an
    ordinary string and write_to() which will write the content to a
    file or file-like object using its write() method.

    No newslines will be added to any of the strings written.

    Instead of strings you may use any object providing a __str__ method
    """
    def __init__(self, *args):
        list.__init__(self, args)

        for a in self:
            if type(a) != str and not hasattr(a, "__str__"):
                raise TypeError("file_like_buffers can only 'contain' "
                                "string objects or those reducable to "
                                "strings")

    def write(self, s):
        """
        Write string s to the buffer.
        """
        self.append(s)

    def writelines(self, l):
        """
        Writes a sequence of strings to the buffer. Uses the append
        operator to check if all of l's elements are strings.
        """
        for a in l: self.append(l)

    __add__ = writelines # Use append() because of type checking.

    def as_string(self):
        """
        Return the buffer as an ordinary string.
        """
        fp = StringIO()
        self.write_to(fp)
        return fp.getvalue()

    __str__ = as_string

    def write_to(self, fp):
        """
        Write the buffer to file pointer fp.
        """
        for a in self:
            if hasattr(a, "write_to"):
                a.write_to(fp)
            else:
                fp.write(str(a))

    def append(self, what):
        """
        Overwrite list's append() method to add type checking.
        """
        if what is None:
            return
        else:
            self.check(what)
            list.append(self, what)

    def insert(self, idx, what):
        self.check(what)
        list.insert(self, idx, what)

    def prepend(self, what):
        """
        Insert an object as the first element of the list.
        """
        self.insert(0, what)

    def check(self, what):
        if type(what) != str and \
               not hasattr(what, "__str__") and \
               not hasattr(what, "write_to"):
            raise TypeError("You can only write strings to a "
                            "file_like_buffer, not %s" % repr(type(what)))


class file_as_buffer:
    def __init__(self, fp):
        self.fp = fp

    def write_to(self, fp):
        from .misc import copy_linewise
        copy_linewise(self.fp, fp)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

