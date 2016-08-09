# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import codecs


def search_function(encoding):
    if encoding == 'pdf_doc':
        return getregentry()


codecs.register(search_function)


### Codec APIs

class Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        return codecs.charmap_encode(input, errors, encoding_table)

    def decode(self, input, errors='strict'):
        return codecs.charmap_decode(input, errors, decoding_table)


class IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return codecs.charmap_encode(input, self.errors, encoding_table)[0]


class IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return codecs.charmap_decode(input, self.errors, decoding_table)[0]


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='pdf-doc',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )


### Decoding Table (from the PDF reference)

decoding_table = (
    '\ufffe'    #  0x00 -> (NULL)
    '\ufffe'    #  0x01 -> (START OF HEADING)
    '\ufffe'    #  0x02 -> (START OF TEXT)
    '\ufffe'    #  0x03 -> (END OF TEXT)
    '\ufffe'    #  0x04 -> (END OF TEXT)
    '\ufffe'    #  0x05 -> (END OF TRANSMISSION)
    '\ufffe'    #  0x06 -> (ACKNOWLEDGE)
    '\ufffe'    #  0x07 -> (BELL)
    '\ufffe'    #  0x08 -> (BACKSPACE)
    '\ufffe'    #  0x09 -> (CHARACTER TABULATION)
    '\ufffe'    #  0x0A -> (LINE FEED)
    '\ufffe'    #  0x0B -> (LINE TABULATION)
    '\ufffe'    #  0x0C -> (FORM FEED)
    '\ufffe'    #  0x0D -> (CARRIAGE RETURN)
    '\ufffe'    #  0x0E -> (SHIFT OUT)
    '\ufffe'    #  0x0F -> (SHIFT IN)
    '\ufffe'    #  0x10 -> (DATA LINK ESCAPE)
    '\ufffe'    #  0x11 -> (DEVICE CONTROL ONE)
    '\ufffe'    #  0x12 -> (DEVICE CONTROL TWO)
    '\ufffe'    #  0x13 -> (DEVICE CONTROL THREE)
    '\ufffe'    #  0x14 -> (DEVICE CONTROL FOUR)
    '\ufffe'    #  0x15 -> (NEGATIVE ACKNOWLEDGE)
    '\ufffe'    #  0x16 -> (SYNCRONOUS IDLE)
    '\ufffe'    #  0x17 -> (END OF TRANSMISSION BLOCK)
    '\u02d8'    #  0x18 -> BREVE
    '\u02c7'    #  0x19 -> CARON
    '\u02c6'    #  0x1A -> MODIFIER LETTER CIRCUMFLEX ACCENT
    '\u02d9'    #  0x1B -> DOT ABOVE
    '\u02dd'    #  0x1C -> DOUBLE ACUTE ACCENT
    '\u02db'    #  0x1D -> OGONEK
    '\u02da'    #  0x1E -> RING ABOVE
    '\u02dc'    #  0x1F -> SMALL TILDE
    ' '         #  0x20 -> SPACE (&#32;)
    '!'         #  0x21 -> EXCLAMATION MARK
    '"'         #  0x22 -> QUOTATION MARK (&quot;)
    '#'         #  0x23 -> NUMBER SIGN
    '$'         #  0x24 -> DOLLAR SIGN
    '%'         #  0x25 -> PERCENT SIGN
    '&'         #  0x26 -> AMPERSAND (&amp;)
    "'"         #  0x27 -> APOSTROPHE (&apos;)
    '('         #  0x28 -> LEFT PARENTHESIS
    ')'         #  0x29 -> RIGHT PARENTHESIS
    '*'         #  0x2A -> ASTERISK
    '+'         #  0x2B -> PLUS SIGN
    ','         #  0x2C -> COMMA
    '-'         #  0x2D -> HYPHEN-MINUS
    '.'         #  0x2E -> FULL STOP (period)
    '/'         #  0x2F -> SOLIDUS (slash)
    '0'         #  0x30 -> DIGIT ZERO
    '1'         #  0x31 -> DIGIT ONE
    '2'         #  0x32 -> DIGIT TWO
    '3'         #  0x33 -> DIGIT THREE
    '4'         #  0x34 -> DIGIT FOUR
    '5'         #  0x35 -> DIGIT FIVE
    '6'         #  0x36 -> DIGIT SIX
    '7'         #  0x37 -> DIGIT SEVEN
    '8'         #  0x38 -> DIGIT EIGJT
    '9'         #  0x39 -> DIGIT NINE
    ':'         #  0x3A -> COLON
    ';'         #  0x3B -> SEMICOLON
    '<'         #  0x3C -> LESS THAN SIGN (&lt;)
    '='         #  0x3D -> EQUALS SIGN
    '>'         #  0x3E -> GREATER THAN SIGN (&gt;)
    '?'         #  0x3F -> QUESTION MARK
    '@'         #  0x40 -> COMMERCIAL AT
    'A'         #  0x41 ->
    'B'         #  0x42 ->
    'C'         #  0x43 ->
    'D'         #  0x44 ->
    'E'         #  0x45 ->
    'F'         #  0x46 ->
    'G'         #  0x47 ->
    'H'         #  0x48 ->
    'I'         #  0x49 ->
    'J'         #  0x4A ->
    'K'         #  0x4B ->
    'L'         #  0x4C ->
    'M'         #  0x4D ->
    'N'         #  0x4E ->
    'O'         #  0x4F ->
    'P'         #  0x50 ->
    'Q'         #  0x51 ->
    'R'         #  0x52 ->
    'S'         #  0x53 ->
    'T'         #  0x54 ->
    'U'         #  0x55 ->
    'V'         #  0x56 ->
    'W'         #  0x57 ->
    'X'         #  0x58 ->
    'Y'         #  0x59 ->
    'Z'         #  0x5A ->
    '['         #  0x5B -> LEFT SQUARE BRACKET
    '\\'        #  0x5C -> REVERSE SOLIDUS (backslash)
    ']'         #  0x5D -> RIGHT SQUARE BRACKET
    '^'         #  0x5E -> CIRCUMFLEX ACCENT (hat)
    '_'         #  0x5F -> LOW LINE (SPACING UNDERSCORE)
    '`'         #  0x60 -> GRAVE ACCENT
    'a'         #  0x61 ->
    'b'         #  0x62 ->
    'c'         #  0x63 ->
    'd'         #  0x64 ->
    'e'         #  0x65 ->
    'f'         #  0x66 ->
    'g'         #  0x67 ->
    'h'         #  0x68 ->
    'i'         #  0x69 ->
    'j'         #  0x6A ->
    'k'         #  0x6B ->
    'l'         #  0x6C ->
    'm'         #  0x6D ->
    'n'         #  0x6E ->
    'o'         #  0x6F ->
    'p'         #  0x70 ->
    'q'         #  0x71 ->
    'r'         #  0x72 ->
    's'         #  0x73 ->
    't'         #  0x74 ->
    'u'         #  0x75 ->
    'v'         #  0x76 ->
    'w'         #  0x77 ->
    'x'         #  0x78 ->
    'y'         #  0x79 ->
    'z'         #  0x7A ->
    '{'         #  0x7B -> LEFT CURLY BRACKET
    '|'         #  0x7C -> VERTICAL LINE
    '}'         #  0x7D -> RIGHT CURLY BRACKET
    '~'         #  0x7E -> TILDE
    '\ufffe'    #  0x7F -> Undefined
    '\u2022'    #  0x80 -> BULLET
    '\u2020'    #  0x81 -> DAGGER
    '\u2021'    #  0x82 -> DOUBLE DAGGER
    '\u2026'    #  0x83 -> HORIZONTAL ELLIPSIS
    '\u2014'    #  0x84 -> EM DASH
    '\u2013'    #  0x85 -> EN DASH
    '\u0192'    #  0x86 ->
    '\u2044'    #  0x87 -> FRACTION SLASH (solidus)
    '\u2039'    #  0x88 -> SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    '\u203a'    #  0x89 -> SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    '\u2212'    #  0x8A ->
    '\u2030'    #  0x8B -> PER MILLE SIGN
    '\u201e'    #  0x8C -> DOUBLE LOW-9 QUOTATION MARK (quotedblbase)
    '\u201c'    #  0x8D -> LEFT DOUBLE QUOTATION MARK (double quote left)
    '\u201d'    #  0x8E -> RIGHT DOUBLE QUOTATION MARK (quotedblright)
    '\u2018'    #  0x8F -> LEFT SINGLE QUOTATION MARK (quoteleft)
    '\u2019'    #  0x90 -> RIGHT SINGLE QUOTATION MARK (quoteright)
    '\u201a'    #  0x91 -> SINGLE LOW-9 QUOTATION MARK (quotesinglbase)
    '\u2122'    #  0x92 -> TRADE MARK SIGN
    '\ufb01'    #  0x93 -> LATIN SMALL LIGATURE FI
    '\ufb02'    #  0x94 -> LATIN SMALL LIGATURE FL
    '\u0141'    #  0x95 -> LATIN CAPITAL LETTER L WITH STROKE
    '\u0152'    #  0x96 -> LATIN CAPITAL LIGATURE OE
    '\u0160'    #  0x97 -> LATIN CAPITAL LETTER S WITH CARON
    '\u0178'    #  0x98 -> LATIN CAPITAL LETTER Y WITH DIAERESIS
    '\u017d'    #  0x99 -> LATIN CAPITAL LETTER Z WITH CARON
    '\u0131'    #  0x9A -> LATIN SMALL LETTER DOTLESS I
    '\u0142'    #  0x9B -> LATIN SMALL LETTER L WITH STROKE
    '\u0153'    #  0x9C -> LATIN SMALL LIGATURE OE
    '\u0161'    #  0x9D -> LATIN SMALL LETTER S WITH CARON
    '\u017e'    #  0x9E -> LATIN SMALL LETTER Z WITH CARON
    '\ufffe'    #  0x9F -> Undefined
    '\u20ac'    #  0xA0 -> EURO SIGN
    '\u00a1'    #  0xA1 -> INVERTED EXCLAMATION MARK
    '\xa2'      #  0xA2 -> CENT SIGN
    '\xa3'      #  0xA3 -> POUND SIGN (sterling)
    '\xa4'      #  0xA4 -> CURRENCY SIGN
    '\xa5'      #  0xA5 -> YEN SIGN
    '\xa6'      #  0xA6 -> BROKEN BAR
    '\xa7'      #  0xA7 -> SECTION SIGN
    '\xa8'      #  0xA8 -> DIAERESIS
    '\xa9'      #  0xA9 -> COPYRIGHT SIGN
    '\xaa'      #  0xAA -> FEMININE ORDINAL INDICATOR
    '\xab'      #  0xAB -> LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    '\xac'      #  0xAC -> NOT SIGN
    '\ufffe'    #  0xAD -> Undefined
    '\xae'      #  0xAE -> REGISTERED SIGN
    '\xaf'      #  0xAF -> MACRON
    '\xb0'      #  0xB0 -> DEGREE SIGN
    '\xb1'      #  0xB1 -> PLUS-MINUS SIGN
    '\xb2'      #  0xB2 -> SUPERSCRIPT TWO
    '\xb3'      #  0xB3 -> SUPERSCRIPT THREE
    '\xb4'      #  0xB4 -> ACUTE ACCENT
    '\xb5'      #  0xB5 -> MICRO SIGN
    '\xb6'      #  0xB6 -> PILCROW SIGN
    '\xb7'      #  0xB7 -> MIDDLE DOT
    '\xb8'      #  0xB8 -> CEDILLA
    '\xb9'      #  0xB9 -> SUPERSCRIPT ONE
    '\xba'      #  0xBA -> MASCULINE ORDINAL INDICATOR
    '\xbb'      #  0xBB -> RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    '\xbc'      #  0xBC -> VULGAR FRACTION ONE QUARTER
    '\xbd'      #  0xBD -> VULGAR FRACTION ONE HALF
    '\xbe'      #  0xBE -> VULGAR FRACTION THREE QUARTERS
    '\xbf'      #  0xBF -> INVERTED QUESTION MARK
    '\xc0'      #  0xC0 ->
    '\xc1'      #  0xC1 ->
    '\xc2'      #  0xC2 ->
    '\xc3'      #  0xC3 ->
    '\xc4'      #  0xC4 ->
    '\xc5'      #  0xC5 ->
    '\xc6'      #  0xC6 ->
    '\xc7'      #  0xC7 ->
    '\xc8'      #  0xC8 ->
    '\xc9'      #  0xC9 ->
    '\xca'      #  0xCA ->
    '\xcb'      #  0xCB ->
    '\xcc'      #  0xCC ->
    '\xcd'      #  0xCD ->
    '\xce'      #  0xCE ->
    '\xcf'      #  0xCF ->
    '\xd0'      #  0xD0 ->
    '\xd1'      #  0xD1 ->
    '\xd2'      #  0xD2 ->
    '\xd3'      #  0xD3 ->
    '\xd4'      #  0xD4 ->
    '\xd5'      #  0xD5 ->
    '\xd6'      #  0xD6 ->
    '\xd7'      #  0xD7 ->
    '\xd8'      #  0xD8 ->
    '\xd9'      #  0xD9 ->
    '\xda'      #  0xDA ->
    '\xdb'      #  0xDB ->
    '\xdc'      #  0xDC ->
    '\xdd'      #  0xDD ->
    '\xde'      #  0xDE ->
    '\xdf'      #  0xDF ->
    '\xe0'      #  0xE0 ->
    '\xe1'      #  0xE1 ->
    '\xe2'      #  0xE2 ->
    '\xe3'      #  0xE3 ->
    '\xe4'      #  0xE4 ->
    '\xe5'      #  0xE5 ->
    '\xe6'      #  0xE6 ->
    '\xe7'      #  0xE7 ->
    '\xe8'      #  0xE8 ->
    '\xe9'      #  0xE9 ->
    '\xea'      #  0xEA ->
    '\xeb'      #  0xEB ->
    '\xec'      #  0xEC ->
    '\xed'      #  0xED ->
    '\xee'      #  0xEE ->
    '\xef'      #  0xEF ->
    '\xf0'      #  0xF0 ->
    '\xf1'      #  0xF1 ->
    '\xf2'      #  0xF2 ->
    '\xf3'      #  0xF3 ->
    '\xf4'      #  0xF4 ->
    '\xf5'      #  0xF5 ->
    '\xf6'      #  0xF6 ->
    '\xf7'      #  0xF7 ->
    '\xf8'      #  0xF8 ->
    '\xf9'      #  0xF9 ->
    '\xfa'      #  0xFA ->
    '\xfb'      #  0xFB ->
    '\xfc'      #  0xFC ->
    '\xfd'      #  0xFD ->
    '\xfe'      #  0xFE ->
    '\xff'      #  0xFF ->
)

### Encoding table
encoding_table = codecs.charmap_build(decoding_table)
