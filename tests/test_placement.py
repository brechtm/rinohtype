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


def make_container(sideways=None, left=0, top=0, width=100, height=50):
    """A minimal stand-in for :class:`rinoh.layout.Container`"""
    own_canvas = Canvas()
    own_canvas.print(MARKER)

    def place_children(page_canvas, offsets):
        page_canvas.print(CHILD)

    return SimpleNamespace(left=left, top=top, width=width, height=height,
                           sideways=sideways, _canvas=own_canvas,
                           place_children=place_children)


def place(container):
    page_canvas = Canvas()
    Container.place(container, page_canvas, ())
    return page_canvas.getvalue().splitlines()


def test_not_sideways():
    lines = place(make_container(left=10, top=20))
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']


def test_sideways_left():
    container = make_container('left', left=10, top=20, width=100, height=50)
    lines = place(container)
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     b'1 0 0 1 50.000000 0.000000 cm',
                     b'0.000000 -1.000000 1.000000 0.000000 0 0 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']
    assert container._canvas is None


def test_sideways_right():
    container = make_container('right', left=10, top=20, width=100, height=50)
    lines = place(container)
    assert lines == [b'q',
                     b'1 0 0 1 10.000000 -20.000000 cm',
                     b'1 0 0 1 0.000000 -100.000000 cm',
                     b'0.000000 1.000000 -1.000000 0.000000 0 0 cm',
                     MARKER.encode(),
                     CHILD.encode(),
                     b'Q']
    assert container._canvas is None


def test_own_contents_rotated_like_children():
    """Own contents and children are subject to the same transform"""
    for sideways in ('left', 'right'):
        container = make_container(sideways)
        lines = place(container)
        rotate_index = next(index for index, line in enumerate(lines)
                            if line.endswith(b'0 0 cm'))
        assert lines.index(MARKER.encode()) == rotate_index + 1
        assert lines.index(CHILD.encode()) == rotate_index + 2
