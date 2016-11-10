.. module:: rinoh.paragraph

.. _paragraph:

Paragraph (:mod:`rinoh.paragraph`)
==================================

.. autoclass:: ParagraphBase
    :members:

.. autoclass:: Paragraph
    :members:

.. autoclass:: ParagraphStyle
    :members:

.. autoclass:: ParagraphState
    :members:


.. module:: rinoh.text

Inline Elements (:mod:`rinoh.text`)
-----------------------------------

.. autoclass:: StyledText
    :members:

.. autoclass:: TextStyle
    :members:

.. autoclass:: SingleStyledText
    :members:

.. autoclass:: MixedStyledText
    :members:


Styling Properties
------------------


Line Spacing
............

.. currentmodule:: rinoh.paragraph

.. autoclass:: LineSpacing
    :members:

.. autoclass:: DefaultSpacing
    :members:

.. autoclass:: ProportionalSpacing
    :members:

.. autoclass:: FixedSpacing
    :members:

.. autoclass:: Leading
    :members:


A number of standard line spacings have been predefined:

.. autodata:: STANDARD

.. autodata:: SINGLE

.. autodata:: DOUBLE


Tabulation
..........

.. autoclass:: TabStop
    :members:


Rendering Internals
-------------------

.. autoclass:: Glyph
    :members:

.. autoclass:: GlyphsSpan
    :members:


Miscellaneous Internals
-----------------------

.. autoclass:: HyphenatorStore
    :members:
