
from io import BytesIO

from .dimension import PT
from .flowable import LabeledFlowable
from .image import InlineImage
from .inline import InlineFlowable
from .number import Label, NumberStyle, format_number
from .paragraph import Paragraph, ParagraphBase, ParagraphStyle, StaticParagraph
from .reference import Reference
from .text import MixedStyledText, SingleStyledText, Tab


__all__ = ['Equation', 'EquationLabel', 'InlineEquation']


try:
    import ziamath
    import cairosvg
except ImportError:
    ziamath = None
    cairosvg = None

MATH_ENABLED = None not in (ziamath, cairosvg)


class EquationLabelStyle(ParagraphStyle, NumberStyle):
    pass


class EquationLabel(ParagraphBase, Label):
    style_class = EquationLabelStyle

    @property
    def referenceable(self):
        return self.parent

    def text(self, container):
        return MixedStyledText(self.number(container), parent=self)


class Equation(LabeledFlowable):

    category = 'equation'

    def __init__(self, latex_equation, custom_label=None,
                 id=None, style=None, parent=None, source=None):
        paragraph = Paragraph(Tab() + InlineEquation(latex_equation, inline=False))
        label = EquationLabel()
        super().__init__(label, paragraph, id=id, style=style, parent=parent)


class InlineEquation(InlineFlowable):
    def __init__(self, latex_equation, inline=True, id=None, style=None, parent=None, source=None):
        if not MATH_ENABLED:
            equation = baseline = None
        else:
            equation = ziamath.Latex(latex_equation, inline=inline)
            baseline = - equation.getyofst() * PT
        super().__init__(baseline, id, style, parent, source)
        self.latex_equation = latex_equation
        self.equation = equation

    def render(self, container, descender, state, space_below=0, **kwargs):
        if self.equation is None:
            self.warn("Math rendering requires the 'ziamath' and "
                      "'cairosvg' packages to be installed.", container)
            return 0, 0, 0
        else:
            pdf_file = BytesIO(cairosvg.svg2pdf(self.equation.svg()))
            inline_image = InlineImage(pdf_file, baseline=self.baseline)
            return inline_image.render(container, descender, state, **kwargs)
