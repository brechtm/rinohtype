# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
This module exports a single class:

* :class:`Dimension`: Late-evaluated dimension, forming the basis of the layout
  engine

It also exports a number of pre-defined units:

* :const:`PT`: PostScript point
* :const:`INCH`: Inch, equal to 72 PostScript points
* :const:`MM`: Millimeter
* :const:`CM`: Centimeter

"""


__all__ = ['Dimension', 'PT', 'INCH', 'MM', 'CM']


class DimensionType(type):
    """Maps comparison operators to their equivalents in :class:`float`"""

    def __new__(mcs, name, bases, cls_dict):
        """Return a new class with predefined comparison operators"""
        for method_name in ('__lt__', '__le__', '__gt__', '__ge__',
                            '__eq__', '__ne__'):
            cls_dict[method_name] = mcs._make_operator(method_name)
        return type.__new__(mcs, name, bases, cls_dict)

    @staticmethod
    def _make_operator(method_name):
        """Return an operator method that takes parameters of type
        :class:`Dimension`, evaluates them, and delegates to the :class:`float`
        operator with name `method_name`"""
        def operator(self, other):
            """Operator delegating to the :class:`float` method `method_name`"""
            float_operator = getattr(float, method_name)
            return float_operator(float(self), float(other))
        return operator


class DimensionBase(object, metaclass=DimensionType):
    """Late-evaluated dimension. The result of mathematical operations on
    dimension objects is not a statically evaluated version, but rather stores
    references to the operator arguments. The result is only evaluated to a
    number on conversion to a :class:`float`.

    The internal representation is in terms of PostScript points. A PostScript
    point is equal to one 72th of an inch."""

    def __neg__(self):
        return DimensionMultiplication(self, -1)

    def __add__(self, other):
        """Return the sum of this dimension and `other`."""
        return DimensionAddition(self, other)

    __radd__ = __add__

    def __sub__(self, other):
        """Return the difference of this dimension and `other`."""
        return DimensionSubtraction(self, other)

    def __rsub__(self, other):
        """Return the difference of `other` and this dimension."""
        return DimensionSubtraction(other, self)

    def __mul__(self, factor):
        """Return the product of this dimension and `factor`."""
        return DimensionMultiplication(self, factor)

    __rmul__ = __mul__

    def __truediv__(self, divisor):
        """Return the quotient of this dimension and `divisor`."""
        return DimensionMultiplication(self, 1.0 / divisor)

    def __repr__(self):
        """Return a textual representation of the evaluated value."""
        return str(float(self)) + 'pt'

    def __abs__(self):
        """Return the absolute value of this dimension (in points)."""
        return abs(float(self))

    def __float__(self):
        """Evaluate the value of this dimension in points."""
        raise NotImplementedError


class Dimension(DimensionBase):
    # TODO: em, ex? (depends on context)
    def __init__(self, value=0):
        """Initialize a dimension at `value` points."""
        self._value = value

    def __iadd__(self, other):
        self._value += other
        return self

    def __float__(self):
        return float(self._value)


class DimensionAddition(DimensionBase):
    def __init__(self, *addends):
        self.addends = addends

    def __float__(self):
        return sum(map(float, self.addends))


class DimensionSubtraction(DimensionBase):
    def __init__(self, minuend, subtrahend):
        self.minuend = minuend
        self.subtrahend = subtrahend

    def __float__(self):
        return float(self.minuend) - float(self.subtrahend)


class DimensionMultiplication(DimensionBase):
    def __init__(self, multiplicand, multiplier):
        self.multiplicand = multiplicand
        self.multiplier = multiplier

    def __float__(self):
        return float(self.multiplicand) * self.multiplier


# Units

PT = Dimension(1)
INCH = 72*PT
MM = INCH / 25.4
CM = 10*MM
