Tables
------

Table without directive:

=====  =====
  A    not A
=====  =====
False  True
True   False
=====  =====


Table directive, default alignment:

.. table::

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


Table directive, right alignment:

.. table::
   :align: right

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


.. table:: Table with caption, default alignment

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


.. table:: Table with caption, left alignment
   :align: left

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


.. table:: Table with caption, right alignment
   :align: right

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====
