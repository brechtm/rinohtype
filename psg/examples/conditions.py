#!/usr/bin/python
# -*- coding: utf-8 -*-
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##  Copyright 2006 by Andreas Junge <aj@jungepartner.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log: conditions.py,v $
# Revision 1.1  2006/10/16 12:50:11  diedrich
# Initial commit
#
# Revision 1.1  2006/10/15 18:02:52  t4w00-diedrich
# Initial commit.
#
#
#

import sys
from string import *
from types import *
from copy import copy
from datetime import datetime
now = datetime.now
from os.path import dirname, join as pjoin

from psg.debug import debug
from psg.exceptions import *
from psg.util import *
from psg.drawing.box import canvas, textbox, eps_image
from psg.fonts.type1 import type1
from psg.document.dsc import dsc_document

from orm2.datasource import datasource
from orm2 import sql
from orm2.debug import sqllog


"""
This is a real world example of psg in action. It has been written for
a customer of mine who wants to provide a price and conditions table
on the www which is stored in an RDBMS and presented to the user as
HTML on the various pages of his CMS and as a downloadable .pdf
file. This module creates a PostScript file which is then converted to
PDF on download through GNU Ghostscript. The RDBMS has been replaced
with a number of classes that generate random latin text for texting
purposes. Except for comments this code is identical to the production
software.

Up to this point this is the most sophisticated layout engine written
for psg. I plan to refine this step by step, on experience basis, to
something that will become part of the core distributionw when I feel
that it does the job well enough. You can see that this aims at an
XML/CSS implementation by some of the identifyers and ideas that are
being used.


The data structure
------------------

   The conditions_schema.py module contains a fake datamodel that
   returns lorem ipsum instead of the data in the RDBMS. The data is
   organized like this::

      class page:
          name: string

          entries: one2many(entry)

      class entry:
          type: either caption or info

          value1: string
          value2: string

The layout
----------

   A caption entry is printed as a caption (value1) and some
   explainatory text (value2). An info entry is a table row with a
   left value (value1) and a right value (value2) which are printed
   on alternating shades of gray.

   A page is split up in two columns which contain sections (the
   pages) which start with a green title and have a table in them
   which is again split up in sections (seperated by captions and
   explainatory text). A page section may not exceed one column and it
   may not be split. (You may note that the tables were previously
   split on column breaks. The customer asked me to change this. This
   puts some constraints to the number of rows per (database-)page
   which are not likely to be broken in practice. However the lorem
   ipsum generator doesn't know about this, which may or may not cause
   problems). The page has a background provided as an EPS image
   containing bitmaps and a number of vector elements.

   The layout engine operates on a sequence of div instances, which
   are basically rectangular subsets of a column. Every div has a
   style associated to it that defines font, color and
   background-color. I wrote special div classes for regular
   paragraphs, table and rows as well as a container for divs that
   keeps them together as one (to prevent column breaks in page
   tables). Font face and -color may not change within a div. That's
   the most noteable constraint I guess. But my little layout engine
   here does this particular job and it does it well!

   This code is not optimized for performance. A number of
   calculations are performed more than once.
"""

import conditions_schema as schema

class style(dict):
    """
    All lengths in PostScript units, all colors either in PostScript
    commands as a string or None. The font must be a psg.fonts.font
    object or None (in which case the font must be set previously to
    rendering the div. The line-height attribute is a factor applied
    to the font size to determine line height. The border-width is not
    taken into account in calculating the padding and margin values, so
    you have to supply large enough values to avoid overlap.
    """

    defaults = { "font": None,             # psg.font.font instance
                 "font-size": 12,          # in pt
                 "char-spacing": 0,        # in pt
                 "line-height": 1,         # A factor applied to font-size
                 "text-align": "left",     # left, right, justified

                 "color": "0 setgray",     # PostScript code to set a color
                 "background-color": None, # PostScript code to set a color

                 "border-color": None,     # PostScript code to set a color
                 "border-width": None,     # In pt

                 "padding-left": 0,        # In pt
                 "padding-top": 0,         # In pt
                 "padding-right": 0,       # In pt
                 "padding-bottom": 0,      # In pt

                 "margin-left": 0,         # In pt
                 "margin-top": 0,          # In pt
                 "margin-right": 0,        # In pt
                 "margin-bottom": 0 }      # In pt

    def __init__(self, **attributes):
        dict.update(self, self.defaults)
        self._set = set(attributes.keys())
        self.update(attributes)

        for key, value in self.items():
            if type(value) == int:
                self[key] = float(self[key])

        assert self.text_align in ( "left", "right", "justify", )

    def __getattr__(self, name):
        name = name.replace("_", "-")

        if "_" + name in self.__dict__:
            method = super().__getattr__(self, "_" + name)
            return method()
        elif name in self:
            return self[name]
        else:
            raise AttributeError(name)

    def __setitem__(self, key, value):
        key = key.replace("_", "-")
        dict.__setitem__(self, key, value)
        self._set.add(key)

    def __getitem__(self, key):
        key = key.replace("_", "-")
        return dict.__getitem__(self, key)

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def h_margin(self):
        return self.margin_left + self.margin_right

    def v_margin(self):
        return self.margin_top + self.margin_bottom

    def hv_margin(self):
        return self.h_margin() + self.v_margin()

    def h_padding(self):
        return self.padding_left + self.padding_right

    def v_padding(self):
        return self.padding_top + self.padding_bottom

    def hv_padding(self):
        return self.h_padding() + self.v_padding()

    def __add__(self, other):
        ret = style()
        for a in self._set:
            ret[a] = self[a]

        for a in other._set:
            ret[a] = other[a]

        return ret

