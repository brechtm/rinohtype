#!/usr/bin/env python

# Build script for Sphinx documentation

import os
import shlex
import shutil
import subprocess
import sys

from collections import OrderedDict


# You can set these variables from the command line.
SPHINXOPTS = os.getenv('SPHINXOPTS', '')
SPHINXBUILD = os.getenv('SPHINXBUILD', 'sphinx-build')
PAPER = os.getenv('PAPER', None)
BUILDDIR = os.getenv('BUILDDIR', '_build')


TARGETS = OrderedDict()


def target(function):
    TARGETS[function.__name__] = function
    return function


# User-friendly check for sphinx-build
def check_sphinx_build():
    with open(os.devnull, 'w') as devnull:
        try:
            if subprocess.call([SPHINXBUILD, '--version'],
                               stdout=devnull, stderr=devnull) == 0:
                return
        except FileNotFoundError:
            pass
    print("The '{0}' command was not found. Make sure you have Sphinx "
          "installed, then set the SPHINXBUILD environment variable to point "
          "to the full path of the '{0}' executable. Alternatively you can "
          "add the directory with the executable to your PATH. If you don't "
          "have Sphinx installed, grab it from http://sphinx-doc.org/)"
          .format(SPHINXBUILD))
    sys.exit(1)


@target
def all():
    """the default target"""
    rinoh()
    return html()


@target
def clean():
    """remove the build directory"""
    shutil.rmtree(BUILDDIR, ignore_errors=True)


def build(builder, success_msg=None, extra_opts=None, outdir=None,
          doctrees=True):
    builddir = os.path.join(BUILDDIR, outdir or builder)
    command = [SPHINXBUILD, '-b', builder]
    if doctrees:
        command.extend(['-d', os.path.join(BUILDDIR, 'doctrees')])
    if extra_opts:
        command.extend(extra_opts)
    command.extend(shlex.split(SPHINXOPTS))
    command.extend(['.', builddir])
    print(' '.join(command))
    if subprocess.call(command) == 0:
        print('Build finished. ' + success_msg.format(builddir))
    else:
        print('Error running {}. Aborting.'.format(SPHINXBUILD))
        sys.exit(1)


@target
def html():
    """make standalone HTML files"""
    return build('html', 'The HTML pages are in {}.')


@target
def dirhtml():
    """make HTML files named index.html in directories"""
    return build('dirhtml', 'The HTML pages are in {}')


@target
def singlehtml():
    """make a single large HTML file"""
    return build('singlehtml', 'The HTML page is in {}.')


@target
def pickle():
    """make pickle files"""
    return build('pickle', 'Now you can process the pickle files.')


@target
def json():
    """make JSON files"""
    return build('json', 'Now you can process the JSON files.')


@target
def htmlhelp():
    """make HTML files and a HTML help project"""
    build('htmlhelp', 'Now you can run HTML Help Workshop with the .hhp '
                      'project file in {}.')
    print('Running HTML Help Workshop...')
    builddir = os.path.join(BUILDDIR, 'htmlhelp')
    rc = subprocess.call(['hhc', os.path.join(builddir, 'rinohtype.hhp')])
    if rc != 1:
        print('Error running HTML Help Workshop. Aborting.')
        sys.exit(1)
    print('HTML Help Workshop finished; the CHM file is in {}.'
          .format(builddir))


@target
def qthelp():
    """make HTML files and a qthelp project"""
    return build('qthelp', 'Now you can run "qcollectiongenerator" with the '
                           '.qhcp project file in {0}, like this: \n'
                           '# qcollectiongenerator {0}/RinohType.qhcp\n'
                           'To view the help file:\n'
                           '# assistant -collectionFile {0}/RinohType.qhc')


@target
def devhelp():
    """make HTML files and a Devhelp project"""
    return build('devhelp', 'To view the help file:\n'
                            '# mkdir -p $HOME/.local/share/devhelp/RinohType\n'
                            '# ln -s {} $HOME/.local/share/devhelp/RinohType\n'
                            '# devhelp')


@target
def epub():
    """make an epub"""
    return build('epub', 'The epub file is in {}.')


@target
def rinoh():
    """make a PDF using rinohtype"""
    return build('rinoh', 'The PDF file is in {}.')


@target
def latex():
    """make LaTeX files, you can set PAPER=a4 or PAPER=letter"""
    extra_opts = ['-D', 'latex_paper_size={}'.format(PAPER)] if PAPER else None
    return build('latex', 'The LaTeX files are in {}.\n'
                          "Run 'make' in that directory to run these through "
                          "(pdf)latex (use the 'latexpdf' target to do that "
                          "automatically).", extra_opts)


@target
def latexpdf():
    """make LaTeX files and run them through pdflatex"""
    rc = latex()
    print('Running LaTeX files through pdflatex...')
    builddir = os.path.join(BUILDDIR, 'latex')
    subprocess.call(['make', '-C', builddir, 'all-pdf'])
    print('pdflatex finished; the PDF files are in {}.'.format(builddir))


@target
def latexpdfja():
    """make LaTeX files and run them through platex/dvipdfmx"""
    rc = latex()
    print('Running LaTeX files through platex and dvipdfmx...')
    builddir = os.path.join(BUILDDIR, 'latex')
    subprocess.call(['make', '-C', builddir, 'all-pdf-ja'])
    print('pdflatex finished; the PDF files are in {}.'.format(builddir))


@target
def text():
    """make text files"""
    return build('text', 'The text files are in {}.')


@target
def man():
    """make manual pages"""
    return build('man', 'The manual pages are in {}.')


@target
def texinfo():
    """make Texinfo files"""
    return build('texinfo', 'The Texinfo files are in {}.\n'
                            "Run 'make' in that directory to run these "
                            "through makeinfo (use the 'info' target to do "
                            "that automatically).")


@target
def info():
    """make Texinfo files and run them through makeinfo"""
    rc = texinfo()
    print('Running Texinfo files through makeinfo...')
    builddir = os.path.join(BUILDDIR, 'texinfo')
    subprocess.call(['make', '-C', builddir, 'info'])
    print('makeinfo finished; the Info files are in {}.'.format(builddir))


@target
def gettext():
    """make PO message catalogs"""
    return build('gettext', 'The message catalogs are in {}.', outdir='locale',
                 doctrees=False)


@target
def changes():
    """make an overview of all changed/added/deprecated items"""
    return build('changes', 'The overview file is in {}.')

@target
def xml():
    """make Docutils-native XML files"""
    return build('xml', 'The XML files are in {}.')


@target
def pseudoxml():
    """make pseudoxml-XML files for display purposes"""
    return build('pseudoxml', 'The pseudo-XML files are in {}.')


@target
def linkcheck():
    """check all external links for integrity"""
    return build('linkcheck', 'Look for any errors in the above output or in '
                              '{}/output.txt.')


@target
def doctest():
    """run all doctests embedded in the documentation (if enabled)"""
    return build('doctest', 'Look at the results in {}/output.txt.')


@target
def help():
    """List all targets"""
    print("Please use '{} <target>' where <target> is one of"
          .format(sys.argv[0]))
    width = max(len(name) for name in TARGETS)
    for name, target in TARGETS.items():
        print('  {name:{width}} {descr}'.format(name=name, width=width,
                                                descr=target.__doc__))


if __name__ == '__main__':
    check_sphinx_build()
    docdir = os.path.dirname(__file__)
    if docdir:
        os.chdir(docdir)
    args = sys.argv[1:] or ['all']
    for arg in args:
        TARGETS[arg]()
