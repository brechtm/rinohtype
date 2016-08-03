# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from rinoh.attribute import Attribute, Bool, Var
from rinoh.dimension import PT
from rinoh.paper import A5
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            PageTemplate, ContentsPartTemplate)


class MyDocumentTemplate(DocumentTemplate):
    class Configuration(TemplateConfiguration):
        a = Attribute(Bool, True, 'flag A')
        b = Attribute(Bool, True, 'flag B')
        c = Attribute(Bool, True, 'flag C')

        page_tmpl = PageTemplate(page_size=Var('paper_size'),
                                 column_spacing=1*PT)

    parts = [ContentsPartTemplate('contents', Configuration.page_tmpl)]


def test_template_configuration():
    conf = MyDocumentTemplate.Configuration(a=False)
    assert conf.get_option('a') == False
    assert conf.get_option('b') == True
    assert conf.get_option('c') == True
    assert conf.get_template_option('page_tmpl', 'columns') == 1
    assert conf.get_template_option('page_tmpl', 'column_spacing') == 1*PT


def test_template_configuration_base():
    base_conf = MyDocumentTemplate.Configuration(a=False)
    conf = MyDocumentTemplate.Configuration(base=base_conf, b=False)
    conf('page_tmpl', column_spacing=10*PT)
    assert conf.get_option('a') == False
    assert conf.get_option('b') == False
    assert conf.get_option('c') == True
    assert conf.get_template_option('page_tmpl', 'columns') == 1
    assert conf.get_template_option('page_tmpl', 'column_spacing') == 10*PT


def test_template_configuration_var():
    conf = MyDocumentTemplate.Configuration(a=False,
                                            paper_size=A5)
    assert conf.get_option('paper_size') == A5
    assert conf.get_template_option('page_tmpl', 'page_size') == A5


def test_template_configuration_var2():
    conf = MyDocumentTemplate.Configuration(a=False,
                                            paper_size=A5)
    conf('page_tmpl', columns=2)
    assert conf.get_option('paper_size') == A5
    assert conf.get_template_option('page_tmpl', 'page_size') == A5
