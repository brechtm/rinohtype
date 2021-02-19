
.. testsetup:: my_document

    import os, shutil, sys, tempfile

    lastdir = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)
    shutil.copy(os.path.join(lastdir, 'my_article.rtt'), tmpdir)
    with open('my_document.rst', 'w') as rst_file:
        rst_file.write('Hello World!')
    sys.path.insert(0, tmpdir)      # mimic python calling script directly

.. testcleanup:: my_document

    os.chdir(lastdir)
    shutil.rmtree(tmpdir)
