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

.. autoclass:: Locale
    :members:


.. module:: rinoh.inline

Inline Elements (:mod:`rinoh.inline`)
-------------------------------------

.. autoclass:: InlineFlowable
    :members:


Styling Properties
------------------

.. currentmodule:: rinoh.paragraph

.. autoclass:: TextAlign
    :members:


Line Spacing
............

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

.. autoclass:: TabAlign
    :members:

.. autoclass:: TabStop
    :members:

.. autoclass:: TabStopList
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