class div:
    """
    A rectengular subset of a column.
    """
    splitable = True

    def __init__(self, content, style):
        if type(content) != str:
            raise TypeError("typeset() only works on unicode strings!")

        self.content = content[:]
        self.style = style

    def height(self, width):
        """
        The height() function performs rudimentary typesetting of the
        div's content to determine its height. The calculations will
        include padding and margin values.
        """
        inner_width = width - self.style.h_padding() + self.style.h_margin()
        height = self.text_height(inner_width)

        return height + self.style.v_padding() + self.style.v_margin()


    def text_height(self, inner_width, words=None):
        """
        Return the height of the text typeset with this div's font in
        a box that's 'innder_width' PostScript units wide. This method
        does not take margin and padding into account.
        """

        if words is None: words = self.words()
        width = inner_width
        line_width = 0.0
        line_height = self.style.font_size * self.style.line_height
        height = line_height


        space_width = self.style.font.metrics.stringwidth(
            " ", self.style.font_size)

        while(words):
            word = car(words)

            word_width = self.style.font.metrics.stringwidth(
                word, self.style.font_size, True, self.style.char_spacing)

            if line_width + word_width > width:
                height += line_height
                line_width = 0.0
            else:
                line_width += word_width + space_width
                words = cdr(words)

        return height


    def words(self):
        """
        Return a list of the words the div contains.
        """
        return self.content.split()


    def render(self, layout_box):

        if self.splitable:
            # Check if there is room in the layout box for at least one line
            min_height = self.style.v_padding() + self.style.v_margin() + \
                         self.style.font_size * self.style.line_height
        else:
            min_height = self.height(layout_box.w())

        if layout_box.y_cursor() < min_height:
            return self

        needed_height = self.height(layout_box.w())

        if layout_box.y_cursor() < needed_height:
            height = layout_box.y_cursor()
        else:
            height = needed_height

        margin_box = canvas(
            layout_box,
            self.style.margin_left,
            layout_box.y_cursor() - height + self.style.margin_bottom,
            layout_box.w() - self.style.h_margin(),
            height - self.style.v_margin(),
            debug.verbose)

        layout_box.append(margin_box)

        self.border_and_background(margin_box)


        if self.style.hv_padding() == 0:
            x = 0
            y = 0
            w = margin_box.w()
            h = margin_box.h()
        else:
            x = self.style.padding_left
            y = self.style.padding_bottom
            w = margin_box.w() - self.style.h_padding()
            h = margin_box.h() - self.style.v_padding()

        if self.style.font.metrics.descender is not None:
            y -= float(self.style.font.metrics.descender) \
                 * self.style.font_size / 1000

        # Create a textbox
        rest = self.typeset(margin_box, x, y, w, h)

        if rest != "":
            rest = div(rest, self.style)
        else:
            rest = None

        layout_box.y_advance(min(height, layout_box.y_cursor()))

        return rest

    def border_and_background(self, margin_box):
        # If we need an inner box...
        if ( self.style.border_color is not None and \
             self.style.border_width is not None ) or \
           self.style.background_color is not None:

            # The box in PostScript commands...
            print("gsave", file=margin_box)
            print("newpath", file=margin_box)
            print("%f %f moveto" % ( 0, 0, ), file=margin_box)
            print("%f %f lineto" % ( 0, margin_box.h(), ), file=margin_box)
            print("%f %f lineto" % ( margin_box.w(),
                                     margin_box.h(), ), file=margin_box)
            print("%f %f lineto" % ( margin_box.w(), 0, ), file=margin_box)
            print("closepath", file=margin_box)

            # Fill if we've got a background color
            if self.style.background_color is not None:
                print(self.style.background_color, file=margin_box)
                print("fill", file=margin_box)

            # If border_color and border_width are available,
            # draw a border.
            if self.style.border_color is not None and \
                   self.style.border_width is not None:
                print(margin_box, self.style.color, file=margin_box)
                print("[5 5] %f setdash"%self.style.border_width, file=margin_box)
                print("stroke", file=margin_box)

            print("grestore", file=margin_box)


    def typeset(self, parent_box, x, y, w, h):
        line_spacing = ( self.style.line_height * self.style.font_size ) - \
                       self.style.font_size

        tb = textbox(parent_box, x, y, w, h, border=debug.verbose)
        parent_box.append(tb)

        tb.set_font(font = self.style.font,
                    font_size = self.style.font_size,
                    kerning = True,
                    alignment = self.style.text_align,
                    char_spacing = self.style.char_spacing,
                    line_spacing = line_spacing)

        if self.style.color is not None:
            print (self.style.color, file=tb)

        return tb.typeset(" ".join(self.words()))


