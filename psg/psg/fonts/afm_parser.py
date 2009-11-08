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
# $Log: afm_parser.py,v $
# Revision 1.6  2006/11/04 18:21:56  diedrich
# Docstring update
#
# Revision 1.5  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.5  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.4  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.3  2006/08/24 13:57:43  t4w00-diedrich
# Use util.line_iterator
#
# Revision 1.2  2006/08/18 17:39:04  t4w00-diedrich
# Modified to use another line iterator. Soon to be replaced by a Mac
# compatible version...
#
# Revision 1.1.1.1  2006/08/16 20:58:49  t4w00-diedrich
# Initial import
#
#


"""
This module defines classes to parse and represent Adobe Font Metrics
files and provides functionality to conveniently access the
information contained. It adheres to the Adobe Font Metrics Format
Specification v. 4.1 available at
U{http://partners.adobe.com/public/developer/font/index.html} and
attempts to be a complete implementation for AFM files (not for ACFM
and AMFM, though these could be added with some industry).

The idea is that an AFM file has sections which contain other sections
and keywords. Sections represented by section objects which implement
the dictionary interface and contain the information contained in that
section with the AFM keywords as keys and the values as Python
primitives, other section objects or lists of other section objects.

a -> FontMetrics

>>> a['FontName']
'Helvetica'

>>> a.Direction[0].UnderlinePosition
None

>>> a.['Direction'][0]['CharMetrics']
<CharMetrics section object>

The structure of an AFM file looks like this::

  FontMetrics
    .. Global Font Info ..

    Direction 0
      .. Direction Info ..

      CharMetrics
        .. Special formated lines with the metrics ..

      KernData
        .. Special formated lines with the kerning data ..

      Composits
        .. Special formaed lines with the composit character data ..

    Direction 1
      .. Direction Info ..

      CharMetrics
        .. Special formated lines with the metrics ..

      KernData
        .. Special formated lines with the kerning data ..

      Composits
        .. Special formaed lines with the composit character data ..

    The Start/StopDirection are optional in an AFM file (who came up
    with *that*??).
"""

import sys, re
from warnings import warn
from types import *

from psg.exceptions import AFMParseError as ParseError
from psg.util import *

# Redefine int and float to raise ParseError instead of ValueError

py_int = int

class int(py_int):
    def __init__(self, value, base=10):
        try:
            py_int.__init__(self, value, base)
        except ValueError:
            raise ParseError(
                "Illegal representation of an integer: %s" % repr(value))

py_float = float

class float(py_float):
    def __init__(self, value):
        try:
            py_float.__init__(self, value)
        except ValueError:
            raise ParseError(
                "Illegal representation of a float: %s" % repr(value))


def float_tuple(elements, size):
    """
    Will parse the first size elements to float and return a
    size-tuple.
    """
    ret = []
    for a in range(size):
        ret.append(float(elements[a]))

    return tuple(ret)

def float_pair(elements):
    """
    Will return the first elements of string list elements as
    a pair of float.
    """
    return float_tuple(elements, 2) # generic classes for AFM file objects


# Regular expression for a PS hexadecimal number
ps_hex_int_re = re.compile("<([a-zA-Z0-9])*?>")

def ps_hex_int(data):
    """
    Return integer value of a PostScript hexadecimal literal. They look like
    <12AB> und so.
    """
    match = ps_hex_int_re.match(data)
    if match is None:
        raise ParseError("Illegal hexadecimal representation: %s" % repr(data))
    else:
        data = match.group(1)

    return int(data, 16)

# Helper classes for sets of sections and keywords

class _keywords(list):
    """
    Store a list of keyword or section classes
    """
    def __init__(self, *args):
        for arg in args:
            if type(arg) != type:
                raise ValueError(
                  "There may only be classes in a keywords list, not %s (%s)"%
                                             ( repr(type(arg)), repr(arg),) )
            self.append(arg)

    def keywords(self):
        for a in self:
            yield a.__name__

    def cls(self, keyword):
        if keyword.startswith("Start"):
            keyword = keyword[5:]

        for a in self:
            if a.__name__ == keyword:
                return a

        raise ParseError("Unknown keyword: %s" % repr(keyword))

class _sections(_keywords):
    def start_keywords(self):
        for a in self.keywords():
            yield "Start%s" % a

