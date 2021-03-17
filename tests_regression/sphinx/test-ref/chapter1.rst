.. _chapter-1:

One
===

.. _section-a:

Section A
---------

.. _par-a:

Paragraph A with some references:

- :ref:`chapter-1`, :ref:`this chapter <chapter-1>`, :numref:`chapter-1`
- :ref:`chapter-2`, :ref:`that chapter <chapter-2>`, :numref:`chapter-2`
- :ref:`section-a`, :ref:`this section <section-a>`, :numref:`section-a`
- :ref:`section-c`, :ref:`that section <section-c>`, :numref:`section-c`
- :ref:`par-a`, :ref:`this paragraph <par-a>`, :numref:`par-a`
- :ref:`par-b`, :ref:`that paragraph <par-b>`, :numref:`par-b`
- :ref:`par-c`, :ref:`yonder paragraph <par-c>`, :numref:`par-c`
- :ref:`par-d`, :ref:`yet another paragraph <par-d>`, :numref:`par-d`
- :ref:`fig-1`, :ref:`this figure <fig-1>`, :numref:`fig-1`
- :ref:`fig-2`, :ref:`that figure <fig-2>`, :numref:`fig-2`
- :ref:`table-1`, :ref:`that table <table-1>`, :numref:`table-1`
- :term:`&&`, :term:`SOS`
- broken reference: :ref:`nonexisting`


.. _section-b:

Section B
---------

.. _par-b:

Paragraph B.

.. figure:: biohazard.png
   :name: fig-1

   Biohazard!


.. table:: Input-output
   :name: table-1

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
