
from copy import copy


class Dimension(object): # internally always pt
    # TODO: em, ex? (depends on context)
    def __init__(self, value=0):
        self.__value = value
        self.__plusTerms = []
        self.__minusTerms = []
        self.__factor = 1

    def add(self, other):
        assert isinstance(other, Dimension)
        this = copy(self)
        self.__init__(0)
        self.__plusTerms = [this, other]

    def __add__(self, other):
        assert isinstance(other, Dimension)
        result = Dimension()
        result.__plusTerms = [self, other]
        return result

    __radd__ = __add__

    def __sub__(self, other):
        assert isinstance(other, Dimension)
        result = Dimension()
        result.__plusTerms = [self]
        result.__minusTerms = [other]
        return result

    __rsub__ = __sub__

    def __mul__(self, factor):
        result = copy(self)
        result.__factor = self.__factor * factor
        return result

    __rmul__ = __mul__

    def __truediv__(self, factor):
        return self * (1.0/factor)

    def __lt__(self, other):
        return float(self) < float(other)

    def __le__(self, other):
        return float(self) <= float(other)

    def __eq__(self, other):
        return float(self) == float(other)

    def __ne__(self, other):
        return float(self) != float(other)

    def __gt__(self, other):
        return float(self) > float(other)

    def __ge__(self, other):
        return float(self) >= float(other)

    def __copy__(self):
        result = Dimension()
        result.__value = self.__value
        result.__plusTerms = copy(self.__plusTerms)
        result.__minusTerms = copy(self.__minusTerms)
        result.__factor = self.__factor
        return result

    def __repr__(self):
        #return str(self.evaluate()) + 'pt' + "    " + hex(id(self))
        return str(self.evaluate()) + 'pt'

    def __float__(self):
        return float(self.evaluate())

    def evaluate(self):
        total = self.__value
        for term in self.__plusTerms:
            total += term.evaluate()
        for term in self.__minusTerms:
            total -= term.evaluate()
        return total * self.__factor

    def below(self, container):
        # TODO: icky!
        assert isinstance(container, Container)
        return self + container.bottom()


NIL = Dimension(0)
