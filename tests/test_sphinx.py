# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import logging

from pathlib import Path

import pytest

from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util.docutils import docutils_namespace
from sphinx.util.i18n import format_date

from rinoh.document import DocumentTree
from rinoh.frontend.sphinx import variable_removed_warnings
from rinoh.language import IT
from rinoh.paper import A4
from rinoh.templates import Book, Article


LOGGER = logging.getLogger(__name__)


def create_sphinx_app(tmp_path, all_docs=('index',), **confoverrides):
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
        app.env.all_docs.update({doc: 0 for doc in all_docs})
    return app


def document_data_dict(**kwargs):
    document_data = {'doc': 'index', 'target': 'rinoh_doc', 'template': 'book',
                     'title': 'Title', 'author': 'Author',
                     'toctree_only': False}
    document_data.update(kwargs)
    return document_data


def get_contents_page_size(template_configuration):
    doctree = DocumentTree([])
    doc = template_configuration.document(doctree)
    doc.backend_document = doc.backend.Document(doc.CREATOR)
    part_template = doc.part_templates[2]
    part = part_template.document_part(doc)
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    return page.get_config_value('page_size', doc)


def get_template_configuration(tmp_path, template='book',
                               **sphinx_config_overrides):
    app = create_sphinx_app(tmp_path, **sphinx_config_overrides)
    return app.builder.template_configuration(template, LOGGER)


def test_sphinx_config_default(tmp_path):
    template_cfg = get_template_configuration(tmp_path)
    assert template_cfg.template == Book
    assert not template_cfg.keys()
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_latex_elements_papersize_no_effect(tmp_path):
    template_cfg = get_template_configuration(
        tmp_path, latex_elements=dict(papersize='a5paper'))
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_latex_option_no_effect(tmp_path):
    confoverrides = dict(latex_logo='logo.png', latex_domain_indices=False)
    app = create_sphinx_app(tmp_path, **confoverrides)
    assert app.config.latex_logo == 'logo.png'
    assert app.config.rinoh_logo is None
    assert app.config.latex_domain_indices == False
    assert app.config.rinoh_domain_indices is None


def test_sphinx_config_language(tmp_path):
    template_cfg = get_template_configuration(tmp_path, language='it')
    assert template_cfg.template == Book
    assert template_cfg['language'] == IT


def test_sphinx_config_language_not_supported(caplog, tmp_path):
    with caplog.at_level(logging.WARNING):
        template_cfg = get_template_configuration(tmp_path,
                                                  language='not_supported')
    assert "The language 'not_supported' is not supported" in caplog.text
    assert template_cfg.template == Book
    assert 'language' not in template_cfg


def test_sphinx_config_template_from_instance(tmp_path):
    base = Article.Configuration('test', stylesheet='sphinx_base14')
    template_cfg = get_template_configuration(tmp_path, template=base)
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (PDF Core Fonts)')


def test_sphinx_config_template_from_entrypoint(tmp_path):
    template_cfg = get_template_configuration(tmp_path, template='article')
    assert not template_cfg.keys()
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (article)')


def test_sphinx_config_template_from_filename(tmp_path):
    template_cfg_path = str(tmp_path / 'template_cfg.rtt')
    with open(template_cfg_path, 'w') as template_cfg:
        print('[TEMPLATE_CONFIGURATION]', file=template_cfg)
        print('template = article', file=template_cfg)
    template_cfg = get_template_configuration(tmp_path, template_cfg_path)
    assert not template_cfg.keys()
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (article)')


def test_sphinx_config_template_from_class(tmp_path):
    template_cfg = get_template_configuration(tmp_path, template=Article)
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (article)')


def test_sphinx_rinoh_documents_logo_relative(tmp_path):
    expected_logo = 'logo.png'
    document_data = document_data_dict(logo=expected_logo)
    app = create_sphinx_app(tmp_path, rinoh_documents=[document_data])
    template_cfg = app.builder.template_configuration('book', LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    assert Path(app.confdir) / expected_logo == rinoh_doc.metadata['logo']


def test_sphinx_rinoh_documents_logo_absolute(tmp_path):
    expected_logo = tmp_path / 'confdir' / 'logo.png'
    document_data = document_data_dict(logo=expected_logo)
    app = create_sphinx_app(tmp_path, rinoh_documents=[document_data])
    template_cfg = app.builder.template_configuration('book', LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    assert expected_logo == rinoh_doc.metadata['logo']


def test_sphinx_default_removed_warning(caplog, tmp_path):
    app = create_sphinx_app(tmp_path)
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert caplog.text == ''


def test_sphinx_rinoh_template_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_template="article")
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_template' has been removed" in caplog.text


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


def test_sphinx_rinoh_logo_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_logo='logo.png')
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_logo' has been removed" in caplog.text


def test_sphinx_rinoh_domain_indices_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_domain_indices=False)
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_domain_indices' has been removed" in caplog.text


def test_sphinx_rinoh_metadata_removed(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, rinoh_metadata=dict(bla=5))
    with caplog.at_level(logging.WARNING):
        variable_removed_warnings(app.config, LOGGER)
    assert "Support for 'rinoh_metadata' has been removed" in caplog.text


def test_sphinx_rinoh_documents_missing_doc(tmp_path):
    rinoh_documents = [dict(target='target')]
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents)
    with pytest.raises(SphinxError) as error:
        app.builder.document_data(LOGGER)
    assert "'doc' key is missing from rinoh_documents entry" in str(error)


