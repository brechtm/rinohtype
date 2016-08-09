# This file is part of rinohtype, the Python document preparation system.
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


class AnchorAnnotation(Annotation):
    pass


class NamedDestination(AnchorAnnotation):
    type = 'NamedDestination'

    def __init__(self, *names):
        self.names = names


class LinkAnnotation(Annotation):
    pass


class NamedDestinationLink(LinkAnnotation):
    type = 'NamedDestinationLink'

    def __init__(self, name):
        self.name = name


class HyperLink(LinkAnnotation):
    type = 'URI'

    def __init__(self, target):
        self.target = target


class AnnotatedSpan(Decorator):
    def __init__(self, span, anchor=None, link=None):
        super().__init__(span)
        self.anchor_annotation = anchor
        self.link_annotation = link


from .text import MixedStyledText


class AnnotatedText(MixedStyledText):
    def __init__(self, text_or_items, annotation, style=None, parent=None):
        super().__init__(text_or_items, style=style, parent=parent)
        self.annotation = annotation

    def spans(self, container):
        ann = self.annotation
        anchor = ann if isinstance(ann, AnchorAnnotation) else None
        link = ann if isinstance(ann, LinkAnnotation) else None
        for span in super().spans(container):
            if isinstance(span, AnnotatedSpan):
                if anchor:
                    assert span.anchor_annotation is None
                    span.anchor_annotation = anchor
                elif link:
                    assert span.link_annotation is None
                    span.link_annotation = link
                yield span
            else:
                yield AnnotatedSpan(span, anchor=anchor, link=link)
