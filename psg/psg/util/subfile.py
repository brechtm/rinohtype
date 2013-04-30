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
# $Log: subfile.py,v $
# Revision 1.4  2006/08/30 14:18:08  t4w00-diedrich
# Added write_to() function to subfile.
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
Wrapper class for file objects that will emulate a file that contains
a specified subset of the 'parent' file.
"""

import sys, os
from string import *
from types import *



def subfile(fp, offset, length):
    """
    This is a funny thing: A subfil class Knows a file, an offset and
    a length. It implements the fill interface as described in the
    Python Library Reference chapter 2.2.8. It will emulate a file
    whoes first byte is the byte of the 'parent' file pointed to by
    the offset and whoes length is the provided length. After each of
    the calls to one of its functions, the 'parent' file's file
    pointer will be restored to its previous position.

    This function will return a filesystem_subfile instance if the
    provided file pointer is a regular file and a default_subfile if
    it is not.

    Obviously, the filepointer must support seeking. The file should
    be opened read-only. Though you *may* write to the 'parent' as
    well as to the subfile, you *may* not want to do so, 'cause it may
    screw things up goood...
    """
    if hasattr(fp, "fileno"):
        return filesystem_subfile(fp, offset, length)
    else:
        return default_subfile(fp, offset, length)

class _subfile(object):
    """
    Don't instantiate!! Although you can, don't!
    """
    def __init__(self, fp, offset, length):
        self.parent = fp
        self.offset = offset
        self.length = length

        self.seek(0)

    def close(self):
        self.parent.close()

    def flush(self):
        self.parent.flush()

    def isatty(self):
        return self.parent.isatty()

    def next(self):
        raise NotImplementedError("The subfile class dosn't support iteration "
                                  "use readlines() below!")

    def read(self, bytes=None):
        if bytes is None: bytes = self.length

        if self.parent.tell() + bytes > self.offset + self.length:
            bytes = self.offset + self.length - self.parent.tell()

        if bytes < 1:
            return ""
        else:
            return self.parent.read(bytes)

    def readline(self, size=None):
        old_pos = self.parent.tell()
        line = self.parent.readline()
        if self.parent.tell() > self.offset + self.length:
            too_many = self.parent.tell() - (self.offset + self.length)
            return line[:-too_many]
        else:
            return line

    def readlines(self, sizehint=256):
        old_tell = self.parent.tell()
        bytes_read = 0
        for line in self.parent.readlines():
            bytes_read += len(line)
            if old_tell + bytes_read > self.offset + self.length:
                too_many = (old_tell+ bytes_read) - (self.offset + self.length)
                yield line[:-too_many]
                break
            else:
                yield line


    def xreadlines(self):
        return self.readlines()

    def seek(self, offset, whence=0):
        if whence == 0:
            if offset < 0: raise IOError("Can't seek beyond file start")
            self.parent.seek(self.offset + offset, 0)
        elif whence == 1:
            if self.parent.tell() - offset < 0:
                raise IOError("Invalid argument (seek beyond file start)")
            self.parent.seek(offset, 1)
        elif whence == 2:
            self.parent.seek(self.offset + self.length + offset, 0)
        else:
            raise IOError("Invalid argument (don't know how to seek)")

    def tell(self):
        return self.parent.tell() - self.offset

    def truncate(self):
        raise NotImplementedError("subfile does not implement truncate!")

    def write(self, s):
        """
        This will happily overwrite the subfile's end into whatever it
        will find there. It will reset the file pointer to the end of
        the subfile if that happens.
        """
        self.parent.write(s)
        if self.parent.tell() > self.offset + self.length:
            self.seek(0, 2)

    def writelines(self, seq):
        for a in seq: write(str(a))

    def write_to(self, fp):
        self.seek(0)
        while True:
            r = self.read(1024)
            if len(r) == 0:
                break
            else:
                fp.write(r)


class filesystem_subfile(_subfile):
    def __init__(self, fp, offset, length):
        if not hasattr(fp, "fileno"):
            raise ValueError("A filesystem_subfile must always be used with "
                             "a regular file, owning a fileno() method")

        parent = os.fdopen(os.dup(fp.fileno()))
        if isinstance(fp, self.__class__):
            _subfile.__init__(self, parent, offset+fp.offset, length)
        else:
            _subfile.__init__(self, parent, offset, length)


    def fileno(self):
        return self.parent.fileno()

class default_subfile(_subfile):
    def __init__(self, fp, offset, length):
        _subfile.__init__(self, fp, offset, length)

    def save(self):
        self.parent_seek_pointer = self.parent.tell()
        self.parent.seek(self.offset + self.seek_pointer)

    def restore(self):
        self.seek_pointer = self.parent.tell() - self.offset
        self.parent.seek(self.parent_seek_pointer)

    def read(self, size=None):
        self.save()
        return _subfile.read(self, size)
        self.restore()

    def readline(self, size):
        self.save()
        return _subfile.readline(self, size)
        self.restore()

    def readlines(self, size):
        self.save()
        return _subfile.readlines(self, size)
        self.restore()

    def seek(self, offset, whence=0):
        if whence == 0:
            self.seek_pointer = offset
        elif whence == 1:
            self.seek_pointer += offset
        elif whence == 2:
            self.seek_pointer = self.length + offset
        else:
            raise IOError("Invalid argument (don't know how to seek)")

    def tell(self):
        return self.seek_pointer

    def write(self, s):
        self.save()
        return _subfile.write(self, s)
        self.restore()

    def writelines(self, l):
        self.save()
        return _subfile.writelines(self, l)
        self.restore()



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

# Utilities for reading files
