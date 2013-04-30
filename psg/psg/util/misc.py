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
# $Log: misc.py,v $
# Revision 1.11  2007/04/09 19:21:49  diedrich
# Added web_color_to_ps_command(color)
#
# Revision 1.10  2006/11/15 21:53:50  diedrich
# Added always_parenthesis to ps_escape()
#
# Revision 1.9  2006/10/29 13:04:29  diedrich
# The copy_linewise() function now has an optional parameter ignore_comments.
#
# Revision 1.8  2006/09/11 13:49:36  t4w00-diedrich
# Octal code escape sequences in PS strings are always three digit now.
#
# Revision 1.7  2006/09/08 12:55:21  t4w00-diedrich
# Added pfb2pfa and pfb2pfa_buffer
#
# Revision 1.6  2006/08/30 03:56:56  t4w00-diedrich
# Added car() and cdr().
#
# Revision 1.5  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.4  2006/08/25 13:34:56  t4w00-diedrich
# Added ps_escape()
#
# Revision 1.3  2006/08/24 14:00:49  t4w00-diedrich
# line_iterator saves the last line now, not the last line's
# length. Saved a seek().
#
# Revision 1.2  2006/08/23 12:39:28  t4w00-diedrich
# Merge actually works pretty well now.
#
# Revision 1.1  2006/08/19 15:42:59  t4w00-diedrich
# Initial commit (as util)
#
#
#

"""
Misc utility functions and classes.
"""

__all__ = ["car", "cdr", "line_iterator", "copy_linewise", "ordered_set",
           "ps_escape", "join80", "eight_squares", "pfb2pfa", "pfb2pfa_buffer",
           "web_color_to_ps_command"]

import sys, os

from .measure import *

from .file_like_buffer import file_like_buffer
from .subfile import subfile
from ..exceptions import PFBError

# Lost In Single Paranthesis
def car(l): return l[0]
head = car
def cdr(l): return l[1:]
tail = cdr

class line_iterator:
    r"""
    Iterate over the lines in a file. Keep track of the line numbers.
    After a call to next() the file's seek indicator will point at the
    next by after the newline. Lines are delimited by either \r\n, \n,
    \r, which ever comes first, in this order. Lines that are longer
    than 256 bytes will be returned as 256 byte strings without a
    newline (because that's the buffer size). This function is binary
    save, no newline transformations are performed.

    FIXME: This needs to be rewriten! Best in C, I guess.
    """
    def __init__(self, fp):
        """
        Make sure to open fp binary mode so no newline conversion is
        performed.
        """
        self.fp = fp
        self.line_number = 0
        self.again = False
        self.last_line = ""

    def __next__(self):

        if self.again:
            self.again = False
            self.fp.seek(self.last_line_length, 1)
            return self.last_line

        old = self.fp.tell()
        buffer = self.fp.read(256)

        bytes_read = len(buffer)
        if bytes_read == 0: # eof
            raise StopIteration
        else:
            unix_index = buffer.find(b"\n")
            mac_index = buffer.find(b"\r")

            if unix_index == -1 and mac_index == -1:
                return buffer.decode("ASCII")
            else:
                if unix_index == -1: unix_index = len(buffer)
                if mac_index == -1: mac_index = len(buffer)

            if unix_index == mac_index + 1:
                eol = mac_index + 1
            elif unix_index > mac_index:
                eol = mac_index
            else:
                eol = unix_index

            ret = buffer[:eol+1].decode("ASCII")

            self.last_line_length = len(ret)
            self.fp.seek(old + self.last_line_length, 0)

            self.last_line = ret

            self.line_number += 1

            return ret

    readline = __next__

    def rewind(self):
        """
        'Rewind' the file to the line before this one.

        @raises: OSError (from file.seek())
        """
        self.again = True
        self.line_number -= 1
        self.fp.seek(-self.last_line_length, 1)


    def __iter__(self):
        return self


def copy_linewise(frm, to, ignore_comments=False):
    """
    This makes sure that all PostScript comments end with a regular
    Unix newline. (I'm not sure, what PostScript interpreters think of
    mixed-newline files.) Otherwise it does not alter the input stream
    and should be binary safe.
    """
    last_char = ""
    for line in line_iterator(frm):
        if not (ignore_comments and line.startswith("%%")):
            to.write(line)

        #if line.startswith("%"):
        #    if last_char != "\n": to.write("\n")
        #    to.write(strip(line))
        #    to.write("\n")
        #    last_char = "\n"
        #else:
        #    to.write(line)
        #    if len(line) > 0:
        #        last_char = line[-1]

