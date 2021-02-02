# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re

from copy import copy
from os import path
from pathlib import Path

import docutils

from docutils.nodes import GenericNodeVisitor, SkipNode

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.errors import SphinxError
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
                logger.warning("'rinoh_documents' config value references"
                               " unknown document '{}'".format(docname))
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
            logger.warning("No 'rinoh_documents' config value found; no"
                           " documents will be written")
            document_data = []
        document_data = [entry for entry in document_data
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
        # resolve :ref:s to other PDF files -- we can't add a cross-reference,
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

    def generate_indices(self, docnames, indices_config):
        def index_flowables(content):
            for section, entries in content:
                yield IndexLabel(str(section))
                for (name, subtype, docname, anchor, _, _, _) in entries:
                    target_ids = ([anchor] if anchor else None)
                    entry_name = SingleStyledText(name, style='domain')
                    yield IndexEntry(entry_name,
                                     level=2 if subtype == 2 else 1,
                                     target_ids=target_ids)

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
        data = copy(document_data)
        target = data.pop('target')
        logger.info("processing %s... ", target, nonl=1)
        rinoh_document = self.construct_rinohtype_document(data)
        outfilename = path.join(self.outdir, os_path(target))
        ensuredir(path.dirname(outfilename))
        logger.info("rendering... ")
        rinoh_document.render(outfilename)
        logger.info("done")

    def construct_rinohtype_document(self, document_data):
        doc = document_data.pop('doc')
        toctree_only = document_data.pop('toctree_only', False)
        template = document_data.pop('template', 'book')
        domain_indices = document_data.pop('domain_indices', True)

        doctree, docnames = self.assemble_doctree(doc, toctree_only)
        self.preprocess_tree(doctree)
        self.post_process_images(doctree)
        rinoh_tree = from_doctree(doctree, sphinx_builder=self)
        rinoh_template = self.template_configuration(template, logger)
        rinoh_document = rinoh_template.document(rinoh_tree)
        extra_indices = StaticGroupedFlowables(
            self.generate_indices(docnames, domain_indices))
        # TODO: use out-of-line flowables?
        rinoh_document.insert('back_matter', extra_indices, 0)
        self.set_document_metadata(rinoh_document, document_data)
        return rinoh_document

    def template_configuration(self, template, logger):
        config = self.config
        contructor_args = {}
        if isinstance(template, str):
            tmpl_path = path.join(self.confdir, template)
            if path.isfile(tmpl_path):
                base = TemplateConfigurationFile(template, source=self)
                contructor_args['base'] = base
                template_cls = contructor_args['base'].template
            else:
                template_cls = DocumentTemplate.from_string(template)
        elif isinstance(template, TemplateConfiguration):
            contructor_args['base'] = template
            template_cls = template.template
        else:
            template_cls = template

        language = config.language
        if language:
            try:
                contructor_args['language'] = Language.from_string(language)
            except KeyError:
                logger.warning("The language '{}' is not supported by"
                               " rinohtype.".format(language))

        sphinx_config = template_cls.Configuration('Sphinx conf.py options',
                                                   **contructor_args)
        return sphinx_config

    def set_document_metadata(self, rinoh_document, metadata):
        rinoh_document.metadata.pop('date')     # Sphinx provides a default
        rinoh_document.metadata.update(metadata)
        if 'logo' in rinoh_document.metadata:
            logo_path = Path(rinoh_document.metadata['logo'])
            if not logo_path.is_absolute():
                rinoh_document.metadata['logo'] = self.confdir / logo_path
        for key, default in METADATA_DEFAULTS.items():
            if key in rinoh_document.metadata:
                continue
            rinoh_document.metadata[key] = default(self.config)


METADATA_DEFAULTS = dict(
    title=lambda cfg: '{} documentation'.format(cfg.project),
    subtitle=lambda cfg: '{} {}'.format(_('Release'), cfg.release),
    author=lambda cfg: cfg.author,
    date=lambda cfg: (cfg.today or format_date(cfg.today_fmt or _('%b %d, %Y'),
                                               language=cfg.language))
)


def fully_qualified_id(docname, id):
    return id if id.startswith('%') else '%' + docname + '#' + id


def rinoh_document_to_document_data(entry, logger):
    if type(entry) in (list, tuple):
        entry = list_to_document_data(entry, logger)
    for key in ('doc', 'target'):
        if key not in entry:
            raise SphinxError("'{}' key is missing from rinoh_documents"
                              " entry".format(key))
    return entry


def list_to_document_data(entry, logger):
    logger.warning("'rinoh_documents' entry converted from list. In future"
                   " versions this shall be deprecated.")
    keys = ('doc', 'target', 'title', 'author', 'toctree_only')
    document_data = dict(zip(keys, entry))
    document_data['template'] = 'book'
    return document_data


def latex_document_to_document_data(entry, logger):
    logger.warning("'rinoh_documents' config variable not set, automatically"
                   " converting from 'latex_documents'")
    startdocname, targetname, title, author, documentclass = entry[:5]
    toctree_only = entry[5] if len(entry) > 5 else False
    targetname_root, _ = os.path.splitext(targetname)
    return list_to_document_data([startdocname, targetname_root, title, author,
                                  toctree_only], logger)


def variable_removed_warnings(config, logger):
    def warn(variable, thing, where):
        message = ("Support for '{}' has been removed. Instead, please"
                   " specify the {} to use in your {}.")
        logger.warning(message.format(variable, thing, where))
    if config.rinoh_stylesheet is not None:
        warn('rinoh_stylesheet', 'style sheet', 'template configuration')
    if config.rinoh_paper_size is not None:
        warn('rinoh_paper_size', 'paper size', 'template configuration')
    if config.rinoh_template is not None:
        warn('rinoh_template', 'template', "'rinoh_documents' entries")
    if config.rinoh_logo is not None:
        warn('rinoh_logo', 'logo', "'rinoh_documents' entries")
    if config.rinoh_domain_indices is not None:
        warn('rinoh_domain_indices', 'domain indices',
             "'rinoh_documents' entries")
    if config.rinoh_metadata is not None:
        warn('rinoh_metadata', 'metadata values', "'rinoh_documents' entries")


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', None, 'env', (dict, list))
    # the following are no longer supported and have are ignored
    app.add_config_value('rinoh_logo', None, 'html')
    app.add_config_value('rinoh_domain_indices', None, 'html')
    app.add_config_value('rinoh_template', None, 'html')
    app.add_config_value('rinoh_metadata', None, 'html')
    app.add_config_value('rinoh_stylesheet', None, 'html')
    app.add_config_value('rinoh_paper_size', None, 'html')
    return dict(version=rinoh_version,
                parallel_read_safe=True)
