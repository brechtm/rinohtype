# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re

from os import path
from pathlib import Path

import docutils

from docutils.nodes import GenericNodeVisitor, SkipNode

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.locale import _
from sphinx.util.console import bold, darkgreen, brown
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import ensuredir, os_path, SEP
from sphinx.util import logging
from sphinx.util.i18n import format_date

from rinoh.attribute import Source
from rinoh.flowable import StaticGroupedFlowables
from rinoh.index import IndexSection, IndexLabel, IndexEntry
from rinoh.language import Language
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            TemplateConfigurationFile)
from rinoh.text import SingleStyledText
from rinoh import __version__ as rinoh_version

from rinoh.frontend.rst import from_doctree
from rinoh.util import cached

from . import nodes


logger = logging.getLogger(__name__)


class RinohTreePreprocessor(GenericNodeVisitor):
    """Preprocess the docutils document tree to prepare it for mapping to the
    rinohtype document tree"""

    def __init__(self, document, builder):
        super().__init__(document)
        self.default_highlight_language = builder.config.highlight_language
        self.highlight_stack = [self.default_highlight_language]
        self.current_docname = None

    def default_visit(self, node):
        try:
            if 'refid' in node:
                node['refid'] = fully_qualified_id(self.current_docname,
                                                   node['refid'])
            elif 'refuri' in node and node.get('internal', False):
                node['refid'] = node.attributes.pop('refuri')
            ids, module_ids = [], []
            for id in node['ids']:
                if id.startswith('module-'):
                    module_ids.append(id)
                else:
                    ids.append(fully_qualified_id(self.current_docname, id))
            node['ids'] = ids + module_ids
        except (TypeError, KeyError):
            pass

    def default_departure(self, node):
        pass

    def visit_start_of_file(self, node):
        self.current_docname = node['docname']
        self.highlight_stack.append(self.default_highlight_language)

    def depart_start_of_file(self, node):
        self.highlight_stack.pop()

    def visit_highlightlang(self, node):
        self.highlight_stack[-1] = node.get('lang')
        raise SkipNode

    def visit_rubric(self, node):
        if node.children[0].astext() in ('Footnotes', _('Footnotes')):
            node.tagname = 'footnotes-rubric'  # mapped to a DummyFlowable
            raise SkipNode

    def visit_literal_block(self, node):
        self.default_visit(node)
        if 'language' not in node.attributes:
            node.attributes['language'] = self.highlight_stack[-1]


