.. module:: rinoh.flowable

.. _flowables:

Flowable (:mod:`rinoh.flowable`)
================================

.. autoclass:: Flowable

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

.. autoclass:: LabeledFlowableState
    :members:


Grouping Flowables
------------------

.. autoclass:: GroupedFlowables
    :members:

.. autoclass:: GroupedFlowablesState
    :members:


.. autoclass:: StaticGroupedFlowables
    :members:

.. autoclass:: GroupedLabeledFlowables
    :members:


Floating Flowables
------------------

.. autoclass:: Float
    :members:


Styling Properties
------------------

.. autoclass:: HorizontalAlignment
    :members:

.. autoclass:: FlowableWidth
    :members:
