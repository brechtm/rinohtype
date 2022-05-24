Creating content
======================

Now is an appropriate time to add some content to work with.

The first page of the project is the ``index.rst`` file. You can replace the
entire contents of the file with the following (edit the text to your taste)::

    All about me
    ============

    Write a few paragraphs introducing yourself.


    Basic formatting examples
    -------------------------

    Basic formatting in reStructuredText includes:

    * *emphasis*
    * **strong emphasis**
    * asterisks for list items

    Good things to include in your introduction would be a note about what you
    do and where you live.


    Some examples of Sphinx elements
    --------------------------------

    ..  epigraph::

        I'd like to be remembered by my friends and enemies as honest and
        stylish but slightly sinister. But mostly I'd just like to be
        remembered.

        -- Me


    ..  note:: Take note!

        Include a ``note`` element, like this one, in order to demonstrate
        how this is handled.

    ..  admonition:: An admonition

        An ``admonition`` is a generic kind of note, amongst several other
        kinds that Sphinx has to offer.

    ..  toctree::
        :hidden:

        plans
        skills


Add a new file, ``plans.rst``, containing::


    My plans
    ========

    Say something about your plans.

    Short-term plans
    ----------------

    Perhaps you have some things that you intend to do in the near future.

    For example, to write some Python code::

        def plot_file(self, filename="", wait=None, resolution=None, bounds=None):
            """Plots and image encoded as JSON lines in ``filename``. Passes the
            lines in the supplied JSON file to ``plot_lines()``.
            """

            bounds = bounds or self.bounds

            with open(filename, "r") as line_file:
                lines = json.load(line_file)

            self.plot_lines(
                lines=lines,
                wait=wait,
                resolution=resolution,
                bounds=bounds,
                flip=True
            )

    And to quote  a great mind:

        A good will is not good because of what it effects or accomplishes,
        because of its fitness to attain some proposed end, but only because of
        its volition, that is, it is good in itself and, regarded for itself,
        is to be valued incomparably higher than all that could merely be
        brought about by it in favor of some inclination and indeed, if you
        will, of the sum of all inclinations.

    Long-term plans
    ---------------

    And perhaps you have some that will come later on.

    Include an image. If you want a suitable image file, use `Dürer's
    rhinoceros from Wikipedia
    <https://en.wikipedia.org/wiki/Dürer's_Rhinoceros#/media/File:The_Rhinocero
    s_(N GA_1964.8.697)_enhanced.png>`_. Rename it to ``rhino.png`` and place
    it in the root of your Sphinx project.

    ..  figure:: /rhino.png
        :figclass: wider
        :alt:

        Not to be mistaken with rinoh: a rhino.

And another, ``skills.rst``::

    Skills
    ======

    I enjoy learing new skills.

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus
    fringilla quis metus id porta. Nullam nibh ligula, mattis at molestie non,
    interdum eu massa. Curabitur id sapien ut purus interdum lacinia.

    Sed congue ligula sit amet porta pulvinar. Etiam magna risus, porttitor
    viverra accumsan vel, rutrum quis eros. Curabitur at nibh lacus. Fusce ex
    massa, pellentesque sed est eu, lacinia sodales nibh. Curabitur volutpat
    justo a tortor bibendum, sed rutrum purus vestibulum.

    Aliquam aliquet neque id erat cursus, vestibulum condimentum erat
    convallis. In tristique, quam lacinia semper pretium, ante arcu blandit
    turpis, non mollis sem magna ac risus.

    Suspendisse pharetra tellus libero, ac aliquet est mattis non. Nunc
    pretium scelerisque erat sit amet rutrum. Aliquam sit amet ornare mi.

    Morbi lacus purus, elementum et leo nec, dictum dictum nulla. Sed
    fringilla at elit venenatis molestie. Cras rhoncus enim sed interdum
    sodales. Proin at sodales quam. Duis auctor libero mattis metus venenatis
    pretium. Etiam bibendum bibendum nisi, quis vulputate nisi commodo ut.

    Duis semper metus id quam venenatis euismod.


The last thing to do is to add a table of contents to the ``index.rst`` file,
so it knows how to organise the content you have created. At the end of the
file, add::

    ..  toctree::
        :hidden:

        plans
        skills

Add additional pages if you wish.

This isn't the place for a primer on Sphinx and rST, so you should look for
other resources if you need guidance on more ambitious formatting at this
stage.

Run ``make html`` and reload the ``index.html`` page to see the new content as
HTML; run ``make rinoh`` and re-open ``allaboutme.pdf`` to see the new version
of the PDF (if you're lucky, your PDF viewer will reload the changed file for
your automatically).
