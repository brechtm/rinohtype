.. module:: rinoh.paragraph

.. _paragraph:

Paragraph (:mod:`rinoh.paragraph`)
==================================

.. autoclass:: ParagraphBase
    :members:

.. autoclass:: Paragraph
    :members:

.. autoclass:: ParagraphState
    :members:


.. module:: rinoh.text

Styled Text (:mod:`rinoh.text`)
-------------------------------

.. autoclass:: StyledText
    :members:

.. autoclass:: SingleStyledText
    :members:

.. autoclass:: MixedStyledText
    :members:


.. module:: rinoh.inline

Inline Elements (:mod:`rinoh.inline`)
-------------------------------------

.. autoclass:: InlineFlowable
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


.. _predefined_line_spacings:

The following standard line spacings have been predefined:

.. autodata:: DEFAULT

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
