# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
from os import path

import docutils

from docutils.nodes import GenericNodeVisitor, SkipNode

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.locale import _
from sphinx.util.console import bold, darkgreen, brown
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import ensuredir, os_path, SEP

from rinoh.flowable import StaticGroupedFlowables
from rinoh.highlight import pygments_style_to_stylesheet
from rinoh.index import IndexSection, IndexLabel, IndexEntry
from rinoh.language import Language
from rinoh.paper import A4, LETTER
from rinoh.style import StyleSheet
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            TemplateConfigurationFile)
from rinoh.text import SingleStyledText

from ..rst import ReStructuredTextReader

from . import nodes


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


class RinohBuilder(Builder):
    """Renders to a PDF using rinohtype."""

    name = 'rinoh'
    format = 'pdf'
    supported_image_types = ['application/pdf', 'image/png', 'image/jpeg']

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
        self.info(darkgreen(indexfile) + " ", nonl=1)
        tree = self.env.get_doctree(indexfile)
        tree['docname'] = indexfile
        new_tree = docutils.utils.new_document('<rinoh output>')
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
        self.info()
        self.info("resolving references...")
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

    def init_document_data(self):
        document_data = []
        preliminary_document_data = [list(entry)
                                     for entry in self.config.rinoh_documents]
        if not preliminary_document_data:
            self.warn('no "rinoh_documents" config value found; '
                      'no documents will be written')
            return
        # assign subdirs to titles
        self.titles = []
        for entry in preliminary_document_data:
            docname = entry[0]
            if docname not in self.env.all_docs:
                self.warn('"rinoh_documents" config value references unknown '
                          'document %s' % docname)
                continue
            document_data.append(entry)
            if docname.endswith(SEP + 'index'):
                docname = docname[:-5]
            self.titles.append((docname, entry[2]))
        return document_data

    def write(self, *ignored):
        document_data = self.init_document_data()
        for entry in document_data:
            docname, targetname, title, author = entry[:4]
            toctree_only = entry[4] if len(entry) > 4 else False
            self.info("processing " + targetname + "... ", nonl=1)
            doctree, docnames = self.assemble_doctree(docname, toctree_only)
            self.preprocess_tree(doctree)

            self.info("rendering... ")
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            self.write_doc(self.config.master_doc, doctree, docnames,
                           targetname)
            self.info("done")

    def write_doc(self, docname, doctree, docnames, targetname):
        config = self.config
        suffix, = config.source_suffix
        source_path = os.path.join(self.srcdir, docname + suffix)
        parser = ReStructuredTextReader()
        rinoh_tree = parser.from_doctree(source_path, doctree)
        template_cfg = template_from_config(config, self.confdir, self.warn)
        rinoh_document = template_cfg.document(rinoh_tree)
        extra_indices = StaticGroupedFlowables(self.generate_indices(docnames))
        rinoh_document.insert('back_matter', extra_indices, 0)
        rinoh_logo = config.rinoh_logo
        if rinoh_logo:
            rinoh_document.metadata['logo'] = rinoh_logo
        rinoh_document.metadata['title'] = doctree.settings.title
        rinoh_document.metadata['subtitle'] = ('Release {}'
                                               .format(config.release))
        rinoh_document.metadata['author'] = doctree.settings.author
        outfilename = path.join(self.outdir, os_path(targetname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)


def template_from_config(config, confdir, warn):
    template_cfg = {}
    if isinstance(config.rinoh_template, str):
        tmpl_path = path.join(confdir, config.rinoh_template)
        if path.isfile(tmpl_path):
            template_cfg['base'] = TemplateConfigurationFile(tmpl_path)
            template_cls = template_cfg['base'].template
        else:
           template_cls = DocumentTemplate.from_string(config.rinoh_template)
    elif isinstance(config.rinoh_template, TemplateConfiguration):
        template_cfg['base'] = config.rinoh_template
        template_cls = config.rinoh_template.template
    else:
        template_cls = config.rinoh_template
    if isinstance(config.rinoh_stylesheet, str):
        stylesheet_path = path.join(confdir, config.rinoh_stylesheet)
        stylesheet = StyleSheet.from_string(stylesheet_path
                                            if path.isfile(stylesheet_path)
                                            else config.rinoh_stylesheet)
    else:
        stylesheet = config.rinoh_stylesheet
    if config.pygments_style is not None:
        if stylesheet is not None:
            base = stylesheet
        elif 'base' in template_cfg:
            base = template_cfg['base']['stylesheet']
        else:
            base = template_cls.stylesheet.default_value
        stylesheet = pygments_style_to_stylesheet(config.pygments_style, base)
    if stylesheet is not None:
        template_cfg['stylesheet'] = stylesheet

    language = config.language
    if language:
        try:
            template_cfg['language'] = Language.from_string(language)
        except KeyError:
            warn('The language "{}" is not supported by rinohtype.')

    variables = {}
    if config.rinoh_paper_size:
        variables['paper_size'] = config.rinoh_paper_size

    sphinx_config = template_cls.Configuration('Sphinx conf.py options',
                                               **template_cfg)
    sphinx_config.variables.update(variables)
    return sphinx_config



def fully_qualified_id(docname, id):
    return id if id.startswith('%') else '%' + docname + '#' + id



def info_config_conversion(config_option):
    print("'rinoh_{0}' config variable not set, automatically converting "
          "from 'latex_{0}'".format(config_option))


def default_documents(config):
    def latex_document_to_rinoh_document(entry):
        startdocname, targetname, title, author, documentclass = entry[:5]
        toctree_only = entry[5] if len(entry) > 5 else False
        targetname_root, _ = os.path.splitext(targetname)
        return startdocname, targetname_root, title, author, toctree_only

    info_config_conversion('documents')
    return [latex_document_to_rinoh_document(entry)
            for entry in config.latex_documents]


def default_paper_size(config):
    info_config_conversion('paper_size')
    try:
        return dict(a4paper=A4,
                    letterpaper=LETTER)[config.latex_elements['papersize']]
    except KeyError:
        return dict(a4=A4, letter=LETTER)[config.latex_paper_size]


def default_logo(config):
    info_config_conversion('logo')
    return config.latex_logo


def default_domain_indices(config):
    info_config_conversion('domain_indices')
    return config.latex_domain_indices


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', default_documents, 'env')
    app.add_config_value('rinoh_stylesheet', None, 'html')
    app.add_config_value('rinoh_paper_size', default_paper_size, 'html')
    app.add_config_value('rinoh_logo', default_logo, 'html')
    app.add_config_value('rinoh_domain_indices', default_domain_indices, 'html')
    app.add_config_value('rinoh_template', 'book', 'html')
