
from io import BytesIO

from .attribute import Attribute, OverrideDefault
from .color import BLACK, Color
from .dimension import Dimension, PT
from .flowable import LabeledFlowable
from .image import InlineImage
from .inline import InlineFlowable, InlineFlowableStyle
from .number import Label, NumberFormat, NumberStyle
from .paragraph import Paragraph, ParagraphBase, ParagraphStyle
from .text import MixedStyledText, Tab


__all__ = ['DisplayEquation', 'EquationLabel', 'Equation']


try:
    import ziamath
    import cairosvg
except ImportError:
    ziamath = None
    cairosvg = None

MATH_ENABLED = None not in (ziamath, cairosvg)


class EquationLabelStyle(ParagraphStyle, NumberStyle):
    number_format = OverrideDefault(NumberFormat.NUMBER)


class EquationLabel(ParagraphBase, Label):
    style_class = EquationLabelStyle

    @property
    def referenceable(self):
        return self.parent

    def text(self, container):
        try:
            label = [self.number(container)]
        except KeyError:
            label = []
        return MixedStyledText(label, parent=self)


class DisplayEquation(LabeledFlowable):

    category = 'equation'

    def __init__(self, latex_equation, custom_label=None,
                 id=None, style=None, parent=None, source=None):
        paragraph = Paragraph(Tab() + Equation(latex_equation, inline=False))
        label = EquationLabel()
        super().__init__(label, paragraph, id=id, style=style, parent=parent)


class EquationStyle(InlineFlowableStyle):
    font_size = Attribute(Dimension, 9*PT, 'Height of characters')
    font_color = Attribute(Color, BLACK, 'Color of the font')


class Equation(InlineFlowable):
    style_class = EquationStyle

    def __init__(self, latex_equation, inline=True, id=None, style=None, parent=None, source=None):
        super().__init__(id=id, style=style, parent=parent, source=source)
        self.latex_equation = latex_equation
        self.inline = inline

    def fallback_to_parent(self, attribute):
        return attribute in ('font_size', 'font_color')

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        if MATH_ENABLED:
            size = float(self.get_style('font_size', flowable_target))
            color = str(self.get_style('font_color', flowable_target))
            self._math = ziamath.Latex(self.latex_equation, inline=self.inline,
                                       size=size, color=color)
            self.baseline = - self._math.getyofst() * PT

    def render(self, container, descender, state, space_below=0, **kwargs):
        if not MATH_ENABLED:
            self.warn("Math rendering requires the 'ziamath' and "
                      "'cairosvg' packages to be installed.", container)
            return 0, 0, 0
        pdf_file = BytesIO(cairosvg.svg2pdf(self._math.svg()))
        inline_image = InlineImage(pdf_file)
        return inline_image.render(container, descender, state, **kwargs)
