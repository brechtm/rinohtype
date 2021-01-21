Inline Markup
=============

Paragraphs contain text and may contain inline markup: *emphasis*,
**strong emphasis**, ``inline literals``, standalone hyperlinks
(http://www.python.org), external hyperlinks (Python_), internal
cross-references (example_), external hyperlinks with embedded URIs
(`Python web site <http://www.python.org>`__).

.. _Python: http://www.python.org/

Literal blocks are indicated with a double-colon ("::") at the end of
the preceding paragraph (over there ``-->``).  They can be indented::

    if literal_block:
        text = 'is left as-is'
        spaces_and_linebreaks = 'are preserved'
        markup_processing = None


.. _example:

Table
=====

=====  =====  ======
   Inputs     Output
------------  ------
  A      B    A or B
=====  =====  ======
False  False  False
True   False  True
False  True   True
True   True   True
=====  =====  ======
