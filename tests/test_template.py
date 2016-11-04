# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from rinoh.attribute import Attribute, Bool, Var
from rinoh.dimension import PT
from rinoh.document import DocumentTree
from rinoh.paper import A5
from rinoh.template import DocumentTemplate, PageTemplate, ContentsPartTemplate


class MyDocumentTemplate(DocumentTemplate):
    a = Attribute(Bool, True, 'flag A')
    b = Attribute(Bool, True, 'flag B')
    c = Attribute(Bool, True, 'flag C')

    parts = ['contents']

    contents = ContentsPartTemplate()

    contents_page = PageTemplate(page_size=Var('paper_size'),
                                 column_spacing=1*PT)


document_tree = DocumentTree([])


def test_template_configuration():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    doc = MyDocumentTemplate(document_tree, configuration=conf)
    assert doc.get_option('a') == False
    assert doc.get_option('b') == True
    assert doc.get_option('c') == True
    assert doc.get_template_option('contents_page', 'columns') == 1
    assert doc.get_template_option('contents_page', 'column_spacing') == 1*PT


def test_template_configuration_base():
    base_conf = MyDocumentTemplate.Configuration('base', a=False)
    conf = MyDocumentTemplate.Configuration('test', base=base_conf, b=False)
    conf('contents_page', column_spacing=10*PT)
    doc = MyDocumentTemplate(document_tree, configuration=conf)
    assert doc.get_option('a') == False
    assert doc.get_option('b') == False
    assert doc.get_option('c') == True
    assert doc.get_template_option('contents_page', 'columns') == 1
    assert doc.get_template_option('contents_page', 'column_spacing') == 10*PT


def test_template_configuration_unsupported_option():
    with pytest.raises(TypeError):
        MyDocumentTemplate.Configuration('test', unsupported=666)


def test_template_configuration_var():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    conf.variables['paper_size'] = A5
    doc = MyDocumentTemplate(document_tree, configuration=conf)
    assert doc.get_option('a') == False
    assert doc.get_option('b') == True
    assert doc.get_option('c') == True
    assert doc.get_template_option('contents_page', 'page_size') == A5


def test_template_configuration_var2():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    conf('contents_page', columns=2)
    conf.variables['paper_size'] = A5
    doc = MyDocumentTemplate(document_tree, configuration=conf)
    assert doc.get_option('a') == False
    assert doc.get_option('b') == True
    assert doc.get_option('c') == True
    assert doc.get_template_option('contents_page', 'page_size') == A5
