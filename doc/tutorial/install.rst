Installation
============

All work will take place in a Python virtual environment.

First, create a directory for your project, then a virtual environment within
it, and activate the virtual environment::

    mkdir rinoh-tutorial
    cd rinoh-tutorial
    python -m venv .env
    source .env/bin/activate

Install rinotype::

    pip install rinohtype

You'll notice that Sphinx and various other components are installed as
dependencies of rinohtype.


Start a new Sphinx project
--------------------------

Use ``sphinx-quickstart`` to bootstrap a new project::

    sphinx-quickstart .

You'll need to answer a few questions. Name the project ``All about me`` when
asked. You can accept any defaults for other questions. Sphinx will create a
set of files ready for you to start working with.

Test your project, by running::

    make html

Sphinx will build the HTML version of the (rather empty) site and inform you
that it can be found in ``_build/html``. Open the ``index.html`` file inside
there in your browser.

Do the same with rinohtype's Sphinx builder::

    make rinoh

which should create a PDF version of the project, as
``_build/rinoh/allaboutme.pdf``. We now have a working project that generates
both HTML and PDF versions of the content, and we can begin developing it
further.
