# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .util import Decorator
from .style import PARENT_STYLE
from .text import MixedStyledText


__all__ = ['Annotation', 'HyperLink', 'AnnotatedSpan', 'AnnotatedText']


class Annotation(object):
    pass


class HyperLink(Annotation):
    type = 'URI'

    def __init__(self, target):
        self.target = target


class AnnotatedSpan(Decorator):
    def __init__(self, span, annotation):
        super().__init__(span)
        self.annotation = annotation


class AnnotatedText(MixedStyledText):
    def __init__(self, text_or_items, annotation, style=PARENT_STYLE,
                 parent=None):
        super().__init__(text_or_items, style=style, parent=parent)
        self.annotation = annotation

    def spans(self):
        return (AnnotatedSpan(span, self.annotation)
                for item in self for span in item.spans())


