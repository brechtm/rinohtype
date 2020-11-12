# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re
import struct

from binascii import unhexlify
from io import BytesIO
from warnings import warn


from . import Font, GlyphMetrics, LeafGetter, MissingGlyphException
from .mapping import UNICODE_TO_GLYPH_NAME, ENCODINGS
from ..font.style import FontVariant, FontWeight, FontSlant, FontWidth
from ..util import cached
from ..warnings import warn


def string(string):
    return string.strip()


def number(string):
    try:
        number = int(string)
    except ValueError:
        number = float(string)
    return number


def boolean(string):
    return string.strip() == 'true'


class AdobeFontMetricsParser(dict):
    SECTIONS = {'FontMetrics': string,
                'CharMetrics': int}

    KEYWORDS = {'FontName': string,
                'FullName': string,
                'FamilyName': string,
                'Weight': string,
                'FontBBox': (number, number, number, number),
                'Version': string,
                'Notice': string,
                'EncodingScheme': string,
                'MappingScheme': int,
                'EscChar': int,
                'CharacterSet': string,
                'Characters': int,
                'IsBaseFont': boolean,
                'VVector': (number, number),
                'IsFixedV': boolean,
                'CapHeight': number,
                'XHeight': number,
                'Ascender': number,
                'Descender': number,
                'StdHW': number,
                'StdVW': number,

                'UnderlinePosition': number,
                'UnderlineThickness': number,
                'ItalicAngle': number,
                'CharWidth': (number, number),
                'IsFixedPitch': boolean}

    HEX_NUMBER = re.compile(r'<([\da-f]+)>', re.I)

    def __init__(self, file):
        self._glyphs = {}
        self._ligatures = {}
        self._kerning_pairs = {}
        sections, section = [self], self
        section_names = [None]
        for line in file.readlines():
            try:
                key, values = line.split(None, 1)
            except ValueError:
                key, values = line.strip(), []
            if not key:
                continue
            if key == 'Comment':
                pass
            elif key.startswith('Start'):
                section_name = key[5:]
                section_names.append(section_name)
                section[section_name] = {}
                section = section[section_name]
                sections.append(section)
            elif key.startswith('End'):
                assert key[3:] == section_names.pop()
                sections.pop()
                section = sections[-1]
            elif section_names[-1] == 'CharMetrics':
                glyph_metrics = self._parse_character_metrics(line)
                self._glyphs[glyph_metrics.name] = glyph_metrics
            elif section_names[-1] == 'KernPairs':
                tokens = line.split()
                if tokens[0] == 'KPX':
                    pair, kerning = (tokens[1], tokens[2]), tokens[-1]
                    self._kerning_pairs[pair] = number(kerning)
                else:
                    raise NotImplementedError
            elif section_names[-1] == 'Composites':
                warn('Composites in Type1 fonts are currently not supported.'
                     '({})'.format(self.filename) if self.filename else '')
            elif key == chr(26):    # EOF marker
                assert not file.read()
            else:
                funcs = self.KEYWORDS[key]
                try:
                    values = [func(val)
                              for func, val in zip(funcs, values.split())]
                except TypeError:
                    values = funcs(values)
                section[key] = values

    def _parse_character_metrics(self, line):
        ligatures = {}
        for item in line.strip().split(';'):
            if not item:
                continue
            tokens = item.split()
            key = tokens[0]
            if key == 'C':
                code = int(tokens[1])
            elif key == 'CH':
                code = int(self.HEX_NUMBER.match(tokens[1]).group(1), base=16)
            elif key in ('WX', 'W0X'):
                width = number(tokens[1])
            elif key in ('WY', 'W0Y'):
                height = number(tokens[1])
            elif key in ('W', 'W0'):
                width, height = number(tokens[1]), number(tokens[2])
            elif key == 'N':
                name = tokens[1]
            elif key == 'B':
                bbox = tuple(number(num) for num in tokens[1:])
            elif key == 'L':
                ligatures[tokens[1]] = tokens[2]
            else:
                raise NotImplementedError
        if ligatures:
            self._ligatures[name] = ligatures
        return GlyphMetrics(name, width, bbox, code)


class AdobeFontMetrics(Font, AdobeFontMetricsParser):
    units_per_em = 1000
    # encoding is set in __init__

    name = LeafGetter('FontMetrics', 'FontName')
    bounding_box = LeafGetter('FontMetrics', 'FontBBox')
    fixed_pitch = LeafGetter('FontMetrics', 'IsFixedPitch')
    italic_angle = LeafGetter('FontMetrics', 'ItalicAngle')
    ascender = LeafGetter('FontMetrics', 'Ascender', default=750)
    descender = LeafGetter('FontMetrics', 'Descender', default=-250)
    line_gap = 200
    cap_height = LeafGetter('FontMetrics', 'CapHeight', default=700)
    x_height = LeafGetter('FontMetrics', 'XHeight', default=500)
    stem_v = LeafGetter('FontMetrics', 'StdVW', default=50)

    def __init__(self, file_or_filename, weight, slant, width,
                 unicode_mapping=None):
        try:
            filename = file_or_filename
            file = open(file_or_filename, 'rt', encoding='ascii')
            close_file = True
        except TypeError:
            filename = None
            file = file_or_filename
            close_file = False
        self._suffixes = {FontVariant.NORMAL: ''}
        self._unicode_mapping = unicode_mapping
        AdobeFontMetricsParser.__init__(self, file)
        if close_file:
            file.close()
        if self.encoding_scheme == 'FontSpecific':
            self.encoding = {glyph.name: glyph.code
                             for glyph in self._glyphs.values()
                             if glyph.code > -1}
        else:
            self.encoding = ENCODINGS[self.encoding_scheme]
        super().__init__(filename,  weight, slant, width)

    encoding_scheme = LeafGetter('FontMetrics', 'EncodingScheme')

    _SUFFIXES = {FontVariant.SMALL_CAPITAL: ('.smcp', '.sc', 'small'),
                 FontVariant.OLDSTYLE_FIGURES: ('.oldstyle', )}

    def _find_suffix(self, char, variant, upper=False):
        try:
            return self._suffixes[variant]
        except KeyError:
            for suffix in self._SUFFIXES[variant]:
                for name in self._char_to_glyph_names(char,
                                                      FontVariant.NORMAL):
                    if name + suffix in self._glyphs:
                        self._suffixes[variant] = suffix
                        return suffix
            else:
                return ''
