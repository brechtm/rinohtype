
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


Paragraph following the first sideways table.

.. table:: Another sideways table
   :class: sideways

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====
