

import unittest


from pyte.dimension import Dimension, PT, INCH


class TestDimension(unittest.TestCase):

    # utility methods

    def assertEqualAndIsNeither(self, operation, term1, term2, reference):
        result = operation(term1, term2)
        self.assertEqual(result, reference)
        self.assertIsNot(result, term1)
        self.assertIsNot(result, term2)

    def assertEqualAndIsFirst(self, operation, term1, term2, reference):
        result = operation(term1, term2)
        self.assertEqual(result, reference)
        self.assertIs(result, term1)

    # test operators

    def test_addition(self):
        op = lambda a, b: a + b
        self.assertEqualAndIsNeither(op, 100*PT, 10, 110)
        self.assertEqualAndIsNeither(op, 100*PT, 10*PT, 110)
        self.assertEqualAndIsNeither(op, 100, 10*PT,  110)
        self.assertEqualAndIsNeither(op, 1*INCH, 8*PT, 80)

    def test_subtraction(self):
        op = lambda a, b: a - b
        self.assertEqualAndIsNeither(op, 100*PT, 10, 90)
        self.assertEqualAndIsNeither(op, 100*PT, 10*PT, 90)
        self.assertEqualAndIsNeither(op, 100, 10*PT, 90)
        self.assertEqualAndIsNeither(op, 1*INCH, 2*PT, 70)

    def test_multiplication(self):
        op = lambda a, b: a * b
        self.assertEqualAndIsNeither(op, 3, 30*PT, 90)
        self.assertEqualAndIsNeither(op, 30*PT, 3, 90)

    def test_division(self):
        op = lambda a, b: a / b
        self.assertEqualAndIsNeither(op, 30*PT, 5, 6)

    def test_inplace_addition(self):
        def op(a, b):
            a += b
            return a
        self.assertEqualAndIsFirst(op, 20*PT, 50, 70)
        self.assertEqualAndIsFirst(op, 20*PT, 30*PT, 50)

    def test_inplace_subtraction(self):
        def op(a, b):
            a -= b
            return a
        self.assertEqualAndIsFirst(op, 100*PT, 50, 50)
        self.assertEqualAndIsFirst(op, 100*PT, 30*PT, 70)

    def test_inplace_multiplication(self):
        def op(a, b):
            a *= b
            return a
        self.assertEqualAndIsFirst(op, 20*PT, 3, 60)

    def test_inplace_division(self):
        def op(a, b):
            a /= b
            return a
        self.assertEqualAndIsFirst(op, 60*PT, 3, 20)

    def test_negation(self):
        op = lambda a, _: - a
        self.assertEqualAndIsNeither(op, 20*PT, None, -20)

    # test late evaluation

    def test_late_addition(self):
        def op(a, b):
            result = a + b
            a += 2*PT
            return result
        self.assertEqualAndIsNeither(op, 10*PT, 5*PT, 17)

    def test_late_subtraction(self):
        def op(a, b):
            result = a - b
            a += 2*PT
            return result
        self.assertEqualAndIsNeither(op, 10*PT, 5*PT, 7)

    def test_late_multiplication(self):
        def op(a, b):
            result = a * b
            a += 2*PT
            return result
        self.assertEqualAndIsNeither(op, 10*PT, 2, 24)

    def test_late_division(self):
        def op(a, b):
            result = a / b
            a += 2*PT
            return result
        self.assertEqualAndIsNeither(op, 10*PT, 2, 6)