##            if not upper:
##                return self._find_suffix(self.char_to_name(char.upper()),
##                                         possible_suffixes, True)

    def _unicode_to_glyph_names(self, unicode):
        if self._unicode_mapping:
            for name in self._unicode_mapping.get(unicode, []):
                yield name
        try:
            for name in UNICODE_TO_GLYPH_NAME[unicode]:
                yield name
            # TODO: map to uniXXXX or uXXXX names
        except KeyError:
            warn("Don't know how to map unicode index 0x{:04x} ({}) to a "
                 "PostScript glyph name.".format(unicode, chr(unicode)))

    def _char_to_glyph_names(self, char, variant):
        suffix = self._find_suffix(char, variant) if char != ' ' else ''
        for name in self._unicode_to_glyph_names(ord(char)):
            yield name + suffix

    @cached
    def get_glyph(self, char, variant):
        for name in self._char_to_glyph_names(char, variant):
            if name in self._glyphs:
                return self._glyphs[name]
        if variant != FontVariant.NORMAL:
            warn('No {} variant found for unicode index 0x{:04x} ({}), falling '
                 'back to the standard glyph.'.format(variant, ord(char), char))
            return self.get_glyph(char, FontVariant.NORMAL)
        else:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({}).'
                 .format(self.name, ord(char), char))
            raise MissingGlyphException

    def get_ligature(self, glyph, successor_glyph):
        try:
            ligature_name = self._ligatures[glyph.name][successor_glyph.name]
            return self._glyphs[ligature_name]
        except KeyError:
            return None

    def get_kerning(self, a, b):
        return self._kerning_pairs.get((a.name, b.name), 0.0)


class PrinterFont(object):
    def __init__(self, header, body, trailer):
        self.header = header
        self.body = body
        self.trailer = trailer


class PrinterFontASCII(PrinterFont):
    START_OF_BODY = re.compile(br'\s*currentfile\s+eexec\s*')

    def __init__(self, filename):
        with open(filename, 'rb') as file:
            header = self._parse_header(file)
            body, trailer = self._parse_body_and_trailer(file)
        super().__init__(header, body, trailer)

    @classmethod
    def _parse_header(cls, file):
        header = BytesIO()
        for line in file:
            # Adobe Reader can't handle carriage returns, so we remove them
            header.write(line.translate(None, b'\r'))
            if cls.START_OF_BODY.match(line.translate(None, b'\r\n')):
                break
        return header.getvalue()

    @staticmethod
    def _parse_body_and_trailer(file):
        body = BytesIO()
        trailer_lines = []
        number_of_zeros = 0
        lines = file.readlines()
        for line in reversed(lines):
            number_of_zeros += line.count(b'0')
            trailer_lines.append(lines.pop())
            if number_of_zeros == 512:
                break
            elif number_of_zeros > 512:
                raise Type1ParseError
        for line in lines:
            cleaned = line.translate(None, b' \t\r\n')
            body.write(unhexlify(cleaned))
        trailer = BytesIO()
        for line in reversed(trailer_lines):
            trailer.write(line.translate(None, b'\r'))
        return body.getvalue(), trailer.getvalue()


class PrinterFontBinary(PrinterFont):
    SECTION_HEADER_FMT = '<BBI'
    SEGMENT_TYPES = {'header': 1,
                     'body': 2,
                     'trailer': 1}

    def __init__(self, filename):
        with open(filename, 'rb') as file:
            segments = []
            for segment_name in ('header', 'body', 'trailer'):
                segment_type, segment = self._read_pfb_segment(file)
                if self.SEGMENT_TYPES[segment_name] != segment_type:
                    raise Type1ParseError('Not a PFB file')
                segments.append(segment)
            check, eof_type = struct.unpack('<BB', file.read(2))
            if check != 128 or eof_type != 3:
                raise Type1ParseError('Not a PFB file')
        super().__init__(*segments)

    @classmethod
    def _read_pfb_segment(cls, file):
        header_data = file.read(struct.calcsize(cls.SECTION_HEADER_FMT))
        check, segment_type, length = struct.unpack(cls.SECTION_HEADER_FMT,
                                                    header_data)
        if check != 128:
            raise Type1ParseError('Not a PFB file')
        return int(segment_type), file.read(length)


class Type1Font(AdobeFontMetrics):
    def __init__(self, filename, weight=FontWeight.MEDIUM,
                 slant=FontSlant.UPRIGHT, width=FontWidth.NORMAL,
                 unicode_mapping=None, core=False):
        super().__init__(filename + '.afm', weight, slant, width,
                         unicode_mapping)
        self.core = core
        if not core:
            if os.path.exists(filename + '.pfb'):
                self.font_program = PrinterFontBinary(filename + '.pfb')
            else:
                self.font_program = PrinterFontASCII(filename + '.pfa')


class Type1ParseError(Exception):
    pass
