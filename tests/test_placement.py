# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


"""Tests for :meth:`rinoh.layout.Container.place`

These tests inspect the operators that are written to the page canvas so that
we can verify in which order a container's own contents, the sideways
transform and its children are placed.

"""

from types import SimpleNamespace

from rinoh.backend.pdf import Canvas
from rinoh.layout import Container


MARKER = 'container contents'
CHILD = 'child contents'
ANNOTATION = 'annotation'
ANNOTATION_LEFT = 10
ANNOTATION_TOP = 5
ANNOTATION_WIDTH = 20
ANNOTATION_HEIGHT = 3


def make_container(sideways=None, left=0, top=0, width=100, height=50):
    """A minimal stand-in for :class:`rinoh.layout.Container`

    Its own canvas holds a marker so that we can tell where its contents end
    up in the page canvas' operator stream.

    """
    own_canvas = Canvas()
    own_canvas.print(MARKER)
    own_canvas.annotate(ANNOTATION, ANNOTATION_LEFT, ANNOTATION_TOP,
                        ANNOTATION_WIDTH, ANNOTATION_HEIGHT)

    def place_children(page_canvas, offsets):
        page_canvas.print(CHILD)
        place_children.offsets = offsets

    return SimpleNamespace(left=left, top=top, width=width, height=height,
                           sideways=sideways, _canvas=own_canvas,
                           place_children=place_children)


def place(container):
    page_canvas = Canvas()
    Container.place(container, page_canvas, ())
    return page_canvas


def placement(container):
    return place(container).getvalue().splitlines()


def offset_fields(offsets):
    offset, = offsets
    return (offset.a, offset.b, offset.c, offset.d, offset.e, offset.f)


def annotation_location(page_canvas):
    location, = page_canvas.annotations
    return (location.left, location.top, location.width, location.height)


def test_not_sideways():
    container = make_container(left=10, top=20)
    page_canvas = place(container)
    lines = page_canvas.getvalue().splitlines()
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']
    assert container._canvas is None
    assert offset_fields(container.place_children.offsets) == (1, 0, 0, 1,
                                                              10, 20)
    assert annotation_location(page_canvas) == (20, 25, 20, 3)


def test_sideways_left():
    container = make_container('left', left=10, top=20, width=100, height=50)
    page_canvas = place(container)
    lines = page_canvas.getvalue().splitlines()
    # the container's own contents must be written after the sideways
    # transform (the old, buggy ordering wrote them right after the first
    # translate operator, that is, at index 2)
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     b'1 0 0 1 50.000000 0.000000 cm',
                     b'0.000000 -1.000000 1.000000 0.000000 0 0 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']
    assert container._canvas is None
    assert offset_fields(container.place_children.offsets) == (0, 1, -1, 0,
                                                              60, 20)
    assert annotation_location(page_canvas) == (52, 30, 3, 20)


def test_sideways_right():
    container = make_container('right', left=10, top=20, width=100, height=50)
    page_canvas = place(container)
    lines = page_canvas.getvalue().splitlines()
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     b'1 0 0 1 0.000000 -100.000000 cm',
                     b'0.000000 1.000000 -1.000000 0.000000 0 0 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']
    assert container._canvas is None
    assert offset_fields(container.place_children.offsets) == (0, -1, 1, 0,
                                                              10, 120)
    assert annotation_location(page_canvas) == (15, 90, 3, 20)


def test_own_contents_rotated_like_children():
    """Own contents and children are subject to the same transform"""
    for sideways in ('left', 'right'):
        lines = placement(make_container(sideways))
        rotate_index = next(index for index, line in enumerate(lines)
                            if line.endswith(b'0 0 cm'))
        assert lines.index(MARKER.encode()) == rotate_index + 1
        assert lines.index(CHILD.encode()) == rotate_index + 2


def test_translation_offsets_are_composed():
    """Offsets are composed in the order the containers are nested"""
    canvas = Canvas()
    canvas.annotate(ANNOTATION, 1, 2, 3, 4)
    page_canvas = Canvas()
    inner = page_canvas.annotation_transform(10, 20, 30, 40)
    outer = page_canvas.annotation_transform(5, 7, 50, 60)
    canvas.write_to(page_canvas, (inner, outer))
    assert annotation_location(page_canvas) == (16, 29, 3, 4)


def test_rotation_offsets_are_composed():
    canvas = Canvas()
    canvas.annotate(ANNOTATION, 1, 2, 3, 4)
    page_canvas = Canvas()
    inner = page_canvas.annotation_transform(10, 20, 30, 40)
    outer = page_canvas.annotation_transform(5, 7, 50, 60, 'right')
    canvas.write_to(page_canvas, (inner, outer))
    assert annotation_location(page_canvas) == (27, 43, 4, 3)


def test_write_to_without_offsets():
    canvas = Canvas()
    canvas.annotate(ANNOTATION, 1, 2, 3, 4)
    page_canvas = Canvas()
    canvas.write_to(page_canvas, ())
    assert annotation_location(page_canvas) == (1, 2, 3, 4)


def test_destination_point_on_sideways_container():
    """Destinations are points, even though they carry a width in the layout"""
    canvas = Canvas()
    canvas.annotate(ANNOTATION, 5, 10, 0, 0)
    page_canvas = Canvas()
    transform = page_canvas.annotation_transform(10, 20, 100, 50, 'right')
    canvas.write_to(page_canvas, (transform,))
    assert annotation_location(page_canvas) == (20, 115, 0, 0)
