# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .util import Decorator


__all__ = ['NamedDestination', 'NamedDestinationLink', 'HyperLink',
           'AnnotatedSpan', 'AnnotatedText']


class Annotation(object):
    pass


class NamedDestination(Annotation):
    type = 'NamedDestination'

    def __init__(self, name):
        self.name = name


class NamedDestinationLink(Annotation):
    type = 'NamedDestinationLink'

    def __init__(self, name):
        self.name = name


class HyperLink(Annotation):
    type = 'URI'

    def __init__(self, target):
        self.target = target


class AnnotatedSpan(Decorator):
    def __init__(self, span, annotation):
        super().__init__(span)
        self.annotation = annotation


from .text import MixedStyledText


class AnnotatedText(MixedStyledText):
    def __init__(self, text_or_items, annotation, style=None, parent=None):
        super().__init__(text_or_items, style=style, parent=parent)
        self.annotation = annotation

    def spans(self, container):
        return (AnnotatedSpan(span, self.annotation)
                for item in self for span in item.spans(container))
