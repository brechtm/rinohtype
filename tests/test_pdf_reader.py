

import unittest


from pyte.backend.pdf.reader import PDFObjectReader


class TestPDFReader(unittest.TestCase):

    def test_read_name(self):
        def test_name(bytes_name, unicode_name):
            name = read_name(BytesIO(bytes_name))
            self.assertEqual(str(name), unicode_name)

        test_name(b'Adobe#20Green Blue', 'Adobe Green Blue')
        test_name(b'PANTONE#205757#20CV', 'PANTONE 5757 CV')
        test_name(b'paired#28#29parentheses', 'paired()parentheses')
        test_name(b'The_Key_of_F#23_Minor', 'The_Key_of_F#_Minor')
        test_name(b'A#42', 'AB')
