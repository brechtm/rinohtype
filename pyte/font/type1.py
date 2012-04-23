
import struct, os

from . import Font
from .style import WEIGHTS, MEDIUM
from .style import SLANTS, UPRIGHT, OBLIQUE, ITALIC
from .style import WIDTHS, NORMAL, CONDENSED, EXTENDED
from .metrics import FontMetrics, GlyphMetrics
from .mapping import glyph_names, encodings


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
        try:
            file = open(file_or_filename, 'rt', encoding='ascii')
            close_file = True
        except TypeError:
            file = file_or_filename
            close_file = False
        self.parse(file)
        if close_file:
            file.close()

    def from_unicode(self, code):
        names = glyph_names[code]
        if type(names) == tuple:
            for name in names:
                if name in self.glyphs:
                    return self.glyphs[name]
            else:
                raise KeyError
        else:
            return self.glyphs[names]
        # TODO: map to uniXXXX or uXXXX names

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
                self.glyphs[glyph_metrics.name] = glyph_metrics
            elif section_names[-1] == 'KernPairs':
                tokens = line.split()
                if tokens[0] == 'KPX':
                    pair, kerning = (tokens[1], tokens[2]), tokens[-1]
                    self.kerning_pairs[pair] = number(kerning)
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
            self.ligatures[name] = ligatures
        return GlyphMetrics(name, width, bbox, code)


class Type1Font(Font):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL,
                 core=False):
        self.metrics = AdobeFontMetrics(filename + '.afm')
        encoding_name = self.metrics['FontMetrics']['EncodingScheme']
        if encoding_name == 'FontSpecific':
            self.encoding = {glyph.name: glyph.code
                             for glyph in self.metrics.glyphs.values()
                             if glyph.code > -1}
        else:
            self.encoding = encodings[encoding_name]
        super().__init__(weight, slant, width)
        self.filename = filename
        self.core = core
        if not core:
            if os.path.exists(filename + '.pfa'):
                self.parse_pfa(filename + '.pfa')
            else:
                self.parse_pfb(filename + '.pfb')

    @property
    def name(self):
        return self.metrics['FontMetrics']['FontName']

    def has_glyph(self, name):
        return name in self.metrics.glyphs

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
