
First Section
=============

Paragraph preceding the first sideways table.


.. table:: Sideways table
   :class: sideways

   +------------------------+------------+----------+----------+
   | Header row, column 1   | Header 2   | Header 3 | Header 4 |
   | (header rows optional) |            |          |          |
   +========================+============+==========+==========+
   | body row 1, column 1   | column 2   | column 3 | column 4 |
   +------------------------+------------+----------+----------+
   | body row 2             | Cells may span columns.          |
   +------------------------+------------+---------------------+
   | body row 3\ [#f1]_     | Cells may  | - Table cells       |
   +------------------------+ span rows. | - contain           |
   | body row 4             |            | - body elements.    |
   +------------------------+------------+----------+----------+
   | body row 5             | Cells may also be     |          |
   |                        | empty: ``-->``        |          |
   +------------------------+-----------------------+----------+


.. [#f1] Footnote text should also rotate.


Paragraph following the first sideways table and preceding the second sideways
table.

.. table:: Another sideways table
   :class: sideways-break

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


Second Section
==============

Paragraph preceding the third sideways table which spans two pages.

.. table:: Sideways table spanning two pages
   :class: sideways-break

   +------------------------+------------+----------+----------+
   | Header row, column 1   | Header 2   | Header 3 | Header 4 |
   | (header rows optional) |            |          |          |
   +========================+============+==========+==========+
   | body row 1, column 1   | column 2   | column 3 | column 4 |
   +------------------------+------------+----------+----------+
   | body row 2             | Cells may span columns.          |
   +------------------------+------------+---------------------+
   | body row 3\ [#f2]_     | Cells may  | - Table cells       |
   +------------------------+ span rows. | - contain           |
   | body row 4             |            | - body elements.    |
   +------------------------+------------+----------+----------+
   | body row 5             | Cells may also be     |          |
   |                        | empty: ``-->``        |          |
   +------------------------+------------+----------+----------+
   | body row 6, column 1   | column 2   | column 3 | column 4 |
   +------------------------+------------+----------+----------+
   | body row 7             | Cells may span columns.          |
   +------------------------+------------+---------------------+
   | body row 8\ [#f3]_     | Cells may  | - Table cells       |
   +------------------------+ span rows. | - contain           |
   | body row 9             |            | - body elements.    |
   +------------------------+------------+----------+----------+
   | body row 10            | Cells may also be     |          |
   |                        | empty: ``-->``        |          |
   +------------------------+------------+----------+----------+
   | body row 11, column 1  | column 2   | column 3 | column 4 |
   +------------------------+------------+----------+----------+
   | body row 12            | Cells may span columns.          |
   +------------------------+------------+---------------------+
   | body row 13\ [#f4]_    | Cells may  | - Table cells       |
   +------------------------+ span rows. | - contain           |
   | body row 14            |            | - body elements.    |
   +------------------------+------------+----------+----------+
   | body row 15            | Cells may also be     |          |
   |                        | empty: ``-->``        |          |
   +------------------------+-----------------------+----------+

.. [#f2] Footnote in a sideways table spanning multiple pages.

.. [#f3] Another footnote.

.. [#f4] And the last footnote.