class ordered_set(list):
    """
    Technically an ordered_set is a list, not a set. What it has in
    common with a set is that it will check whether a new element is
    already on the list and if so, not append it a second time.
    """
    def __init__(self, iterable=[]):
        list.__init__(self)
        map(self.append, iterable)

    def append(self, what):
        if what in self:
            return
        else:
            list.append(self, what)

    add = append

    def insert(self, idx, what):
        if what in self:
            return
        else:
            list.insert(self, idx, what)

def ps_escape(s, always_parenthesis=True):
    """
    Return a PostScript string literal containing s.

    @param always_parenthesis: If set, the returned literal will always
      have ()s around it. If it is not set, this will only happen, if
      a 's' contains a space.
    """
    if not  always_parenthesis and " " in s:
        always_parenthesis = True

    if always_parenthesis: ret = ["("]
    for a in map(ord, s):
        if (a < 32) or (chr(a) in r"\()"):
            ret.append(r"\03%o" % a)
        else:
            ret.append(chr(a))

    if always_parenthesis: ret.append(")")
    return "".join(ret)

def join80(collection):
    r"""
    Like string.join(collection, ' ') except that it uses \n occasionly to
    create 80char lines.
    """
    ret = []
    length = 0

    for a in collection:
        if length + len(a) > 80:
            ws = "\n"
            length = 0
        else:
            ws = " "
            length += len(a) + 1

        ret.append(a)
        ret.append(ws)

    if len(ret) > 1:
        del ret[-1]

    return "".join(ret)

def eight_squares(canvas, spacing=mm(6)):
    """
    Create eight equally sized sqares on the canvas. Return bounding_box
    objects representing the squares.
    """
    available_height = canvas.h() - 3*spacing
    box_size = available_height / 4.0
    if box_size > (canvas.w() - spacing) / 2.0:
        box_size = (canvas.w() - spacing) / 2.0

    top = canvas.h()
    for a in range(4):
        yield bounding_box(0, top-box_size,
                           box_size, top)
        yield bounding_box(box_size + spacing, top-box_size,
                           2*box_size + spacing, top)

        top -= box_size + spacing



def pfb2pfa(pfb, pfa):
    """
    Convert a PostScript Type1 font in binary representation (pfb) to
    ASCII representation (pfa). This function is modeled after the
    pfb2pfa program written in C by Piet Tutelaers. I freely admit
    that I understand only rudimentarily what I'm doing here.
    """

    while True:
        r = pfb.read(1)
        if ord(r) != 128:
            raise PFBError("Not a pfb file!")

        t = ord(pfb.read(1))

        if t == 1 or t == 2:
            l1 = ord(pfb.read(1))
            l2 = ord(pfb.read(1))
            l3 = ord(pfb.read(1))
            l4 = ord(pfb.read(1))

            l = l1 | l2 << 8 | l3 << 16 | l4 << 24

        if t == 1:
            for i in range(l):
                c = pfb.read(1)
                if c == "\r":
                    pfa.write("\n")
                else:
                    pfa.write(c.decode("ASCII"))

        elif t == 2:
            for i in range(l):
                c = pfb.read(1)
                pfa.write("%02x" % ord(c))
                if (i + 1) % 30 == 0:
                    pfa.write("\n")

            pfa.write("\n")
        elif t == 3:
            break
        else:
            raise PFBError("Error in PFB file: unknown field type %i!" % t)


class pfb2pfa_buffer(file_like_buffer):
    """
    A pfa2pfb buffer is a file like buffer which, initialized from a
    pfb file, will write a pfa file into its output file.
    """
    def __init__(self, pfb_fp):
        self.pfb = pfb_fp

    def write_to(self, fp):
        self.pfb.seek(0)
        pfb2pfa(self.pfb, fp)


def web_color_to_ps_command(color):
    """
    Take a web-compatible hexadecimal tuple as a string and return a
    PostScript command appropriate to set that color.
    """
    # Make sure we have a legal color string
    color = strip(lower(color))

    std_colors = { "white": "ffffff",
                   "black": "000000",
                   "red": "ff0000",
                   "green": "00ff00",
                   "blue": "0000ff" }

    if color in std_colors:
        color = std_colors[color]

    if color[0] == "#": color = color[1:]
    if len(color) > 6: color = color[:5]
    if len(color) != 6: color += "0" * (6 - len(color))

    red = int(color[:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[-2:], 16)

    return "%f %f %f setrgbcolor" % ( red / 255.0,
                                      green / 255.0,
                                      blue / 255.0, )


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

