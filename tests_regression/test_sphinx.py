# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from regression import render_rst

from sphinx.application import Sphinx
from rinoh.frontend.sphinx import nodes    # load the Sphinx docutils nodes


def sphinx_render(source, filename, tmpdir):
    # register Sphinx directives and roles
    Sphinx(srcdir=tmpdir.strpath, confdir=None, outdir=tmpdir.strpath,
           doctreedir=tmpdir.strpath, buildername='dummy', status=None)
    render_rst(source, filename, tmpdir)



def test_centered(tmpdir):
    source = ('',
              '.. centered:: A centered paragraph.'
              '')
    sphinx_render(source, 'centered', tmpdir)


def test_hlist(tmpdir):
    source = ('.. hlist::',
              '   :columns: 3',
              '',
              '   * A list of',
              '   * short items',
              '   * that should be',
              '   * displayed',
              '   * horizontally')
    sphinx_render(source, 'hlist', tmpdir)


def test_inline_markup(tmpdir):
    source = ('Inline Markup roles:',
              '',
              ':abbr:          :abbr:`LIFO (last-in, first-out)` :abbr:`KISS`',
              ':command:       :command:`rm`',
              ':dfn:           :dfn:`definition`',
              ':file:          :file:`README.txt` :file:`Makefile`',
              ':guilabel:      :guilabel:`&Cancel`',
              ':kbd:           :kbd:`Control-x`',
              ':mailheader:    :mailheader:`Content-Type`',
              ':makevar:       :makevar:`var`',
              ':manpage:       :manpage:`ls(1)`',
              ':menuselection: :menuselection:`Menu --> Item`',
              ':mimetype:      :mimetype:`png`',
              ':newsgroup:     :newsgroup:`comp.lang.python`',
              ':program:       :program:`rinoh`',
              ':regexp:        :regexp:`.*`',
              ':samp:          :samp:`print 1+{variable}`')
    sphinx_render(source, 'inline_markup', tmpdir)
