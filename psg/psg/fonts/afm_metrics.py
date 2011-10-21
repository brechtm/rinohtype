##!/usr/bin/python
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
# $Log: afm_metrics.py,v $
# Revision 1.7  2006/09/22 16:27:35  t4w00-diedrich
# Added ascender and descender attributes.
#
# Revision 1.6  2006/09/08 12:54:30  t4w00-diedrich
# Added font_bounding_box() method
#
# Revision 1.5  2006/09/06 23:23:08  t4w00-diedrich
# Docstring update.
#
# Revision 1.4  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.3  2006/08/24 13:57:05  t4w00-diedrich
# Use fp instead for file name for afm_metric constructor
#
# Revision 1.2  2006/08/18 17:39:49  t4w00-diedrich
# Initial commit
#
# Revision 1.1.1.1  2006/08/16 20:58:48  t4w00-diedrich
# Initial import
#
#


"""
This module defines afm_metrics. This class implements the metrics
interface as a higher level interface to the AFM file parser from
afm_parser.py.
"""

import re
from warnings import warn

from psg.util import bounding_box
from .afm_parser import parse_afm
from .metrics import metrics, glyph_metric
from .encoding_tables import encoding_tables, glyph_name_to_unicode


class global_info(property):
    """
    Property class for properties that can be retrieved directly from
    the parser data.
    """
    def __init__(self, keyword):
        self.keyword = keyword

    def __get__(self, metrics, owner="dummy"):
        return metrics.FontMetrics.get(self.keyword, None)


class afm_metrics(metrics):
    gs_uni_re = re.compile("uni[A-Z0-9]{4}")

    def __init__(self, fp):
        """
        @param fp: File pointer of the AFM file opened for reading.
        """
        metrics.__init__(self)

        self.FontMetrics = parse_afm(fp)

        # Create a glyph_metric object for every glyph and put it into self
        # indexed by its unicode code.
        char_metrics = self.FontMetrics["Direction"][0]["CharMetrics"]

        # glyph name to unicode mapping
        for glyph_name, info in char_metrics.by_glyph_name.items():
            if self.gs_uni_re.match(glyph_name):
                # This may be a Ghostscript specific convention. No word
                # about this in the standard document.
                unicode_char_code = int(glyph_name[3:], 16)
            elif glyph_name != '.notdef':
                try:
                    unicode = glyph_name_to_unicode[glyph_name]
##                    if unicode in self:
##                        warn("'{0}': glyph '{1}' is already stored for unicode "
##                             "{2:04x}".format(glyph_name, self[unicode].ps_name,
##                                              unicode))
##                        continue
                    bb = bounding_box.from_tuple(info["B"])
                    self[unicode] = glyph_metric(info["C"], info["W0X"],
                                                 glyph_name, bb)
                except KeyError:
                    pass

        # FontEncoding to unicode mapping
        try:
            encoding_table = encoding_tables[self.encoding_scheme]
            try:
                for char_code, info in char_metrics.items():
                    unicode_char_code = encoding_table[char_code]
                    self[unicode_char_code] = glyph_metric(char_code,
                                                           info["W0X"],
                                                           info.get("N", None),
                                                           bb)
            except KeyError:
                raise KeyError("Character code not in encoding table")
        except KeyError:
            pass

        # Create kerning pair index
        try:
            kern_pairs = self.FontMetrics["KernData"]["KernPairs"]
            for pair, info in kern_pairs.iteritems():
                a, b = pair
                key, info0, info1 = info

                if key == "KPH":
                    a = char_metrics[a]['N']
                    b = char_metrics[b]['N']

                kerning = info0
                self.kerning_pairs[ ( a, b, ) ] = kerning
        except KeyError:
            pass

    def get_kerning(self, a, b, default=0.0):
        # a and b are unicode character codes or glyph names
        try:
            # TODO: remove temporary try/except when equations are fixed
            if type(a) == int:
                a = self[a].ps_name
            if type(b) == int:
                b = self[b].ps_name
        except KeyError:
            pass

        return self.kerning_pairs.get((a, b), default)

    ps_name = global_info("FontName")
    full_name = global_info("FullName")
    family_name = global_info("FamilyName")
    weight = global_info("Weight")
    character_set = global_info("CharacterSet")
    encoding_scheme = global_info("EncodingScheme")
    fontbbox = global_info("FontBBox")
    ascender = global_info("Ascender")
    descender = global_info("Descender")

    def _italic(self):
        if self.FontMetrics.get("ItalicAngle", 0) == 0:
            return False
        else:
            return True

    def _fixed_width(self):
        Direction = self.FontMetrics["Direction"][0]
        if Direction is None:
            return None
        else:
            return Direction.get("IsFixedPitch", False)

    def character_codes(self):
        """
        Return a list of available character codes in font encoding.
        """
        cm = self.FontMetrics["Direction"][0]["CharMetrics"]
        return cm.keys()

    def font_bounding_box(self):
        """
        Return the font bounding box as a bounding_box object in regular
        PostScript units.
        """
        numbers = self.fontbbox
        numbers = map(lambda n: n / 1000.0, numbers)
        return bounding_box.from_tuple(numbers)

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

