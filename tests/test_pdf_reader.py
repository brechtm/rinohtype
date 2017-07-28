# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from io import BytesIO

from rinoh.backend.pdf import cos
from rinoh.backend.pdf.reader import PDFObjectReader


def test_read_boolean():
    def test_boolean(bytes_boolean, boolean):
        reader = PDFObjectReader(BytesIO(bytes_boolean))
        result = reader.next_item()
        assert isinstance(result, cos.Boolean) and bool(result) == boolean

    test_boolean(b'true', True)
    test_boolean(b'false', False)


def test_read_integer():
    def test_integer(bytes_integer, integer):
        reader = PDFObjectReader(BytesIO(bytes_integer))
        result = reader.next_item()
        assert isinstance(result, cos.Integer) and result == integer

    test_integer(b'123', 123)
    test_integer(b'43445', 43445)
    test_integer(b'+17', 17)
    test_integer(b'-98', -98)
    test_integer(b'0', 0)


def test_read_real():
    def test_real(bytes_real, real):
        reader = PDFObjectReader(BytesIO(bytes_real))
        result = reader.next_item()
        assert isinstance(result, cos.Real) and result == real

    test_real(b'34.5', 34.5)
    test_real(b'-3.62', -3.62)
    test_real(b'+123.6', 123.6)
    test_real(b'4.', 4.0)
    test_real(b'-.002', -.002)
    test_real(b'0.0', 0.0)


def test_read_name():
    def test_name(bytes_name, unicode_name):
        reader = PDFObjectReader(BytesIO(bytes_name))
        result = reader.next_item()
        assert isinstance(result, cos.Name) and str(result) == unicode_name

    test_name(b'/Adobe#20Green', 'Adobe Green')
    test_name(b'/PANTONE#205757#20CV', 'PANTONE 5757 CV')
    test_name(b'/paired#28#29parentheses', 'paired()parentheses')
    test_name(b'/The_Key_of_F#23_Minor', 'The_Key_of_F#_Minor')
    test_name(b'/A#42', 'AB')


def test_read_dictionary():
    input = b"""
    << /Type          /Example
       /Subtype       /DictionaryExample
       /Version       0.01
       /IntegerItem   12
       /StringItem    (a string)
       /Subdictionary  << /Item1         0.4
                          /Item2         true
                          /LastItem      (not!)
                          /VeryLastItem  (OK)
                       >>
    >>"""
    reader = PDFObjectReader(BytesIO(input))
    result = reader.next_item()
    expected = cos.Dictionary([('Type', cos.Name('Example')),
                               ('Subtype', cos.Name('DictionaryExample')),
                               ('Version', cos.Real(0.01)),
                               ('IntegerItem', cos.Integer(12)),
                               ('StringItem', cos.String('a string')),
                               ('Subdictionary', cos.Dictionary(
                                   [('Item1', cos.Real(0.4)),
                                    ('Item2', cos.Boolean(True)),
                                    ('LastItem', cos.String('not!')),
                                    ('VeryLastItem', cos.String('OK'))]))])
    assert isinstance(result, cos.Dictionary)
    assert dict(result) == dict(expected)
