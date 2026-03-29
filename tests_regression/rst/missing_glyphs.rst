:warnings:
    Don't know how to map unicode index 0x232d
    Times-Roman does not contain glyph for unicode index 0x232d
    DejaVuSerif does not contain glyph for unicode index 0x232d
    Times-Roman does not contain glyph for unicode index 0x2207

.. include:: <isotech.txt>

Missing glyphs: |cylcty| and |nabla|.

Without surrounding whitespace:\ |cylcty|\ and\ |nabla|.

Missing glyph in a linked reference: |solo|_, |after|_, |before|_.

.. [#f1] Footnote one!
.. [#f2] Footnote two!

.. |solo| replace:: |nabla|
.. _solo: http://www.python.org

.. |after| replace:: |nabla| after
.. _after: http://www.python.org

.. |before| replace:: after |nabla|
.. _before: http://www.python.org

.. |>| unicode:: 0x2023

Test for word wrapping of a line with missing glyph: Menu |>| Item

And Menu |>| Item, Utility Functions |>| System Status |>| Sys Ctrl
