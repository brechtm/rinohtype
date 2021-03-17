# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from rinoh import register_template
from rinoh.attribute import Attribute, Bool, Var, OverrideDefault
from rinoh.dimension import PT
from rinoh.document import DocumentTree
from rinoh.paper import A5
from rinoh.reference import (Field, SECTION_NUMBER, SECTION_TITLE, PAGE_NUMBER,
                             NUMBER_OF_PAGES)
from rinoh.template import (DocumentTemplate, PageTemplate,
                            ContentsPartTemplate, TemplateConfigurationFile)
from rinoh.text import SingleStyledText


class MyDocumentTemplate(DocumentTemplate):
    a = Attribute(Bool, True, 'flag A')
    b = Attribute(Bool, True, 'flag B')
    c = Attribute(Bool, True, 'flag C')

    parts = OverrideDefault(['contents'])

    contents = ContentsPartTemplate()

    contents_page = PageTemplate(page_size=Var('paper_size'),
                                 column_spacing=1*PT)


register_template('my_document_template', MyDocumentTemplate)


document_tree = DocumentTree([])


def create_document(configuration):
    doc = MyDocumentTemplate(document_tree, configuration=configuration)
    doc.backend_document = doc.backend.Document(doc.CREATOR)
    return doc


def test_template_configuration():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    doc = create_document(conf)
    assert doc.get_option('a') is False
    assert doc.get_option('b') is True
    assert doc.get_option('c') is True
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('columns', doc) == 1
    assert page.get_config_value('column_spacing', doc) == 1*PT


def test_template_configuration_base():
    base_conf = MyDocumentTemplate.Configuration('base', a=False)
    conf = MyDocumentTemplate.Configuration('test', base=base_conf, b=False)
    conf('contents_page', column_spacing=10*PT)
    doc = create_document(conf)
    assert doc.get_option('a') is False
    assert doc.get_option('b') is False
    assert doc.get_option('c') is True
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('columns', doc) == 1
    assert page.get_config_value('column_spacing', doc) == 10*PT


CONFIGURATION_A = """
[TEMPLATE_CONFIGURATION]
name = configuration A
template = my_document_template
;stylesheet = ../stylesheet/stylesheet.rts

a = false
b = false

[VARIABLES]
my_header_text = '{SECTION_NUMBER(1)} {SECTION_TITLE(1)}'

[contents_page]
header_text = $(my_header_text)
footer_text = '{PAGE_NUMBER} / {NUMBER_OF_PAGES}'
"""

CONFIGURATION_B = """
[TEMPLATE_CONFIGURATION]
name = configuration B
base = a.rtt

a = true
c = false

[VARIABLES]
my_header_text = 'Configuration B Header'

"""


def test_template_configuration_file():
    with TemporaryDirectory() as tmpdir:
        dir = Path(tmpdir)
        with (dir / 'a.rtt').open('w') as a:
            a.write(CONFIGURATION_A)
        conf = TemplateConfigurationFile(a.name)
    assert conf.template == MyDocumentTemplate
    header_text = conf.get_variable(PageTemplate, 'header_text',
                                    Var('my_header_text'))
    expected_header_text = (Field(SECTION_NUMBER(1)) + ' '
                            + Field(SECTION_TITLE(1)))
    assert header_text == expected_header_text
    doc = create_document(conf)
    assert doc.get_option('a') is False
    assert doc.get_option('b') is False
    assert doc.get_option('c') is True
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('columns', doc) == 1
    assert page.get_config_value('column_spacing', doc) == 1*PT
    # the retrieved config values have a parent (Header/Footer), so we can't
    # use == but compare their repr (which doesn't include the parent)
    assert (repr(page.get_config_value('header_text', doc))
            == repr(expected_header_text))
    assert (repr(page.get_config_value('footer_text', doc))
            == repr(Field(PAGE_NUMBER) + ' / ' + Field(NUMBER_OF_PAGES)))


def test_template_configuration_file_base():
    with TemporaryDirectory() as tmpdir:
        dir = Path(tmpdir)
        with (dir / 'a.rtt').open('w') as a:
            a.write(CONFIGURATION_A)
        with (dir / 'b.rtt').open('w') as b:
            b.write(CONFIGURATION_B)
        conf = TemplateConfigurationFile(b.name)
    assert conf.template == MyDocumentTemplate
    header_text = conf.get_variable(PageTemplate, 'header_text',
                                    Var('my_header_text'))
    expected_header_text = SingleStyledText('Configuration B Header')
    assert header_text == expected_header_text
    doc = create_document(conf)
    assert doc.get_option('a') is True
    assert doc.get_option('b') is False
    assert doc.get_option('c') is False
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('columns', doc) == 1
    assert page.get_config_value('column_spacing', doc) == 1*PT
    # the retrieved config values have a parent (Header/Footer), so we can't
    # use == but compare their repr (which doesn't include the parent)
    assert (repr(page.get_config_value('header_text', doc))
            == repr(expected_header_text))
    assert (repr(page.get_config_value('footer_text', doc))
            == repr(Field(PAGE_NUMBER) + ' / ' + Field(NUMBER_OF_PAGES)))


def test_template_configuration_unsupported_option():
    with pytest.raises(TypeError):
        MyDocumentTemplate.Configuration('test', unsupported=666)


def test_template_configuration_var():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    conf.variables['paper_size'] = A5
    doc = create_document(conf)
    assert doc.get_option('a') is False
    assert doc.get_option('b') is True
    assert doc.get_option('c') is True
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('page_size', doc) == A5


def test_template_configuration_var2():
    conf = MyDocumentTemplate.Configuration('test', a=False)
    conf('contents_page', columns=2)
    conf.variables['paper_size'] = A5
    doc = create_document(conf)
    assert doc.get_option('a') is False
    assert doc.get_option('b') is True
    assert doc.get_option('c') is True
    part_template, = doc.part_templates
    part = part_template.document_part(doc, 'number')
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    assert page.template_name == 'contents_page'
    assert page.get_config_value('page_size', doc) == A5
