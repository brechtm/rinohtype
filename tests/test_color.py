

import unittest


from rinoh.color import Color, HexColor, Gray


class TestColor(unittest.TestCase):

    def test_components(self):
        for r, g, b in [(1, 0.1, 0.8), (0.12, 0.0001, 0.008), (0.87, 0.4, 0.3)]:
            color = Color(r, g, b)
            self.assertEqual(color.r, r)
            self.assertEqual(color.g, g)
            self.assertEqual(color.b, b)
            self.assertEqual(color.a, 1.0)

        for r, g, b, a in [(0.5, 0.4, 0.3, 0.2), (0.2, 0.4, 0.6, 0.8)]:
            color = Color(r, g, b, a)
            self.assertEqual(color.r, r)
            self.assertEqual(color.g, g)
            self.assertEqual(color.b, b)
            self.assertEqual(color.a, a)

    def test_bad_value(self):
        for values in [(-0.1, 0, 0), (1, float('+inf'), 0), (0, 0, 1.01),
                       (0.5, 0.5, 0.5, 2.0)]:
            self.assertRaises(ValueError, Color, *values)

    def test_hex_color(self):
        color = HexColor('#1023F6')
        self.assertEqual(color.r, 0x10 / 255)
        self.assertEqual(color.g, 0x23 / 255)
        self.assertEqual(color.b, 0xF6 / 255)
        self.assertEqual(color.a, 1.0)
        self.assertEqual(repr(color), '#1023f6')

        color2 = HexColor('E30BCAD7')
        self.assertEqual(color2.r, 0xE3 / 255)
        self.assertEqual(color2.g, 0x0B / 255)
        self.assertEqual(color2.b, 0xCA / 255)
        self.assertEqual(color2.a, 0xD7 / 255)
        self.assertEqual(repr(color2), '#e30bcad7')

    def test_short_hex_color(self):
        color3 = HexColor('#A49')
        self.assertEqual(color3.r, 0xAA / 255)
        self.assertEqual(color3.g, 0x44 / 255)
        self.assertEqual(color3.b, 0x99 / 255)
        self.assertEqual(repr(color3), '#a49')

        color4 = HexColor('#2c6e')
        self.assertEqual(color4.r, 0x22 / 255)
        self.assertEqual(color4.g, 0xCC / 255)
        self.assertEqual(color4.b, 0x66 / 255)
        self.assertEqual(color4.a, 0xEE / 255)
        self.assertEqual(repr(color4), '#2c6e')

    def test_bad_hex_value(self):
        for hex_string in ['', 'zz0000', '0011223', 'a', '0011223344']:
            self.assertRaises(ValueError, HexColor, hex_string)

    def test_gray(self):
        for luminance in (1.0, 0.37, 0.987):
            gray = Gray(luminance)
            self.assertEqual(gray.r, luminance)
            self.assertEqual(gray.g, luminance)
            self.assertEqual(gray.b, luminance)
            self.assertEqual(gray.a, 1.0)

        for luminance, alpha in [(0.8, 0.2), (0.1, 0), (0.14159, 0.999)]:
            gray = Gray(luminance, alpha)
            self.assertEqual(gray.r, luminance)
            self.assertEqual(gray.g, luminance)
            self.assertEqual(gray.b, luminance)
            self.assertEqual(gray.a, alpha)