# Keyword and Section classes

class keyword:
    """
    Abstract class for all the keywords.

    @cvar optional: Specifies whether this keyword must appear in its
      section
    @cvar default: Default value used on initialization if no info is given.
    """
    optional = True
    default = None

    def __init__(self, info):
        if (info is None or info == "") and self.default is not None:
            self.info = self.default
        else:
            self.info = info

    def value(self):
        return self.info

class section(keyword, dict):
    """
    Abstract base class for all file section.
    A section is a dict mapping contained keywords to the appropriate
    information. As opposed to regular dicts, the dict may contain
    entries several times.

    @cvar info_cls: Class into which the info string shall be converted
       (int or float, actually)
    @cvar opotional: Specifies whether a Start/End pair for this section
       may be omited (as for Start/EndDirection)
    @cvar multiple: integer indicating if the parent section may contain
       several of these sections. 0 means there is only one, a number > 0
       means there may be that number of instences
    @cvar subsections: List of possible subsection classes
    @cvar keywords: List of keyword classes that this section
      may contain
    @cvar implicit_start_stop: Boolean indicating whether this section's
      Start/StopSection keywords may be omited (I hate this feature!)
    @ivar _all: List containing all entries to the dict.
    """
    info_cls = int
    optional = False
    multiple = 0
    implicit_start_stop = False

    subsections = _sections()
    keywords = _keywords()

    def __init__(self, line_iterator, info, parent, implicit_keyword=False):
        """
        @param line_iterator: Line iterator (see below)
          seek()) with the file pointer at the beginning of the first line
          for this section
        @param info: The rest of the section keyword's line (in a line
          'StartDirection 0' it would be ' 0'
        @param implicit_keyword: Boolean indicating whether this section
          started without a keyword. True implies that this section ends with
          the end of file.
        """
        keyword.__init__(self, info)
        self._all = []

        try:
            if self.info is not None:
                self.info = self.info_cls(self.info)
        except ValueError:
            raise ParseError("Can't parse %s as %s" % \
                            ( repr(info), self.info_cls.__name__, ))

        self.implicit_keyword = implicit_keyword

        self.parse(line_iterator, parent)
        self.check()

    def parse(self, line_iterator, parent):
        while True:
            line = line_iterator.readline()
            if line == "":
                if self.implicit_keyword:
                    break
                else:
                    raise ParseError("Unexpected end of file")

            if line.strip() == "": # empty line
                continue

            parts = line.split()
            keyword = parts[0]

            if len(parts) > 1:
                info = " ".join(parts[1:])
            else:
                info = ""

            if keyword in self.keywords.keywords():
                self.add_keyword(keyword, info)
            elif keyword in self.subsections.start_keywords():
                self.add_subsection(line_iterator, keyword, info)
            elif keyword.startswith("End%s" % self.__class__.__name__):
                return # Finished this section
            elif parent is not None and keyword in parent.keywords.keywords():
                # It seems that if the subsection's keywords are omited
                # section and subsection keywords may be mixed freely.
                # No word of that in the specification but as Adobe's own
                # files do it, it must be "standard" complient, I guess.
                # This format suks.
                parent.add_keyword(keyword, info)
            elif parent is not None and keyword \
                                   in parent.subsections.start_keywords():
                parent.add_subsection(line_iterator, keyword, info)
            elif parent is not None and \
                     keyword.startswith("End%s" % parent.__class__.__name__):
                # We'v run into the parent's End line, rewind the file buffer
                # so that the parent sees the line and pass control back
                # to 'him'.
                line_iterator.rewind()
                return
            elif keyword in ( "",  "Comment", ) :
                continue # An empty line
            elif keyword[0] in "abcdefghijklmnopqrstuvwxyz":
                continue # keywords that start with a lower char are user
                         # defined and supposed to be ignored
            else:
                # Check the subsection's keyword lists: If it is a keyword
                # from an implicit subsection rewind the filepointer to the
                # beginning of the line and create a new section.
                found = False
                for cls in self.subsections:
                    if cls.implicit_start_stop and \
                       keyword in cls.keywords.keywords():
                        line_iterator.rewind()
                        found = True
                        self.add_subsection(line_iterator, cls.__name__, None,
                                            implicit_start_stop=True)

                if not found:
                    tpl = ( self.__class__.__name__, repr(line), )
                    raise ParseError("Unknown line in %s section: %s " % tpl)

    def check(self):
        pass

    def add_subsection(self, line_iterator, keyword, info,
                       implicit_start_stop=False):
        subsection_class = self.subsections.cls(keyword)
        section_object = subsection_class(line_iterator, info, self,
                                          implicit_start_stop)

        if keyword.startswith("Start"):
            keyword = keyword[5:]

        if section_object.multiple == 0:
            if keyword in self:
                tpl = ( keyword, self.__class__.__name__, )
                raise ParseError("Multiple %s sections in %s" % tpl)
            self.set(keyword, section_object)
        else:
            try:
                if info is None:
                    idx = 0
                else:
                    idx = int(info)

                if keyword not in self:
                    l = []
                    for a in range(section_object.multiple):
                        l.append(None)

                    self.set(keyword, l)
                else:
                    l = self.get(keyword)

                l[idx] = section_object
                #subsection_class(line_iterator, info, self)
            except ValueError:
                raise ParseError("Can't parse %s into int" %repr(info))

    def add_keyword(self, keyword, info):
        if keyword in self:
            tpl = ( self.__class__.__name__, keyword, )
            raise ParseError("Section %s already has keyword %s" % tpl)
        else:
            cls = self.keywords.cls(keyword)
            obj = cls(info)
            self.set(keyword, obj.value())

    def set(self, name, value):
       if name not in self:
           self[name] = value

       self._all.append( (name, value,) )

    __setvalue__ = set

    def values(self):
        return list(self.itervalues())

    def itervalues(self):
        for a in self._all:
            yield a[1]

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for a in self._all:
            yield a


