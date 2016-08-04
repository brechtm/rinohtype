.. module:: rinoh.flowable

.. _flowables:

Flowable
========

.. autoclass:: Flowable

.. autoclass:: FlowableStyle

.. autoclass:: FlowableState


No-Output Flowables
-------------------

These flowables do not directly place anything on the page. All except
:class:`DummyFlowable` do have side-effects however. Some of these side-effects
affect the rendering of the document in an indirect way.

.. autoclass:: DummyFlowable

.. autoclass:: AnchorFlowable

.. autoclass:: SetMetadataFlowable

.. autoclass:: WarnFlowable

.. autoclass:: PageBreak


Labeled Flowables
-----------------

.. autoclass:: LabeledFlowable
    :members:

.. autoclass:: LabeledFlowableStyle
    :members:

.. autoclass:: LabeledFlowableState
    :members:


Grouping Flowables
------------------

.. autoclass:: GroupedFlowables
    :members:

.. autoclass:: GroupedFlowablesStyle
    :members:

.. autoclass:: GroupedFlowablesState
    :members:


.. autoclass:: StaticGroupedFlowables
    :members:

.. autoclass:: GroupedLabeledFlowables
    :members:


Horizontally Aligned Flowables
------------------------------

.. autoclass:: HorizontallyAlignedFlowable
    :members:

.. autoclass:: HorizontallyAlignedFlowableStyle
    :members:

.. autoclass:: HorizontallyAlignedFlowableState
    :members:


Floating Flowables
------------------

.. autoclass:: Float
    :members:

.. autoclass:: FloatStyle
    :members:
