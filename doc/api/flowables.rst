.. _flowables:

Flowables
=========

.. module:: rinoh.flowable


Base Class for Flowables
------------------------

.. autoclass:: Flowable

.. autoclass:: FlowableStyle

.. autoclass:: FlowableState


Flowables that Do Not Render Anything
-------------------------------------

These flowables do not place anything on the page. All except
:class:`DummyFlowable` do have side-effects however. Some of these side-effects
affect the rendering of the document in an indirect way.

.. autoclass:: DummyFlowable

.. autoclass:: SetMetadataFlowable

.. autoclass:: WarnFlowable

.. autoclass:: PageBreak


Labeled Flowables
-----------------

.. autoclass:: LabeledFlowable

.. autoclass:: LabeledFlowableStyle


Grouping Flowables
------------------

.. autoclass:: GroupedFlowables

.. autoclass:: GroupedFlowablesStyle

.. autoclass:: GroupedFlowablesState


.. autoclass:: StaticGroupedFlowables

.. autoclass:: GroupedLabeledFlowables


Horizontally Aligned Flowables
------------------------------

.. autoclass:: HorizontallyAlignedFlowable

.. autoclass:: HorizontallyAlignedFlowableStyle

.. autoclass:: HorizontallyAlignedFlowableState


Floating Flowables
------------------

.. autoclass:: Float