class data_section(section):
    """
    Abstract base class for section that contain 'non-keyword' data like
    FontMetrics and KernData. Subclasses need to overload the parse_line()
    method and probably the constructor, too, to set up their own
    datastructures. Of course, since this class implements the dictionary
    interface its objects may be used as a container themselves.
    """
    info_cls = int

    def parse(self, line_iterator, parent):
        while True:
            line = line_iterator.readline()

            if line == "":
                raise ParseError("Unexpected end of file")
            elif line.strip().startswith("End%s" % self.__class__.__name__):
                return # end of section
            elif line.strip() == "":
                continue # empty line
            else:
                # pass the line
                self.parse_line(line)


    def parse_line(self, line):
        raise NotImplementedError()

# Keyword types

class string(keyword):
    """
    For keys containing strings. Does the same thing keyword does...
    """
    pass

class integer(keyword):
    """
    For integer values
    """
    def __init__(self, info):
        self.info = int(info)

class number(keyword):
    """
    For 'number' values, i.e. floats
    """
    def __init__(self, info):
        self.info = float(info)

class tuple_of_number(keyword):
    """
    For tuples of numbers of a give size
    """
    tuple_size = 2
    def __init__(self, info):
        parts = info.split()
        info = []

        for part in parts:
            info.append(float(part))

        if len(info) != self.tuple_size:
            raise ParseError("%s needs %i number arguments" % \
                             ( self.__class__.__name__, self.tuple_size, ))

        self.info = tuple(info)

class boolean(keyword):
    def __init__(self, info):
        if "true" in info.lower():
            self.info = True
        elif "false" in info.lower():
            self.info = False
        else:
            raise ParseError("%s needs boolean argument" % \
                             ( self.__class__.__name__, ))

class array(keyword):
    def __init__(self, info):
        raise NotImplementedError()






# Actuel Keywords

class MetricSets(integer): pass
class FontName(string): optional = False
class FullName(string): pass
class FamilyName(string): pass
class Weight(string): pass
class FontBBox(tuple_of_number): tuple_size = 4; optional=False
class Version(string): pass
class Notice(string): pass
class EncodingScheme(string): pass
class MappingScheme(integer): pass
class EscChar(integer): pass
class CharacterSet(string): pass
class Characters(integer): pass
class IsBaseFont(boolean): pass
class VVector(tuple_of_number): tuple_size = 2
class IsFixedV(boolean): pass
class CapHeight(number): pass
class XHeight(number): pass
class Ascender(number): pass
class Descender(number): pass
class IsCIDFont(boolean): pass
class StdHW(number): pass
class StdVW(number): pass

class UnderlinePosition(number): pass
class UnderlineThickness(number): pass
class ItalicAngle(number): pass
class CharWidth(tuple_of_number): tuple_size = 2
class IsFixedPitch(boolean): pass


# Actual Sections

class CharMetrics(data_section):

    def parse_line(self, line):
        """
        Parse a CharMetrics line info a dict as { 'KEY': info }
        """
        line = line.strip() # get rid of eol characters
        parts = line.split(";") # split by the ;s
        parts = filter(lambda s: s != "", parts) # remove whitespace

        info = {}
        for part in parts:
            elements = part.split()

            key = elements[0]
            if len(elements) < 2:
                raise ParseError("CharMetrics key without data")
            else:
                elements = elements[1:]
                data = " ".join(elements)

            # For these codes see Adobe Font Metrics File Format Specification
            # 3d. edition, pp. 31ff (section 8).

            if key == "C": # character code
                info["C"] = int(data)
                info["CH"] = int(data)

            elif key == "CH": # character code (hex)
                data = ps_hex_int(data)
                info["C"] = data
                info["CH"] = data

            elif key == "WX" or key == "W0X": # character width direction 0
                data = float(data)

                info["WX"] = data
                info["W0X"] = data

            elif key == "W1X": # character width direction 1
                info["W1X"] = float(data)

            elif key == "WY" or key == "W0Y": # character height direction 0
                data = float(data)

                info["WY"] = data
                info["W0Y"] = data

            elif key == "W1Y": # character height direction 1
                info["W1Y"] = float(data)

            elif key == "W" or key == "W0": # character width vector (wri dir 0
                wx, wy = float_pair(elements)
                info["W"] = ( wx, wy, )
                info["W0"] = ( wx, wy, )

            elif key == "W1": # character width vector (writing direction 1)
                wx, wy = float_pair(elements)
                info["W1"] = ( wx, wy, )

            elif key == "W1": # character width vector (writing direction 1)
                wx, wy = float_pair(elements)
                info["W1"] = ( wx, wy, )

            elif key == "N": # postscript character name
                info["N"] = data

            elif key == "B": # character bounding box
                info["B"] = float_tuple(elements, 4)

            elif key == "L": # Ligature
                if len(elements) != 2:
                    raise ParseError(
                        "CharMetrics key L must be L successor ligature")
                info["L"] = tuple(elements)

            else:
                raise ParseError("Unknown CharMetric line: %s" % repr(line))

        if "C" not in info:
            raise ParseError("Illegal CharMetrics line: Either C or CH key" +\
                             "Must be present! (%s)" % repr(line))
        else:
            self.set(info["C"], info)

class TrackKern(data_section):
    """
    The TrackKern dictionary will contain tuples like::

       (degree, min-ptsize, min-kern, max-ptsize, max-kern,)

    following the TrackKern semantics as described in the format
    specifications on page 33 (section 9). degree is an integer, the
    others are floats. degree will be used as the dictionary key.
    """
    def parse_line(self, line):
        elements = line.split()
        elements = filter(lambda a: a != "", elements)

        if len(elements) != 6:
            raise ParseError("Illegal TrackKern dataset: %s" % repr(line))

        degree = int(elements[0])
        rest = elements[1:]
        rest = map(float, rest)

        tpl = tuple([degree] + rest)
        self.set(degree, tpl)


class KernPairs(data_section):
    """
    The KernPairs dict will contain tuples as::

       ( 'KP|KPH|KPX|KPY', float, float, )

    keyed by pairs of strings (character names) or pairs of integers
    (hex representations). I'd love to key the data by both but I
    don't know how to get character names from hex representations.
    """
    def parse_line(self, line):
        line = line.strip() # get rid of eol characters
        parts = line.split(";") # split by the ;s
        parts = filter(lambda s: s != "", parts) # remove whitespace

        info = {}
        for part in parts:
            elements = part.split()

            key = elements[0]
            if len(elements) < 2:
                raise ParseError("KernPairs key without data: %s" % repr(line))
            else:
                elements = elements[1:]
                data = " ".join(elements)

            try:
                if key == "KP":
                    key = ( elements[0], elements[1], )
                    value = ( "KP", float(elements[2]), float(elements[3]), )
                elif key == "KPH":
                    key = ( ps_hex_int(elements[0]), ps_hex_int(elements[1]), )
                    value = ( "KPH", float(elements[2]), float(elements[3]), )
                elif "KPX":
                    key = ( elements[0], elements[1], )
                    value = ( "KPX", float(elements[2]), 0, )
                elif "KPY":
                    key = ( elements[0], elements[1], )
                    value = ( "KPY", 0, float(elements[2]), )
                else:
                    raise ParseError("Unknown data key in KernPairs line %s" %\
                                                                    repr(line))

                self.set(key, value)
            except IndexError:
                msg = "Illegel number of data elements in KernPairs line %s" %\
                                                                     repr(line)
                raise ParseError(msg)

