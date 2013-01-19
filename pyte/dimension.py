"""
This module exports a single class:

* `Dimension`: Late-evaluated dimension, forming the basis of the layout engine

It also exports a number of pre-defined dimensions:

* `PT`: PostScript point
* `INCH`: inch, equal to 72 PostScript points
* `MM`: millimeter
* `CM`: centimeter

"""

from copy import copy


__all__ = ['Dimension']


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
    """Late-evaluated dimension.

    The internal representations is in terms of PostScript points. A PostScript
    pointhich is defined as one 72th of an inch.
    The value of a dimension is only evaluated to a value in points when
    required by converting it to a float. Its value depends recursively on the
    evaluated values of the :class:`Dimension`s it depends upon."""

    # TODO: em, ex? (depends on context)
    def __init__(self, value=0, _plus_terms=None, _minus_terms=None, _factor=1):
        """Initialize a :class:`Dimension` at `value` points.
        You should *not* specify values for other arguments than `value`!"""
        self._value = value
        self._plus_terms = _plus_terms or []
        self._minus_terms = _minus_terms or []
        self._factor = _factor

    def __neg__(self):
        """Return the negative of this :class:`Dimension`"""
        inverse = copy(self)
        inverse._factor *= - 1
        return inverse

    def __iadd__(self, other):
        """Return this :class:`Dimension`, adding `other` (in place)"""
        this = copy(self)
        self.__init__(_plus_terms=[this, other])
        return self

    def __isub__(self, other):
        """Return this :class:`Dimension`, subtracting `other` (in place)"""
        this = copy(self)
        self.__init__(_plus_terms=[this], _minus_terms=[other])
        return self

    def __add__(self, other):
        """Return the sum of this :class:`Dimension` and `other`"""
        return self.__class__(_plus_terms=[self, other])

    __radd__ = __add__

    def __sub__(self, other):
        """Return the difference of this :class:`Dimension` and `other`"""
        return self.__class__(_plus_terms=[self], _minus_terms=[other])

    def __rsub__(self, other):
        return self.__class__(_plus_terms=[other], _minus_terms=[self])

    def __imul__(self, factor):
        """Multiply this :class:`Dimension` by `factor` (in place)"""
        self._factor *= factor
        return self

    def __mul__(self, factor):
        """Return the product of this :class:`Dimension` and `factor`"""
        result = copy(self)
        result._factor = self._factor * factor
        return result

    __rmul__ = __mul__

    def __truediv__(self, factor):
        """Return the quotient of this :class:`Dimension` and `factor`"""
        return self * (1.0 / factor)

    def __repr__(self):
        """Return a textual representation of the evaluated value"""
        return str(float(self)) + 'pt'

    def __float__(self):
        """Evaluate the value of this :class:`Dimension` in points"""
        total = (self._value + sum(map(float, self._plus_terms))
                             - sum(map(float, self._minus_terms)))
        return float(total) * self._factor


PT = Dimension(1)
INCH = 72*PT
MM = INCH / 25.4
CM = 10*MM