class lr_div(div):
    splitable = False

    def __init__(self, left, right, style, padding=3):
        self.left = left
        self.right = right
        self.padding = padding
        self.style = style

    def widths(self, width):
        right_width = self.style.font.metrics.stringwidth(self.right,
                                                          self.style.font_size)

        if right_width > (width - self.padding) / 2.0:
            right_width = (width - self.padding) / 2.0

        left_width = width - right_width

        return ( left_width, right_width, )

    def text_height(self, width, words=None):
        left_width, right_width = self.widths(width)

        left_height = div.text_height(self, left_width, self.left.split())
        right_height = div.text_height(self, right_width,
                                       self.right.split())

        return max(left_height, right_height)

    def typeset(self, parent_box, x, y, w, h):
        left_width, right_width = self.widths(w)

        line_spacing = ( self.style.line_height * self.style.font_size ) - \
                       self.style.font_size


        tb = textbox(parent_box, x, y, left_width, h, border=debug.verbose)
        parent_box.append(tb)

        tb.set_font(font = self.style.font,
                    font_size = self.style.font_size,
                    kerning = True,
                    alignment = self.style.text_align,
                    char_spacing = self.style.char_spacing,
                    line_spacing = line_spacing)


        if self.style.color is not None:
            print(self.style.color, file=tb)

        tb.typeset(self.left)

        tb = textbox(parent_box,
                     left_width, y, right_width, h,
                     border=debug.verbose)
        parent_box.append(tb)

        tb.set_font(font = self.style.font,
                    font_size = self.style.font_size,
                    kerning = True,
                    alignment = self.style.text_align,
                    char_spacing = self.style.char_spacing,
                    line_spacing = line_spacing)


        if self.style.color is not None:
            print(self.style.color, file=tb)

        tb.typeset(self.right)

        return ""

class div_div(div):
    """
    A div containing divs to keep the page tables together on customer
    request.
    """
    splitable = False

    def __init__(self, divs):
        self.divs = divs

    def height(self, width):
        return sum(map(lambda div: div.height(width), self.divs))

    def render(self, layout_box):
        if self.height(layout_box.w()) > layout_box.y_cursor():
            return self
        else:
            for div in self.divs:
                div.render(layout_box)

class layout_box(canvas):
    """
    This class is for the columns.
    """
    def __init__(self, parent, x, y, w, h, border=False, clip=False, **kw):
        canvas.__init__(self, parent, x, y, w, h, border, clip)

        self._y_cursor = h

    def y_cursor(self):
        return self._y_cursor

    def y_advance(self, amount):
        if self._y_cursor - amount < 0:
            raise EndOfBox()
        else:
            self._y_cursor -= amount




