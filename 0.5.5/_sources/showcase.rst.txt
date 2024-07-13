.. _showcase:

Showcase
========

Some examples of PDF documents produced by rinohtype are collected here. This
section mainly serves to give users an idea of the level of customization that
is achievable by means of custom templates and style sheets.


Lekis
-----

:showcase:`Odpisy.pdf` was styled by means of both a custom template and style
sheet. The custom template (Python) and configuration (INI file):

- configures Czech as the document's language, which prevents a line break
  after specific words (following Czech typography rules)
- defines custom title (with vector logo) and colophon pages
- sets a background for content pages, marking the page header
- defines a custom back page, listing company contact details

Actually, there are two template configuration files: a base configuration and
one for a special type of documents. The latter inherits from the base template
configuration and only overrides what needs changing. In this case, it omits
the table of contents part from the document. :showcase:`Odpisy.pdf` is an
example of such a document.


.. magick montage -density 20 "doc/showcase/Odpisy.pdf[0,2,5]" -background grey
    -tile x1 -border 4 -bordercolor white -geometry +0+0
    doc/showcase/Odpisy.png
.. figure:: showcase/Odpisy.png

   Some pages from :showcase:`Odpisy.pdf`


A single style sheet is used for both types of documents. It does not specify
the Sphinx style sheet included with rinohtype as a base stylesheet so as to
avoid unexpected changes in the document style in case the Sphinx style sheet
is updated in a future rinohtype release. The style sheet defines:

- the ``[VARIABLES]`` section defines monospaced, serif and sans-serif
  typefaces and a set of key colors that are referenced in style definitions
- custom 'numbering' for headings (square glyph) and bullet lists (fast forward
  glyph)
- a top border for certain headings
- custom in-line titles (in-line images or specific font glyphs) for
  admonitions
- coloured styling for the ``menuselection`` role
- small-capital styling for keyboard shortcuts
