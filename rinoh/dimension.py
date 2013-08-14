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

from copy import copy


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


class Dimension(object, metaclass=DimensionType):
    """Late-evaluated dimension. The result of mathematical operations on
    dimension objects is not a statically evaluated version, but rather stores
    references to the operator arguments. The result is only evaluated to a
    number on conversion to a :class:`float`.

    The internal representation is in terms of PostScript points. A PostScript
    point is equal to one 72th of an inch."""

    # TODO: em, ex? (depends on context)
    def __init__(self, value=0, _plus_terms=None, _minus_terms=None, _factor=1):
        """Initialize a dimension at `value` points.
        You should *not* specify values for other arguments than `value`!"""
        self._value = value
        self._plus_terms = _plus_terms or []
        self._minus_terms = _minus_terms or []
        self._factor = _factor

    def __neg__(self):
        """Return the negative of this dimension."""
        inverse = copy(self)
        inverse *= - 1
        return inverse

    def __iadd__(self, other):
        """Return this dimension after adding `other` (in place)."""
        this = copy(self)
        self.__init__(_plus_terms=[this, other])
        return self

    def __isub__(self, other):
        """Return this dimension after subtracting `other` (in place)."""
        this = copy(self)
        self.__init__(_plus_terms=[this], _minus_terms=[other])
        return self

    def __add__(self, other):
        """Return the sum of this dimension and `other`."""
        return self.__class__(_plus_terms=[self, other])

    __radd__ = __add__

    def __sub__(self, other):
        """Return the difference of this dimension and `other`."""
        return self.__class__(_plus_terms=[self], _minus_terms=[other])

    def __rsub__(self, other):
        """Return the difference of `other` and this dimension."""
        return self.__class__(_plus_terms=[other], _minus_terms=[self])

    def __imul__(self, factor):
        """Return this dimension after multiplying it by `factor` (in place)."""
        self._factor *= factor
        return self

    def __mul__(self, factor):
        """Return the product of this dimension and `factor`."""
        return self.__class__(_plus_terms=[self], _factor=factor)

    __rmul__ = __mul__

    def __truediv__(self, factor):
        """Return the quotient of this dimension and `factor`."""
        return self * (1.0 / factor)

    def __itruediv__(self, factor):
        """Return this dimension after dividing it by `factor` (in place)."""
        self._factor /= factor
        return self

    def __repr__(self):
        """Return a textual representation of the evaluated value."""
        return str(float(self)) + 'pt'

    def __float__(self):
        """Evaluate the value of this dimension in points."""
        total = (self._value + sum(map(float, self._plus_terms))
                             - sum(map(float, self._minus_terms)))
        return float(total) * self._factor

    def __abs__(self):
        """Return the absolute value of this dimension (in points)."""
        return abs(float(self))


# Units

PT = Dimension(1)
INCH = 72*PT
MM = INCH / 25.4
CM = 10*MM
