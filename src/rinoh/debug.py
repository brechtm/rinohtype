# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


"""Debug rendering helpers

Set the ``RINOH_DEBUG_DESTINATIONS`` environment variable to a non-zero value
to draw named destinations on the page. This is intended for development only;
the resulting PDF is no longer suitable as a regression-test reference.

"""

from os import getenv

from .annotation import destination_anchor
from .color import BLACK, BLUE, RED
from .dimension import PT
from .draw import Rectangle, ShapeStyle, Stroke
from .font.style import FontWeight
from .fonts import adobe14
from .paragraph import render_text


DRAW_DESTINATIONS = getenv('RINOH_DEBUG_DESTINATIONS', '0') != '0'


def draw_destinations(page):
    """Draw the named destinations registered on `page`"""
    if not DRAW_DESTINATIONS:
        return
    font = adobe14.helvetica.get_font(weight=FontWeight.MEDIUM)
    rotation = {'left': -90, 'right': 90}.get(page.display_sideways, 0)
    for annotation_location in page.canvas.annotations:
        annotation = annotation_location.annotation
        if annotation.type != 'NamedDestination':
            continue
        left, top = annotation_location.left, annotation_location.top
        width = annotation_location.width or 0
        height = annotation_location.height or 0
        anchor_left, anchor_top = destination_anchor(annotation_location,
                                                     page.display_sideways)
        if width > 0 or height > 0:
            _rectangle(page, left, top, width, height, stroke=BLUE)
        else:
            _rectangle(page, anchor_left - 4, anchor_top - 4, 8, 8,
                       stroke=BLUE)
        _rectangle(page, anchor_left - 2, anchor_top - 2, 4, 4, fill=RED)
        label = '{} (TL)'.format(', '.join(annotation.names))
        label_top = anchor_top - 3 if anchor_top > 7 else anchor_top + 9
        render_text(page, label, anchor_left + 6, label_top, font, 5*PT,
                    BLACK, rotation)


def _rectangle(page, left, top, width, height, stroke=None, fill=None):
    """Draw a rectangle in page coordinates (origin top-left, y down)"""
    style = ShapeStyle(stroke=Stroke(0.5*PT, stroke) if stroke else None,
                       fill_color=fill)
    Rectangle((left, - top - height), width, height,
              style=style).render(page)
