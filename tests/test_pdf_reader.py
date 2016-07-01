
import pytest

from io import BytesIO

from rinoh.backend.pdf.reader import PDFObjectReader


def test_read_name():
    def test_name(bytes_name, unicode_name):
        reader = PDFObjectReader(BytesIO(bytes_name))
        name = reader.read_name()
        assert str(name) == unicode_name

    test_name(b'Adobe#20Green', 'Adobe Green')
    test_name(b'PANTONE#205757#20CV', 'PANTONE 5757 CV')
    test_name(b'paired#28#29parentheses', 'paired()parentheses')
    test_name(b'The_Key_of_F#23_Minor', 'The_Key_of_F#_Minor')
    test_name(b'A#42', 'AB')
