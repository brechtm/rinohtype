# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .util import Decorator


__all__ = ['NamedDestination', 'NamedDestinationLink', 'HyperLink',
           'AnnotatedSpan', 'AnnotationLocation', 'AnnotationTransform',
           'destination_anchor']


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

    def __repr__(self):
        return f"{type(self).__name__}('{self.name}')"


class HyperLink(LinkAnnotation):
    type = 'URI'

    def __init__(self, target):
        self.target = target


class AnnotatedSpan(Decorator):
    def __init__(self, span, anchor=None, link=None):
        super().__init__(span)
        self.anchor_annotation = anchor
        self.link_annotation = link


class AnnotationLocation(object):
    def __init__(self, annotation, left, top, width, height):
        self.annotation = annotation
        self.left = left
        self.top = top
        self.width = width
        self.height = height


class AnnotationTransform(object):
    """Affine transform for annotation locations

    Annotation coordinates have their origin in the top-left corner of a
    container, with the y axis pointing down. This transform maps coordinates
    in a container's coordinate system to those of its parent container,
    including sideways rotations.

    """

    def __init__(self, a=1, b=0, c=0, d=1, e=0, f=0):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    @classmethod
    def from_container(cls, left, top, width, height, sideways=None):
        """Create the transform for a container's annotation coordinates"""
        left, top = float(left), float(top)
        if sideways == 'left':
            return cls(0, 1, -1, 0, left + float(height), top)
        elif sideways == 'right':
            return cls(0, -1, 1, 0, left, top + float(width))
        else:
            return cls(1, 0, 0, 1, left, top)

    def compose(self, inner):
        """Return the transform that applies `inner` first, then this one"""
        return self.__class__(
            self.a * inner.a + self.c * inner.b,
            self.b * inner.a + self.d * inner.b,
            self.a * inner.c + self.c * inner.d,
            self.b * inner.c + self.d * inner.d,
            self.a * inner.e + self.c * inner.f + self.e,
            self.b * inner.e + self.d * inner.f + self.f)

    def apply(self, annotation_location):
        """Transform `annotation_location` to the parent's coordinates"""
        left, top = annotation_location.left, annotation_location.top
        # Most transforms only translate; skip the corner calculations then
        if self.a == 1 and self.b == 0 and self.c == 0 and self.d == 1:
            return annotation_location.__class__(
                annotation_location.annotation, left + self.e, top + self.f,
                annotation_location.width, annotation_location.height)
        width = annotation_location.width or 0
        height = annotation_location.height or 0
        corners = ((left, top), (left + width, top),
                   (left, top + height), (left + width, top + height))
        xs = [self.a * x + self.c * y + self.e for x, y in corners]
        ys = [self.b * x + self.d * y + self.f for x, y in corners]
        return annotation_location.__class__(
            annotation_location.annotation, min(xs), min(ys),
            abs(self.a) * width + abs(self.c) * height,
            abs(self.b) * width + abs(self.d) * height)


def destination_anchor(annotation_location, sideways=None):
    """Return the destination corner that is top-left on the displayed page"""
    left, top = annotation_location.left, annotation_location.top
    width = annotation_location.width or 0
    height = annotation_location.height or 0
    if sideways == 'right':         # page rotated clockwise
        return left, top + height
    elif sideways == 'left':        # page rotated counterclockwise
        return left + width, top
    return left, top
