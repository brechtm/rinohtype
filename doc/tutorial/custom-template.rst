Creating a custom template
===========================

To recap what we've built so far:

* first, we have a Sphinx project containing some content across multiple
  sections
* as well as Sphinx's built-in HTML rendering, rinohtype includes a builder
  that produces a PDF version
* in ``conf.py``, we have pointed rinohtype at a local template configuration
  file, ``my-article.rtt``
* the ``my-article.rtt`` template configuration does two things: it tells
  rinohtype to use use the built-in ``article`` template, and to use a custom
  stylesheet, ``allaboutme.rts``, that extends the built-in ``sphinx``
  stylesheet


Have a look at the contents of the :ref:`Sphinx style sheet`.
