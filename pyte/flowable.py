
from .style import Style
from .unit import pt


class FlowableStyle(Style):
    attributes = {'spaceAbove': 0 * pt,
                  'spaceBelow': 0 * pt}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Flowable(object):
    def __init__(self):
        pass

    def render(self, canvas, offset=0):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