def test_sphinx_rinoh_documents_missing_target(tmp_path):
    rinoh_documents = [dict(doc='index')]
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents)
    with pytest.raises(SphinxError) as error:
        app.builder.document_data(LOGGER)
    assert "'target' key is missing from rinoh_documents entry" in str(error)


def test_sphinx_rinoh_documents_defaults(tmp_path):
    rinoh_documents = [dict(doc='index', target='target')]
    today_fmt = '%b %d, %Y'
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents,
                            project='Project', release='1.2', author='Georgie',
                            today_fmt=today_fmt, language='en-US')

    template_cfg = app.builder.template_configuration('book', LOGGER)
    document_data, = app.builder.document_data(LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    assert rinoh_doc.metadata['title'] == 'Project documentation'
    assert rinoh_doc.metadata['subtitle'] == 'Release 1.2'
    assert rinoh_doc.metadata['author'] == 'Georgie'
    assert rinoh_doc.metadata['date'] == format_date(today_fmt,
                                                     language='en-US')


def test_sphinx_rinoh_documents_override_defaults(tmp_path):
    expected = dict(title='Title', subtitle='A subtitle',
                    author='Me', date='Today')
    document_data = document_data_dict(**expected)
    app = create_sphinx_app(tmp_path, rinoh_documents=[document_data])
    template_cfg = app.builder.template_configuration('book', LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    for key, value in expected.items():
        assert rinoh_doc.metadata[key] == value


def test_sphinx_rinoh_documents_extra(tmp_path):
    expected_extra = 'Extra'
    document_data = document_data_dict(extra=expected_extra)
    app = create_sphinx_app(tmp_path, rinoh_documents=[document_data])
    template_cfg = app.builder.template_configuration('book', LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    assert expected_extra == rinoh_doc.metadata['extra']


def test_sphinx_rinoh_documents(tmp_path):
    rinoh_document = document_data_dict()
    app = create_sphinx_app(tmp_path, rinoh_documents=[rinoh_document])
    document_data, = app.builder.document_data(LOGGER)
    assert document_data == rinoh_document
    template_cfg = app.builder.template_configuration('book', LOGGER)
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    app.builder.set_document_metadata(rinoh_doc, document_data)
    assert 'logo' not in rinoh_doc.metadata
    assert 'date' in rinoh_doc.metadata


def test_sphinx_rinoh_documents_unknown_document(caplog, tmp_path):
    rinoh_documents = [['not_here', 'rinoh_doc', 'Title', 'Author', False]]
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents)
    with caplog.at_level(logging.WARNING):
        document_data = app.builder.document_data(LOGGER)
    assert not document_data
    assert ("'rinoh_documents' config value references unknown document"
            " 'not_here'") in caplog.text


def test_sphinx_rinoh_documents_list(caplog, tmp_path):
    rinoh_documents = [['index', 'rinoh_doc', 'Title', 'Author', False]]
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents)
    with caplog.at_level(logging.WARNING):
        document_data = app.builder.document_data(LOGGER)
    assert document_data == [document_data_dict()]
    assert "'rinoh_documents' entry converted from list" in caplog.text


def test_sphinx_document_data_no_rinoh_documents(caplog, tmp_path):
    app = create_sphinx_app(tmp_path, latex_documents=None)
    with caplog.at_level(logging.WARNING):
        document_data = app.builder.document_data(LOGGER)
    assert not document_data
    assert "No 'rinoh_documents' config value found" in caplog.text


def test_sphinx_document_data_latex_documents_fallback(caplog, tmp_path):
    latex_documents = [['index', 'doc.tex', 'Title', 'Author', 'manual', True]]
    rinoh_documents = [document_data_dict(target='doc', toctree_only=True)]
    app = create_sphinx_app(tmp_path, latex_documents=latex_documents)
    with caplog.at_level(logging.WARNING):
        document_data = app.builder.document_data(LOGGER)
    assert document_data == rinoh_documents
    assert ("'rinoh_documents' config variable not set, automatically"
            " converting from 'latex_documents'") in caplog.text
    assert "'rinoh_documents' entry converted from list." in caplog.text


def test_sphinx_document_data_latex_documents_ignored(caplog, tmp_path):
    latex_documents = [['index', 'doc.tex', 'Title', 'Author', 'manual', True]]
    rinoh_documents = [document_data_dict()]
    app = create_sphinx_app(tmp_path, rinoh_documents=rinoh_documents,
                            latex_documents=latex_documents)
    with caplog.at_level(logging.WARNING):
        document_data = app.builder.document_data(LOGGER)
    assert document_data == rinoh_documents
    assert ("'rinoh_documents' config variable not set, automatically"
            " converting from 'latex_documents'") not in caplog.text


def test_sphinx_titles(caplog, tmp_path):
    rinoh_documents = [document_data_dict(),
                       document_data_dict(doc='other/index',
                                          title="Other Title")]
    all_docs = [doc['doc'] for doc in rinoh_documents]
    app = create_sphinx_app(tmp_path, all_docs=all_docs,
                            rinoh_documents=rinoh_documents)
    titles = app.builder.titles
    assert titles == [('index', "Title"), ('other/', "Other Title")]