def layout(divs, layout_box_factory):
    """
    I'd much rather go to the layout chocolate factory. Anyway, for the sake
    of Martin and Skinner this thing needs a box factory to work. A box
    factory is simply a generator returning boxes through its next() method.
    If you've got a ready made list of boxes, you can just use::

       iter(list_of_boxes)

    which will make this function use the boxes on the list one after the
    other. For more advanced usage, you'll probably want to write a gernator
    function that takes a document as argument and adds pages to that
    document, yielding layout boxes on those pages. The divs parameter must be
    a list of instances of the div class above. If the box factory
    raises a StopIteration exception before all divs are rendered, a
    EndOfDocument exception will be raised.

    There is a not-so-subtle limitation of this function: If you've got a div
    that's not splitable and does not fit in any of those boxes made in your
    factory, this function will demand an endless amount of boxes and go into
    an infinite loop until your cardboard supply runs out... er your core
    memory, that is.

    So if you direct your eyes to the floor, you will see a dotted line
    around my desk and my chair....
    """
    divs = list(divs)
    divs.reverse()
    try:
        current_box = None

        while divs:
            div = divs.pop()

            if current_box is not None and \
                   not isinstance(div, lr_div) and \
                   current_box.y_cursor() < mm(25):
                current_box = None

            if current_box is None:
                current_box = next(layout_box_factory)

            rest = div.render(current_box)

            if rest is not None:
                divs.append(rest)
                current_box = None


    except StopIteration:
        raise EndOfDocument()


############################################################################

def new_page(document, background, italic):
    """
    This is the generator I was talking about in the comment to the
    layout() function above.
    """
    while True:
        page = document.page("a4", None)
        page.append(background)

        left = layout_box(page, mm(40), mm(25), mm(75), mm(242.99),
                          debug.verbose)
        right = layout_box(page, mm(124.75), mm(25), mm(75), mm(242.99),
                           debug.verbose)

        stand = textbox(page, mm(40), mm(19), mm(100), 7)
        stand.set_font(italic, 7)
        page.append(stand)
        stand.typeset("Stand: " + str(now().strftime("%d.%m.%Y")))

        page.append(left)
        yield left

        page.append(right)
        yield right

def my_document(ds):
    document = dsc_document()

    dir = dirname(__file__)

    if dir == "": dir = "."

    print("Loading background", file=debug)
    background = eps_image(document, open(dir + "/conditions_background.eps", 'rb'))


    print("Loading fonts", file=debug)
    italic  = type1(open(pjoin(dir, "italic.pfb"), 'rb'),
                    open(pjoin(dir, "italic.afm"), 'rb'))

    bold    = type1(open(pjoin(dir, "bold.pfb"), 'rb'),
                    open(pjoin(dir, "bold.afm"), 'rb'))

    bolditalic = type1(open(pjoin(dir, "bolditalic.pfb"), 'rb'),
                       open(pjoin(dir, "bolditalic.afm"), 'rb'))

    # Define the relevant styles.
    h1 = style(font=bolditalic, font_size=9.2,
               color="0.98 0 0.48 0.63 setcmykcolor",
               margin_top=mm(2))

    h2 = style(font=bolditalic, font_size=8, color="0 setgray",
               margin_top=mm(2))

    description = style(font=italic, font_size=7, color="0 setgray",
               padding_top=2, padding_bottom=1, text_align="justify")

    tabelle_dunkel = style(font=italic, font_size=7, color="0 setgray",
                           background_color="1 0.24 sub setgray",
                           padding_top=2, padding_bottom=1,
                           padding_right=2)
    tabelle_hell   = style(font=italic, font_size=7, color="0 setgray",
                           background_color="1 0.12 sub setgray",
                           padding_top=2, padding_bottom=1,
                           padding_right=2)

    # Create the divs

    print("Making db requests", file=debug)
    divs = []
    pages = ds.select(schema.page, sql.order_by("rank"))
    tabcounter = 0

    for page in pages:
        ds = []
        ds.append(div(page.name, h1))

        entries = page.entries.select(sql.order_by("rank"))

        for entry in entries:
            if entry.type == "caption":
                if entry.value1 is not None and entry.value1.strip() != "":
                    ds.append(div(entry.value1, h2))

                if entry.value2 is not None and entry.value2.strip() != "":
                    ds.append(div(entry.value2, description))

            elif entry.type == "info":
                if entry.value2 is None or entry.value2.strip() == "":
                    ds.append(div(entry.value1, description))
                else:
                    cls = ( tabelle_dunkel, tabelle_hell, )[tabcounter%2]
                    tabcounter += 1
                    ds.append(lr_div(entry.value1, entry.value2, cls))

        divs.append(div_div(ds))

    # layout
    print("Starting layout process", file=debug)
    layout(divs, new_page(document, background, italic))

    return document


if __name__ == '__main__':

    document = my_document(schema.ds())
    out = open('conditions.ps', 'w', encoding="latin-1")
    document.write_to(out)
    out.close()
