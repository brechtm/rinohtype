
import struct, os

from warnings import warn

from . import Font
from .style import WEIGHTS, MEDIUM
from .style import SLANTS, UPRIGHT, OBLIQUE, ITALIC
from .style import WIDTHS, NORMAL, CONDENSED, EXTENDED
from .style import SMALL_CAPITAL, OLD_STYLE
from .metrics import FontMetrics, GlyphMetrics
from .mapping import UNICODE_TO_GLYPH_NAME, ENCODINGS
from ..warnings import PyteWarning


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


class AdobeFontMetrics(FontMetrics):
    sections = {'FontMetrics': string,
                'CharMetrics': int}

    keywords = {'FontName': string,
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

    def __init__(self, file_or_filename):
        super().__init__()
        self._glyphs = {}
        self._suffixes = {}
        self._ligatures = {}
        self._kerning_pairs = {}
        try:
            file = open(file_or_filename, 'rt', encoding='ascii')
            close_file = True
        except TypeError:
            file = file_or_filename
            close_file = False
        self.parse(file)
        if close_file:
            file.close()

        self.name = self['FontMetrics']['FontName']
        self.bbox = self['FontMetrics']['FontBBox']
        self.italic_angle = self['FontMetrics']['ItalicAngle']
        self.ascent = self['FontMetrics'].get('Ascender', 750)
        self.descent = self['FontMetrics'].get('Descender', -250)
        self.line_gap = 200
        self.cap_height = self['FontMetrics'].get('CapHeight', 700)
        self.x_height = self['FontMetrics'].get('XHeight', 500)
        self.stem_v = self['FontMetrics'].get('StdVW', 50)

    _possible_suffixes = {SMALL_CAPITAL: ('.smcp', '.sc', 'small'),
                          OLD_STYLE: ('.oldstyle', )}

    def _find_suffix(self, char, variant, upper=False):
        try:
            return self._suffixes[variant]
        except KeyError:
            for suffix in self._possible_suffixes[variant]:
                for name in self.char_to_name(char):
                    if name + suffix in self._glyphs:
                        self._suffixes[variant] = suffix
                        return suffix
            else:
                return ''
##            if not upper:
##                return self._find_suffix(self.char_to_name(char.upper()),
##                                         possible_suffixes, True)

    def char_to_name(self, char, variant=None):
        try:
            # TODO: first search character using the font's encoding
            name_or_names = UNICODE_TO_GLYPH_NAME[ord(char)]
            if variant and char != ' ':
                suffix = self._find_suffix(char, variant)
            else:
                suffix = ''
            try:
                yield name_or_names + suffix
            except TypeError:
                for name in name_or_names:
                    yield name + suffix
        except KeyError:
            # TODO: map to uniXXXX or uXXXX names
            warn('Don\'t know how to map unicode index 0x{:04x} ({}) '
                 'to a PostScript glyph name.'.format(ord(char), char),
                 PyteWarning)
            yield 'question'

    def get_glyph(self, char, variant=None):
        for name in self.char_to_name(char, variant):
            if name in self._glyphs:
                return self._glyphs[name]
        if variant:
            warn('No {} variant found for unicode index 0x{:04x} ({}), falling '
                 'back to the standard glyph.'.format(variant, ord(char), char),
                 PyteWarning)
            return self.get_glyph(char)
        else:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({}).'
                 .format(self.name, ord(char), char), PyteWarning)
            return self._glyphs['question']

    def get_ligature(self, glyph, successor_glyph):
        try:
            ligature_name = self._ligatures[glyph.name][successor_glyph.name]
            return self._glyphs[ligature_name]
        except KeyError:
            return None

    def get_kerning(self, a, b):
        return self._kerning_pairs.get((a.name, b.name), 0.0)

    def parse(self, file):
        sections = [self]
        section_names = [None]
        section = self
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
                glyph_metrics = self.parse_character_metrics(line)
                self._glyphs[glyph_metrics.name] = glyph_metrics
            elif section_names[-1] == 'KernPairs':
                tokens = line.split()
                if tokens[0] == 'KPX':
                    pair, kerning = (tokens[1], tokens[2]), tokens[-1]
                    self._kerning_pairs[pair] = number(kerning)
                else:
                    raise NotImplementedError
            else:
                funcs = self.keywords[key]
                try:
                    values = [func(val)
                              for func, val in zip(funcs, values.split())]
                except TypeError:
                    values = funcs(values)
                section[key] = values

    def parse_character_metrics(self, line):
        ligatures = {}
        for item in line.strip().split(';'):
            if not item:
                continue
            tokens = item.split()
            if tokens[0] == 'C':
                code = int(tokens[1])
            elif tokens[0] == 'C':
                code = int(tokens[1], base=16)
            elif tokens[0] in ('WX', 'W0X'):
                width = number(tokens[1])
            elif tokens[0] in ('WY', 'W0Y'):
                height = number(tokens[1])
            elif tokens[0] in ('W', 'W0'):
                width, height = number(tokens[1]), number(tokens[2])
            elif tokens[0] == 'N':
                name = tokens[1]
            elif tokens[0] == 'B':
                bbox = tuple(number(num) for num in tokens[1:])
            elif tokens[0] == 'L':
                ligatures[tokens[1]] = tokens[2]
            else:
                raise NotImplementedError
        if ligatures:
            self._ligatures[name] = ligatures
        return GlyphMetrics(name, width, bbox, code)


class Type1Font(Font):
    units_per_em = 1000

    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL,
                 core=False):
        metrics = AdobeFontMetrics(filename + '.afm')
        super().__init__(metrics, weight, slant, width)
        encoding_name = self.metrics['FontMetrics']['EncodingScheme']
        if encoding_name == 'FontSpecific':
            self.encoding = {glyph.name: glyph.code
                             for glyph in self.metrics._glyphs.values()
                             if glyph.code > -1}
        else:
            self.encoding = ENCODINGS[encoding_name]
        self.filename = filename
        self.core = core
        if not core:
            if os.path.exists(filename + '.pfa'):
                self.parse_pfa(filename + '.pfa')
            else:
                self.parse_pfb(filename + '.pfb')

    def parse_pfa(self, file):
        raise NotImplementedError

    def parse_pfb(self, filename):
        file = open(filename, 'rb')
        header_type, header_length, self.header = self.read_pfb_segment(file)
        body_type, body_length, self.body = self.read_pfb_segment(file)
        trailer_type, trailer_length, self.trailer = self.read_pfb_segment(file)
        check, eof_type = struct.unpack('<BB', file.read(2))
        file.close()
        if check != 128 or eof_type != 3:
            raise TypeError('Not a PFB file')

    def read_pfb_segment(self, file):
        header_fmt = '<BBI'
        header_data = file.read(struct.calcsize(header_fmt))
        check, segment_type, length = struct.unpack(header_fmt, header_data)
        if check != 128:
            raise TypeError('Not a PFB file')
        return segment_type, length, file.read(length)
