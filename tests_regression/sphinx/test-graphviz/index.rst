Graphviz
========

.. graphviz::
   :name: Bar Baz
   :class: my-class

   digraph foo {
      "bar" -> "baz"
   }


.. graphviz::
   :align: right
   :caption: This figure is rendered incorrectly due to bug in the
             alignment of figures (grouped flowables).

   digraph foo {
      "bar" -> "baz";
   }

.. graphviz::
   :align: left
   :alt: Alt

   digraph foo {
      "bar" -> "baz";
   }