class RinohBuilder(Builder, Source):
    """Renders to a PDF using rinohtype."""

    name = 'rinoh'
    format = 'pdf'
    supported_image_types = ['application/pdf', 'image/png', 'image/jpeg']
    supported_remote_images = False

    @property
    def root(self):
        return Path(self.confdir)

    @property
    def titles(self):
        def entry_mapping(entry):
            doc = re.sub(SEP + 'index$', SEP, entry['doc'])
            title = entry['title']
            return doc, title
        document_data = self.document_data(logger)
        return [entry_mapping(entry) for entry in document_data]

    @cached  # cached to avoid logging duplicate warnings
    def document_data(self, logger):
        def known_document_reference(docname):
            if docname not in self.env.all_docs:
                logger.warning('"rinoh_documents" config value references unknown '
                               'document %s' % docname)
                return False
            return True

        config = self.config
        if config.rinoh_documents:
            document_data = [rinoh_document_to_document_data(entry, logger)
                             for entry in config.rinoh_documents]
        elif config.latex_documents:
            document_data = [latex_document_to_document_data(entry, logger)
                             for entry in config.latex_documents]
        else:
            logger.warning('no "rinoh_documents" config value found; '
                           'no documents will be written')
            document_data = []
        document_data = [entry
                         for entry in document_data
                         if known_document_reference(entry['doc'])]
        return document_data

    def get_outdated_docs(self):
        return 'all documents'

    def get_target_uri(self, docname, typ=None):
        return '%' + docname

    def get_relative_uri(self, from_, to, typ=None):
        # ignore source
        return self.get_target_uri(to, typ)

    def preprocess_tree(self, tree):
        """Transform internal refuri targets in reference nodes to refids and
        transform footnote rubrics so that they do not end up in the output"""
        visitor = RinohTreePreprocessor(tree, self)
        tree.walkabout(visitor)

    def prepare_writing(self, docnames):
        # toc = self.env.get_toctree_for(self.config.master_doc, self, False)
        pass

    def assemble_doctree(self, indexfile, toctree_only):
        docnames = set([indexfile])
        logger.info(darkgreen(indexfile) + " ", nonl=1)
        tree = self.env.get_doctree(indexfile)
        tree['docname'] = indexfile
        new_tree = docutils.utils.new_document(tree['source'])
        if toctree_only:
            # extract toctree nodes from the tree and put them in a
            # fresh document
            for node in tree.traverse(addnodes.toctree):
                new_tree += node
        else:
            for node in tree.children:
                if node.tagname == 'section':
                    for child in node.children:
                        if child.tagname != 'title':
                            new_tree += child
                else:
                    new_tree += node
        largetree = inline_all_toctrees(self, docnames, indexfile, new_tree,
                                        darkgreen, [indexfile])
        largetree['docname'] = indexfile
        logger.info("resolving references...")
        self.env.resolve_references(largetree, indexfile, self)
        # resolve :ref:s to distant tex files -- we can't add a cross-reference,
        # but append the document name
        for pendingnode in largetree.traverse(addnodes.pending_xref):
            docname = pendingnode['refdocname']
            sectname = pendingnode['refsectname']
            newnodes = [nodes.emphasis(sectname, sectname)]
            for subdir, title in self.titles:
                if docname.startswith(subdir):
                    newnodes.append(nodes.Text(_(' (in '), _(' (in ')))
                    newnodes.append(nodes.emphasis(title, title))
                    newnodes.append(nodes.Text(')', ')'))
                    break
            else:
                pass
            pendingnode.replace_self(newnodes)
        return largetree, docnames

    def generate_indices(self, docnames):
        def index_flowables(content):
            for section, entries in content:
                yield IndexLabel(str(section))
                for (name, subtype, docname, anchor, _, _, _) in entries:
                    target_ids = ([anchor] if anchor else None)
                    entry_name = SingleStyledText(name, style='domain')
                    yield IndexEntry(entry_name, level=2 if subtype == 2 else 1,
                                     target_ids=target_ids)

        indices_config = self.config.rinoh_domain_indices
        if indices_config:
            for domain in self.env.domains.values():
                for indexcls in domain.indices:
                    indexname = '%s-%s' % (domain.name, indexcls.name)
                    if isinstance(indices_config, list):
                        if indexname not in indices_config:
                            continue
                    content, collapsed = indexcls(domain).generate(docnames)
                    if not content:
                        continue
                    index_section_label = str(indexcls.localname)
                    yield IndexSection(SingleStyledText(index_section_label),
                                       index_flowables(content))

    def write(self, *ignored):
        variable_removed_warnings(self.config, logger)
        document_data = self.document_data(logger)
        for entry in document_data:
            self.write_document(entry)

    def write_document(self, document_data):
        targetname = document_data['target']
        logger.info("processing " + targetname + "... ", nonl=1)
        doctree, docnames = self.assemble_doctree(document_data['doc'],
                                document_data.get('toctree_only', False))
        self.preprocess_tree(doctree)
        self.post_process_images(doctree)

        logger.info("rendering... ")
        rinoh_tree = from_doctree(doctree, sphinx_builder=self)
        rinoh_template = self.template_from_config(logger)
        rinoh_document = rinoh_template.document(rinoh_tree)
        extra_indices = StaticGroupedFlowables(self.generate_indices(docnames))
        # TODO: use out-of-line flowables?
        rinoh_document.insert('back_matter', extra_indices, 0)
        self.set_document_metadata(rinoh_document, document_data)
        outfilename = path.join(self.outdir, os_path(targetname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)

        logger.info("done")

    def template_from_config(self, logger):
        config = self.config
        template_cfg = {}
        if isinstance(config.rinoh_template, str):
            tmpl_path = path.join(self.confdir, config.rinoh_template)
            if path.isfile(tmpl_path):
                base = TemplateConfigurationFile(config.rinoh_template,
                                                 source=self)
                template_cfg['base'] = base
                template_cls = template_cfg['base'].template
            else:
                template_cls = DocumentTemplate.from_string(
                    config.rinoh_template)
        elif isinstance(config.rinoh_template, TemplateConfiguration):
            template_cfg['base'] = config.rinoh_template
            template_cls = config.rinoh_template.template
        else:
            template_cls = config.rinoh_template

        language = config.language
        if language:
            try:
                template_cfg['language'] = Language.from_string(language)
            except KeyError:
                logger.warning("The language '{}' is not supported by rinohtype."
                               .format(language))

        sphinx_config = template_cls.Configuration('Sphinx conf.py options',
                                                   **template_cfg)
        return sphinx_config

    def set_document_metadata(self, rinoh_document, document_data):
        metadata = rinoh_document.metadata
        if self.config.rinoh_logo:
            rinoh_logo = Path(self.config.rinoh_logo)
            if not rinoh_logo.is_absolute():
                rinoh_logo = self.confdir / rinoh_logo
            metadata['logo'] = rinoh_logo
        metadata['title'] = document_data.get('title')
        metadata['subtitle'] = document_data.get('subtitle', _('Release') + ' {}'.format(self.config.release))
        metadata['author'] = document_data.get('author')
        date = (self.config.today
                or format_date(self.config.today_fmt or _('%b %d, %Y'),
                               language=self.config.language))
        metadata['date'] = date
        metadata.update(self.config.rinoh_metadata)


def fully_qualified_id(docname, id):
    return id if id.startswith('%') else '%' + docname + '#' + id


def rinoh_document_to_document_data(entry, logger):
    if type(entry) in (list, tuple):
        return list_to_document_data(entry, logger)
    return dict(entry)


def list_to_document_data(entry, logger):
    logger.warning(
        "'rinoh_documents' converted from list. In future versions this shall be deprecated.")
    keys = ("doc", "target", "title", "author", "toctree_only")
    document_data = dict(zip(keys, entry))
    document_data['template'] = 'book'
    return document_data


def latex_document_to_document_data(entry, logger):
    logger.warning("'rinoh_documents' config variable not set, automatically converting "
                   "from 'latex_documents'")
    startdocname, targetname, title, author, documentclass = entry[:5]
    toctree_only = entry[5] if len(entry) > 5 else False
    targetname_root, _ = os.path.splitext(targetname)
    return list_to_document_data([startdocname, targetname_root, title, author, toctree_only], logger)


def variable_removed_warnings(config, logger):
    message = ("Support for '{}' has been removed. Instead, please specify"
               " the {} to use in your template configuration.")
    if config.rinoh_stylesheet:
        logger.warning(message.format('rinoh_stylesheet', 'style sheet'))
    if config.rinoh_paper_size:
        logger.warning(message.format('rinoh_paper_size', 'paper size'))


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', None, 'env')
    app.add_config_value('rinoh_logo', None, 'html')
    app.add_config_value('rinoh_domain_indices', True, 'html')
    app.add_config_value('rinoh_template', 'book', 'html')
    app.add_config_value('rinoh_metadata', dict(), 'html')
    app.add_config_value('rinoh_stylesheet', None, 'html')
    app.add_config_value('rinoh_paper_size', None, 'html')
    return dict(version=rinoh_version,
                parallel_read_safe=True)
