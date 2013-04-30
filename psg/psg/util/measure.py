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
# $Log: measure.py,v $
# Revision 1.4  2006/10/29 13:03:36  diedrich
# Added parse_paper_size()
#
# Revision 1.3  2006/09/06 23:24:30  t4w00-diedrich
# Added __eq__() to bounding_box
#
# Revision 1.2  2006/08/25 13:34:40  t4w00-diedrich
# Added PAPERSIZES dict and fixed the unit conversion functions
#
# Revision 1.1  2006/08/21 18:57:58  t4w00-diedrich
# Initial commit
#
#
#

"""
This module contains functions and classes for calculating length and
area on paper.
"""

__all__ = ["PAPERSIZES", "parse_paper_size",
    "pt", "m", "dm", "cm", "mm", "foot", "feet", "inch", "pc", "pica",
    "parse_length", "min", "max", "bounding_box"]


import sys
from types import *
from string import *

PAPERSIZES = {
    # This dict is copied over from the pyscript project.

    # Page sizes defined by Adobe documentation
    "11x17": (792, 1224),
    # a3 see below
    # a4 see below
    # a4small should be a4 with an ImagingBBox of [25 25 570 817].
    # b5 see below
    "ledger": (1224, 792), # 11x17 landscape
    "legal": (612, 1008),
    "letter": (612, 792),
    # lettersmall should be letter with an ImagingBBox of [25 25 587 767].
    # note should be letter (or some other size) with the ImagingBBox
    # shrunk by 25 units on all 4 sides.

    # ISO standard paper sizes
    "a0": (2380, 3368),
    "a1": (1684, 2380),
    "a2": (1190, 1684),
    "a3": (842, 1190),
    "a4": (595, 842),
    "a5": (421, 595),
    "a6": (297, 421),
    "a7": (210, 297),
    "a8": (148, 210),
    "a9": (105, 148),
    "a10": (74, 105),

    # ISO and JIS B sizes are different....
    # first ISO
    "b0": (2836, 4008),
    "b1": (2004, 2836),
    "b2": (1418, 2004),
    "b3": (1002, 1418),
    "b4": (709, 1002),
    "b5": (501, 709),
    "b6": (354, 501),
    "jisb0": (2916, 4128),
    "jisb1": (2064, 2916),
    "jisb2": (1458, 2064),
    "jisb3": (1032, 1458),
    "jisb4": (729, 1032),
    "jisb5": (516, 729),
    "jisb6": (363, 516),
    "c0": (2600, 3677),
    "c1": (1837, 2600),
    "c2": (1298, 1837),
    "c3": (918, 1298),
    "c4": (649, 918),
    "c5": (459, 649),
    "c6": (323, 459),

    # U.S. CAD standard paper sizes
    "arche": (2592, 3456),
    "archd": (1728, 2592),
    "archc": (1296, 1728),
    "archb": (864, 1296),
    "archa": (648, 864),

    # Other paper sizes
    "flsa": (612, 936), # U.S. foolscap
    "flse": (612, 936), # European foolscap
    "halfletter": (396, 612),

    # Screen size (NB this is 2mm too wide for A4):
    "screen": (800, 600) }


def parse_paper_size(name, allow_arbitrary=False):
    if name.endswith("landscape"):
        name = strip(name[:-len("landscape")])
        value = parse_paper_size(name, allow_arbitrary)
        return value[1], value[0]

    elif name.endswith("portrait"):
        name = strip(name[:-len("portrait")])
        return parse_paper_size(name, allow_arbitrary)

    if PAPERSIZES.has_key(name):
        w, h =  PAPERSIZES[name]
        return float(w), float(h)
    else:
        if allow_arbitrary:
            pair = split(name, "x")
            if len(pair) != 2:
                raise IllegalPaperSize("I don't know %s" % repr(name))

            try:
                w, h = pair
                w = float(w)
                h = float(h)

                return w, h
            except ValueError:
                raise IllegalPaperSize("I don't know %s" % repr(name))
        else:
            raise IllegalPaperSize("I don't know %s" % repr(name))

# Units - convert everybody's units to PostScript Points

def pt(l):
    return l

def m(l):
     return l / 0.0254 * 72.0

def dm(l):
    return l / 0.254 * 72.0

def cm(l):
    return l / 2.54 * 72.0

def mm(l):
    return l / 25.4 * 72.0

def foot(l):
    return l * 12.0 * 72.0

feet = foot

def inch(l):
    return l * 72.0

def pc(l):
    return l / 6.0 * 72.0

pica = pc

_units = ( "pt", "dm", "cm", "mm", "m", "foot", "inch", "pc", "m",)

def parse_length(s):
    for unit in _units:
        if s.endswith(unit):
            value = s[:-len(unit)]
            try:
                value = float(value)
            except ValueError:
                raise ValueError("Illegal length: %s" % repr(s))

            func = globals()[unit]
            return func(value)

    try:
        value = float(s)
    except ValueError:
        raise ValueError("Illegal length: %s" % repr(s))

    return value


def min(a, b):
    if a < b:
        return a
    else:
        return b

def max(a, b):
    if a > b:
        return a
    else:
        return b

class bounding_box:
    """
    A PostScript BountingBox
    """
    def __init__(self, llx=0, lly=0, urx=0, ury=0):
        """
        Lower left and upper right coordinates. The constrctor will
        'turn' the rectangle so that the first point is the lower left
        and the second the opper right, in the sense of positive
        coordinates the first quadrant of a cartesian plane
        (i.e. Postscript's 'math' geometry rather than 'hardware'
        geometry).
        """

        # Turn the rectangle so that the first point is the lower left
        # and the second the upper right.
        if llx > urx: llx, urx = urx, llx
        if lly > ury: lly, ury = ury, lly

        self.llx = llx
        self.lly = lly
        self.urx = urx
        self.ury = ury

    def from_tuple(cls, tpl):
        llx, lly, urx, ury = tpl
        return cls(llx, lly, urx, ury)

    from_tuple = classmethod(from_tuple)

    def from_string(cls, s):
        """
        Initialize from a PostScript (DSC) string using the
        dsc.parse_literal() function.
        """
        from psg.document import dsc
        tpl = dsc.parse_literals(s, "ffff")
        return cls.from_tuple(tpl)

    from_string = classmethod(from_string)

    def surrounding(self, other):
        """
        Return the bounding box that sourrounds both, self and other.
        """
        return bounding_box(min(self.llx, other.llx),
                            min(self.lly, other.lly),
                            max(self.urx, other.urx),
                            max(self.urx, other.ury))

    def copy(self):
        return bounding_box(self.llx, self.lly, self.urx, self.ury)

    def as_string(self, hires=False):
        """
        @returns: A string representation of this BoundingBox, eigther as
           integers (hires=False, default) or float (hires=True) literals.
        """
        if hires:
            return "%f %f %f %f" % self.as_tuple()
        else:
            return "%i %i %i %i" % self.as_tuple()

    __str__ = as_string

    def as_tuple(self):
        return ( self.llx, self.lly, self.urx, self.ury, )

    def width(self):
        return self.urx-self.llx

    def height(self):
        return self.ury-self.lly

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

