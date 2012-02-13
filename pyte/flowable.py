
from .style import Style, Styled
from .unit import pt


class FlowableStyle(Style):
    attributes = {'spaceAbove': 0 * pt,
                  'spaceBelow': 0 * pt}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Flowable(Styled):
    style_class = FlowableStyle

    def __init__(self, style=None):
        super().__init__(style)

    @property
    def document(self):
        try:
            return self._document
        except AttributeError:
            return self.parent.document

    @document.setter
    def document(self, document):
        self._document = document

    def flow(self, container, offset=0, continued=False):
        self.parent = container
        if not continued:
            space_above = float(self.get_style('spaceAbove'))
        else:
            space_above = 0
        space_below = float(self.get_style('spaceBelow'))
        flowable_height = self.render(container.canvas, offset + space_above)
        return space_above + flowable_height + space_below

    def render(self, canvas, offset=0):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


