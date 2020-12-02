# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import logging

from pathlib import Path

import pytest

from docutils.utils import new_document
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace

from rinoh.document import DocumentTree
from rinoh.frontend.sphinx import (set_document_metadata,
                                   variable_removed_warnings)
from rinoh.language import IT
from rinoh.paper import A4
from rinoh.templates import Book, Article


LOGGER = logging.getLogger(__name__)


def create_sphinx_app(tmp_path, **confoverrides):
    with docutils_namespace():
        confdir = tmp_path / 'confdir'
        confdir.mkdir()
        conf_py = confdir / 'conf.py'
        conf_py.touch()
        app = Sphinx(srcdir=str(tmp_path),
                     confdir=str(confdir),
                     outdir=str(tmp_path / 'output'),
                     doctreedir=str(tmp_path / 'doctrees'),
                     buildername='rinoh',
                     confoverrides=confoverrides)
    return app


def create_document(title='A Title', author='Ann Other', docname='a_name'):
    document = new_document('/path/to/document.rst')
    document.settings.title = title
    document.settings.author = author
    document.settings.docname = docname
    return document


def get_contents_page_size(template_configuration):
    doctree = DocumentTree([])
    doc = template_configuration.document(doctree)
    doc.backend_document = doc.backend.Document(doc.CREATOR)
    part_template = doc.part_templates[2]
    part = part_template.document_part(doc)
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    return page.get_config_value('page_size', doc)


def get_template_cfg(tmp_path, **confoverrides):
    app = create_sphinx_app(tmp_path, **confoverrides)
    return app.builder.template_from_config(LOGGER)


def test_sphinx_config_default(tmp_path):
    template_cfg = get_template_cfg(tmp_path)
    assert template_cfg.template == Book
    assert not template_cfg.keys()
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_latex_elements_papersize_no_effect(tmp_path):
    template_cfg = get_template_cfg(
        tmp_path, latex_elements=dict(papersize='a5paper'))
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_language(tmp_path):
    template_cfg = get_template_cfg(tmp_path, language='it')
    assert template_cfg.template == Book
    assert template_cfg['language'] == IT


def test_sphinx_config_language_not_supported(caplog, tmp_path):
    with caplog.at_level(logging.WARNING):
        template_cfg = get_template_cfg(tmp_path, language='not_supported')
    assert "The language 'not_supported' is not supported" in caplog.text
    assert template_cfg.template == Book
    assert 'language' not in template_cfg


def test_sphinx_config_rinoh_template(tmp_path):
    template_cfg = Article.Configuration('test',
                                         stylesheet='sphinx_article')
    template_cfg = get_template_cfg(tmp_path, rinoh_template=template_cfg)
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (article)')


def test_sphinx_config_rinoh_template_from_entrypoint(tmp_path):
    template_cfg = get_template_cfg(tmp_path, rinoh_template='book')
    assert not template_cfg.keys()
    assert template_cfg.template == Book
    assert template_cfg.get_attribute_value('stylesheet').name == 'Sphinx'


def test_sphinx_config_rinoh_template_from_filename(tmp_path):
    template_cfg_path = str(tmp_path / 'template_cfg.rtt')
    with open(template_cfg_path, 'w') as template_cfg:
        print('[TEMPLATE_CONFIGURATION]', file=template_cfg)
        print('template = book', file=template_cfg)
    template_cfg = get_template_cfg(tmp_path, rinoh_template=template_cfg_path)
    assert not template_cfg.keys()
    assert template_cfg.template == Book
    assert template_cfg.get_attribute_value('stylesheet').name == 'Sphinx'


def test_sphinx_set_document_metadata(tmp_path):
    app = create_sphinx_app(tmp_path, release='1.0', rinoh_template='book')
    template_cfg = app.builder.template_from_config(LOGGER)
    docutils_tree = create_document()
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    set_document_metadata(rinoh_doc, app.config, docutils_tree)
    assert rinoh_doc.metadata['title'] == 'A Title'
    assert rinoh_doc.metadata['subtitle'] == 'Release 1.0'
    assert rinoh_doc.metadata['author'] == 'Ann Other'
    assert 'logo' not in rinoh_doc.metadata
    assert 'date' in rinoh_doc.metadata


def test_sphinx_set_document_metadata_subtitle(tmp_path):
    expected_subtitle = 'A subtitle'
    app = create_sphinx_app(tmp_path, rinoh_metadata={
                            'subtitle': expected_subtitle})
    template_cfg = app.builder.template_from_config(LOGGER)
    docutil_tree = create_document()
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    set_document_metadata(rinoh_doc, app.config, docutil_tree)
    assert expected_subtitle == rinoh_doc.metadata['subtitle']


def test_sphinx_set_document_metadata_logo(tmp_path):
    expected_logo = 'logo.png'
    app = create_sphinx_app(tmp_path, rinoh_logo='logo.png')
    template_cfg = app.builder.template_from_config(LOGGER)
    docutil_tree = create_document()
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    set_document_metadata(rinoh_doc, app.config, docutil_tree)
    assert expected_logo == rinoh_doc.metadata['logo']


def test_sphinx_default_deprecation_warning(caplog, tmp_path):
    app = create_sphinx_app(tmp_path)
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert caplog.text == ''


def test_sphinx_rinoh_stylesheet_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_stylesheet="sphinx")
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_stylesheet' has been removed" in caplog.text


def test_sphinx_rinoh_paper_size_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_paper_size='A4')
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_paper_size' has been removed" in caplog.text
