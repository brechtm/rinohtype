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
from rinoh.number import NUMBER
from rinoh.paper import A4, LETTER
from rinoh.paragraph import Paragraph
from rinoh.reference import Reference, TITLE
from rinoh.style import StyleSheet
from rinoh.template import DocumentTemplate
from rinoh.text import SingleStyledText

from ...backend import pdf

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
        rinoh_document_template = config.rinoh_document_template
        template = (DocumentTemplate.from_string(rinoh_document_template)
                    if isinstance(rinoh_document_template, str)
                    else rinoh_document_template)
        if isinstance(self.config.rinoh_stylesheet, str):
            stylesheet = StyleSheet.from_string(self.config.rinoh_stylesheet)
        elif self.config.rinoh_stylesheet is None:
            stylesheet = template.Configuration.stylesheet.default_value
        else:
            stylesheet = self.config.rinoh_stylesheet
        if config.pygments_style is not None:
            stylesheet = pygments_style_to_stylesheet(config.pygments_style,
                                                      stylesheet)
        paper_size = config.rinoh_paper_size
        base_config = template.Configuration(paper_size=paper_size,
                                             stylesheet=stylesheet)
        if config.rinoh_template_configuration is not None:
            template_configuration = config.rinoh_template_configuration
            if template_configuration.base is None:
                template_configuration.base = base_config
        else:
            template_configuration = base_config
        rinoh_document = template(rinoh_tree,
                                  configuration=template_configuration,
                                  backend=pdf)
        extra_indices = StaticGroupedFlowables(self.generate_indices(docnames))
        rinoh_document.insert('indices', extra_indices, 0)
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


def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph('CHAPTER ' + Reference(section_id, NUMBER, style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE),
                    style='body matter chapter title')


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', default_documents, 'env')
    app.add_config_value('rinoh_stylesheet', None, 'html')
    app.add_config_value('rinoh_paper_size', default_paper_size, 'html')
    app.add_config_value('rinoh_logo', default_logo, 'html')
    app.add_config_value('rinoh_domain_indices', default_domain_indices, 'html')
    app.add_config_value('rinoh_document_template', 'book', 'html')
    app.add_config_value('rinoh_template_configuration', None, 'html')