class KernPairs0(KernPairs): pass
class KernPairs1(KernPairs): pass

class KernData(section):
    info_cls = int
    default = 0

    subsections = _sections(TrackKern, KernPairs, KernPairs0, KernPairs1)

    def check(self):
        if "KernPairs" in self:
            self["KernPairs0"] = self["KernPairs"]

        if "KernPairs0" in self:
            self["KernPairs"] = self["KernPairs0"]

class Composites(data_section):
    """
    The Composits dict will contain lists of tuples, each representing a
    part of the composit char and a displacement vector. The dict will be
    keyed by the name of the resulting char. Refer to section 10 of the
    AFM file specification for details (p. 37f).
    """

    def parse_line(self, line):
        line = line.strip() # get rid of eol characters
        parts = line.split(";") # split by the ;s

        name = None
        char_parts_num = None
        char_parts = []
        for part in parts:
            elements = splitf(part, ";")
            elements = filter(lambda s: s != "", elements) # remove whitespace

            try:
                key = elements[0]
                if len(elements) < 2:
                    msg = "Composit definition key without data: %s"%repr(line)
                    raise ParseError(msg)
                else:
                    elements = elements[1:]
                    data = " ".join(elements)

                if key == "CC":
                    name = elements[0]
                    char_part_num = float(elements[1])

                elif key == "PCC":
                    name = elements[0]
                    delta_x = int(elements[1])
                    delta_y = int(elements[2])

                    char_parts.append( ( name, delta_x, deltay, ) )
                else:
                    raise ParseError("Unknown element in composit: %s" % \
                                                                   repr(line))
            except IndexError:
                msg = "Illegal number of elements in composit char: %s" % \
                                                                   repr(line)
                raise ParseError(msg)

        if name is None:
            raise ParseError("Character name missing from composit char: %s"%\
                                                                   repr(line))

        if char_parts_num != len(char_parts):
            warn("Composit char parts count mismatch: %s (not %i elements)" %\
                                                 (repr(line), char_part_num,))

        self.set(name, char_parts)

class Direction(section):
    optional = False
    multiple = 2
    implicit_start_stop = True

    subsections = _sections( CharMetrics, Composites )
    keywords = _keywords( UnderlinePosition, UnderlineThickness, ItalicAngle,
                          CharWidth, IsFixedPitch )

    info_cls = float

class FontMetrics(section):
    subsections = _sections( Direction, KernData)
    keywords = _keywords( MetricSets,
                          FontName, FullName, FamilyName, Weight,
                          FontBBox, Version, Notice,
                          EncodingScheme, MappingScheme,
                          EscChar, CharacterSet, Characters,
                          IsBaseFont, VVector, IsFixedV,
                          IsCIDFont, # ??
                          CapHeight, XHeight, Ascender, Descender,
                          StdHW, StdVW)


    def __init__(self, lines, parent, info):
        self._all = []
        self.info = float(info)
        self.parse(lines, parent)

# Pars function


def parse_afm(fp):
    """
    Parse afm file pointed to by fp. Return a FontMetrics object.
    """
    lines = line_iterator(fp)
    first_line = lines.readline()
    parts = first_line.split()

    if parts[0] != "StartFontMetrics" or len(parts) != 2:
        raise ParseError("Not a valid AFM file!")

    version = float(parts[1])
    if version > 4.1:
        warn("This parser only knows AFM specification v. 4.1.")

    try:
        return FontMetrics(lines, None, parts[1])
    except ParseError as e:
        e.args = ( e.args[0] + (" (line: %i)" % lines.line_number), )
        raise


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

