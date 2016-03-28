

import unittest


from rinoh.dimension import PT, INCH


class TestDimension(unittest.TestCase):

    # test operators

    def test_addition(self):
        self.assertEqual(100*PT + 10, 110)
        self.assertEqual(100*PT + 10*PT, 110)
        self.assertEqual(100 + 10*PT,  110)
        self.assertEqual(1*INCH + 8*PT, 80)

    def test_subtraction(self):
        self.assertEqual(100*PT - 10, 90)
        self.assertEqual(100*PT - 10*PT, 90)
        self.assertEqual(100 - 10*PT, 90)
        self.assertEqual(1*INCH - 2*PT, 70)

    def test_multiplication(self):
        self.assertEqual(3 * 30*PT, 90)
        self.assertEqual(30*PT * 3, 90)

    def test_division(self):
        self.assertEqual(30*PT / 5, 6)

    def test_grow(self):
        a = 20*PT
        a.grow(50)
        self.assertEqual(a, 70)
        b = 20*PT
        b.grow(30*PT)
        self.assertEqual(b, 50)
        c = 100*PT
        c.grow(-50)
        self.assertEqual(c, 50)
        d = 100*PT
        d.grow(-30*PT)
        self.assertEqual(d, 70)

    def test_negation(self):
        self.assertEqual(-20*PT, -20)

    # test late evaluation

    def test_late_addition(self):
        a = 10*PT
        b = a + 5*PT
        a.grow(2)
        self.assertEqual(b, 17)

    def test_late_subtraction(self):
        a = 10*PT
        b = a - 5*PT
        a.grow(2)
        self.assertEqual(b, 7)

    def test_late_multiplication(self):
        a = 10*PT
        b = a * 2
        a.grow(2)
        self.assertEqual(b, 24)

    def test_late_division(self):
        a = 10*PT
        b = a / 2
        a.grow(2)
        self.assertEqual(b, 6)
