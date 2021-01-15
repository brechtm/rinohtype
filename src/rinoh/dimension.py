# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Classes for expressing dimensions: lengths, widths, line thickness, etc.

Each dimension is expressed in terms of a unit. Several common units are are
defined here as constants. To create a new dimension, multiply number with
a unit::

    height = 100*PT
    width = 50*PERCENT

Fractional dimensions are evaluated within the context they are defined in. For
example, the width of a :class:`Flowable` is evaluated with respect to the
total width available to it.

"""

import inspect
import re
import sys

from .attribute import AcceptNoneAttributeType, ParseError
from collections import OrderedDict
from token import PLUS, MINUS, NUMBER, NAME, OP


__all__ = ['Dimension', 'PT', 'PICA', 'INCH', 'MM', 'CM',
           'PERCENT', 'QUARTERS']


class DimensionType(type):
    """Maps comparison operators to their equivalents in :class:`float`"""

    def __new__(mcs, name, bases, cls_dict):
        """Return a new class with predefined comparison operators"""
        for method_name in ('__lt__', '__le__', '__gt__', '__ge__'):
            if method_name not in cls_dict:
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


class DimensionBase(AcceptNoneAttributeType, metaclass=DimensionType):
    """Late-evaluated dimension

    The result of mathematical operations on dimension objects is not a
    statically evaluated version, but rather stores references to the operator
    arguments. The result is only evaluated to a number on conversion to a
    :class:`float`.

    The internal representation is in terms of PostScript points. A PostScript
    point is equal to one 72nd of an inch.

    """

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

    def __abs__(self):
        """Return the absolute value of this dimension (in points)."""
        return abs(float(self))

    def __float__(self):
        """Evaluate the value of this dimension in points."""
        raise NotImplementedError

    def __eq__(self, other):
        try:
            return float(self) == float(other)
        except (ValueError, TypeError):
            return False

    @classmethod
    def check_type(cls, value):
        return (super().check_type(value) or isinstance(value, Fraction)
                or value == 0)

    REGEX = re.compile(r"""(?P<value>
                             [+-]?         # optional sign
                             \d*\.?\d+     # integer or float value
                           )
                           \s*             # optional space between value & unit
                           (?P<unit>
                             [a-z%/0-9]*   # unit (can be an empty string)
                           )
                       """, re.IGNORECASE | re.VERBOSE)

    @classmethod
    def from_tokens(cls, tokens, source):
        sign = 1
        if tokens.next.exact_type in (PLUS, MINUS):
            sign = -1 if next(tokens).exact_type == MINUS else 1
        token = next(tokens)
        if token.type != NUMBER:
            raise ParseError('Expecting a number')
        try:
            value = int(token.string)
        except ValueError:
            value = float(token.string)
        if tokens.next and tokens.next.type in (NAME, OP):
            unit_string = next(tokens).string
        elif value == 0:
            return Dimension(0)
        else:
            raise ParseError('Expecting a dimension unit')
        if unit_string == '/':
            unit_string += next(tokens).string
        try:
            unit = DimensionUnitBase.all[unit_string.lower()]
        except KeyError:
            raise ParseError("'{}' is not a valid dimension unit"
                             .format(unit_string))
        return sign * value * unit

    @classmethod
    def doc_format(cls):
        return ('a numeric value followed by a unit ({})'
                .format(', '.join('``{}``'.format(unit)
                                  for unit in DimensionUnitBase.all)))

    def to_points(self, total_dimension):
        """Convert this dimension to PostScript points

        If this dimension is context-sensitive, it will be evaluated relative
        to ``total_dimension``. This can be the total width available to a
        flowable, for example.

        Args:
            total_dimension (int, float or Dimension): the dimension providing
                context to a context-sensitive dimension. If int or float, it
                is assumed to have a unit of PostScript points.

        Returns:
            float: this dimension in PostScript points

        """
        return float(self)


class Dimension(DimensionBase):
    """A simple dimension

    Args:
        value (int or float): the magnitude of the dimension
        unit (DimensionUnit): the unit this dimension is expressed in.
            Default: :data:`PT`.

    """

    # TODO: em, ex? (depends on context)
    def __init__(self, value=0, unit=None):
        self._value = value
        self._unit = unit or PT

    def __str__(self):
        number = '{:.2f}'.format(self._value).rstrip('0').rstrip('.')
        return '{}{}'.format(number, self._unit.label)

    def __repr__(self):
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if obj is self._unit:
                return '{}*{}'.format(self._value, name)
        else:
            raise ValueError

    def __float__(self):
        return float(self._value) * self._unit.points_per_unit

    def grow(self, value):
        """Grow this dimension (in-place)

        The ``value`` is interpreted as a magnitude expressed in the same unit
        as this dimension.

        Args:
            value (int or float): the amount to add to the magnitude of this
                dimension

        Returns:
            :class:`Dimension`: this (growed) dimension itself

        """
        self._value += float(value)
        return self


class DimensionAddition(DimensionBase):
    """The sum of a set of dimensions

    Args:
        addends (`Dimension`\\ s):

    """

    def __init__(self, *addends):
        self.addends = list(addends)

    def __float__(self):
        return sum(map(float, self.addends or (0.0, )))


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


class DimensionMaximum(DimensionBase):
    def __init__(self, *dimensions):
        self.dimensions = dimensions

    def __float__(self):
        return max(*(float(dimension) for dimension in self.dimensions))


class DimensionUnitBase(object):
    all = OrderedDict()

    def __init__(self, label):
        self.label = label
        self.all[label] = self


class DimensionUnit(DimensionUnitBase):
    """A unit to express absolute dimensions in

    Args:
        points_per_unit (int or float): the number of PostScript points that
            fit in one unit
        label (str): label for the unit

    """

    def __init__(self, points_per_unit, label):
        super().__init__(label)
        self.points_per_unit = float(points_per_unit)

    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__, self.points_per_unit,
                                   repr(self.label))

    def __rmul__(self, value):
        return Dimension(value, self)


# Units

PT = DimensionUnit(1, 'pt')                 #: PostScript points
INCH = DimensionUnit(72*PT, 'in')           #: imperial/US inch
PICA = DimensionUnit(1 / 6 * INCH, 'pc')    #: computer pica
MM = DimensionUnit(1 / 25.4 * INCH, 'mm')   #: millimeter
CM = DimensionUnit(10*MM, 'cm')             #: centimeter


class Fraction(DimensionBase):
    """A context-sensitive dimension

    This fraction is multiplied by the reference dimension when evaluating it
    using :meth:`to_points`.

    Args:
        numerator (int or float): the numerator of the fraction
        unit (FractionUnit): the fraction unit

    """

    def __init__(self, numerator, unit):
        self._numerator = numerator
        self._unit = unit

    def __str__(self):
       number = '{:.2f}'.format(self._numerator).rstrip('0').rstrip('.')
       return '{}{}'.format(number, self._unit.label)

    __eq__ = AcceptNoneAttributeType.__eq__

    def to_points(self, total_dimension):
        fraction = self._numerator / self._unit.denominator
        return fraction * float(total_dimension)


class FractionUnit(DimensionUnitBase):
    """A unit to express relative dimensions in

    Args:
        denominator (int or float): the number of parts to divide the whole in
        label (str): label for the unit

    """

    def __init__(self, denominator, label):
        super().__init__(label)
        self.denominator = denominator

    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__, self.denominator,
                                   repr(self.label))

    def __rmul__(self, nominator):
        return Fraction(nominator, self)


PERCENT = FractionUnit(100, '%')            #: fraction of 100
QUARTERS = FractionUnit(4, '/4')            #: fraction of 4
