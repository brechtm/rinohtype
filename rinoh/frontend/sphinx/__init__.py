# This file is part of RinohType, the Python document preparation system.
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

from rinoh.dimension import INCH
from rinoh.index import IndexSection, IndexLabel, IndexEntry
from rinoh.number import NUMBER, ROMAN_LC
from rinoh.paper import LETTER
from rinoh.paragraph import Paragraph
from rinoh.reference import (Variable, Reference, PAGE_NUMBER, TITLE,
                             DOCUMENT_TITLE, DOCUMENT_SUBTITLE,
                             SECTION_NUMBER, SECTION_TITLE)
from rinoh.structure import TableOfContentsSection
from rinoh.style import StyleSheetFile
from rinoh.stylesheets import sphinx as sphinx_stylesheet
from rinoh.template import (TitlePageTemplate, PageTemplate, DocumentOptions,
                            DocumentTemplate, FixedDocumentPartTemplate,
                            ContentsPartTemplate)
from rinoh.text import Tab, SingleStyledText

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
    """Renders to a PDF using RinohType."""

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

    def assemble_doctree(self, indexfile):
        docnames = set([indexfile])
        self.info(darkgreen(indexfile) + " ", nonl=1)
        tree = self.env.get_doctree(indexfile)
        tree['docname'] = indexfile
        # extract toctree nodes from the tree and put them in a fresh document
        new_tree = docutils.utils.new_document('<rinoh output>')
        for node in tree.traverse(addnodes.toctree):
            new_tree += node
        largetree = inline_all_toctrees(self, docnames, indexfile, new_tree,
                                        darkgreen)
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
        preliminary_document_data = [list(x)
                                     for x in self.config.rinoh_documents]
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
            docname, targetname, title, author = entry
            self.info("processing " + targetname + "... ", nonl=1)
            doctree, docnames = self.assemble_doctree(docname)
            self.preprocess_tree(doctree)

            self.info("rendering... ")
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            self.write_doc(self.config.master_doc, doctree, docnames,
                           targetname)
            self.info("done")

    def write_doc(self, docname, doctree, docnames, targetname):
        os.chdir(self.srcdir)
        parser = ReStructuredTextReader()
        rinoh_tree = parser.from_doctree(doctree)
        options = DocumentOptions(stylesheet=self.config.rinoh_stylesheet)
        document_parts = self.config.rinoh_document_parts
        indices = list(self.generate_indices(docnames))
        # TODO: more cleanly inject the indices into the document part template
        document_parts[-1].flowables = indices + document_parts[-1].flowables
        rinoh_document = DocumentTemplate(rinoh_tree, document_parts,
                                          options=options, backend=pdf)
        if self.config.rinoh_logo:
            rinoh_document.metadata['logo'] = self.config.rinoh_logo
        rinoh_document.metadata['title'] = doctree.settings.title
        rinoh_document.metadata['subtitle'] = ('Release {}'
                                               .format(self.config.release))
        rinoh_document.metadata['author'] = doctree.settings.author
        outfilename = path.join(self.outdir, os_path(targetname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)


def fully_qualified_id(docname, id):
    return id if id.startswith('%') else '%' + docname + '#' + id


def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph('CHAPTER ' + Reference(section_id, NUMBER, style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE),
                    style='body matter chapter title')


def default_stylesheet(config):
    return StyleSheetFile(sphinx_stylesheet.filename, sphinx_stylesheet.matcher,
                          pygments_style=config.pygments_style or 'sphinx')


def default_document_parts(config):
    page_kwargs = dict(page_size=config.rinoh_paper_size,
                       left_margin=1*INCH, right_margin=1*INCH,
                       top_margin=1*INCH, bottom_margin=1*INCH)
    title_page_template = TitlePageTemplate(**page_kwargs)
    front_matter_right_page =\
        PageTemplate(header_footer_distance=0,
                     header_text=None,
                     footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                     chapter_title_height=2.5 * INCH,
                     chapter_title_flowables=
                        front_matter_section_title_flowables,
                     **page_kwargs)
    front_matter_left_page =\
        PageTemplate(header_footer_distance=0,
                     header_text=None,
                     footer_text=Variable(PAGE_NUMBER),
                     **page_kwargs)
    content_right_page = \
        PageTemplate(header_footer_distance=0,
                     header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                                  + ', ' + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(SECTION_NUMBER(2))
                                  + '.  ' + Variable(SECTION_TITLE(2))
                                  + Tab() + Tab() + Variable(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                     chapter_title_height=2.4*INCH,
                     chapter_title_flowables=
                         body_matter_chapter_title_flowables,
                     **page_kwargs)
    content_left_page = \
        PageTemplate(header_footer_distance=0,
                     header_text=(Variable(DOCUMENT_TITLE) + ', '
                                  + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab() +
                                  'Chapter ' + Variable(SECTION_NUMBER(1))
                                  + '.  ' + Variable(SECTION_TITLE(1))),
                     **page_kwargs)
    back_matter_right_page =\
        PageTemplate(columns=2,
                     header_footer_distance=0,
                     header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                                  + ', ' + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(SECTION_TITLE(1))
                                  + Tab() + Tab() + Variable(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                     chapter_title_height=2.5 * INCH,
                     chapter_title_flowables=
                        front_matter_section_title_flowables,
                     **page_kwargs)
    back_matter_left_page =\
        PageTemplate(columns=2,
                     header_footer_distance=0,
                     header_text=(Variable(DOCUMENT_TITLE) + ', '
                                  + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab()
                                  + Variable(SECTION_TITLE(1))),
                     **page_kwargs)
    return [FixedDocumentPartTemplate([], title_page_template),
            FixedDocumentPartTemplate([TableOfContentsSection()],
                                      front_matter_right_page,
                                      front_matter_left_page,
                                      page_number_format=ROMAN_LC),
            ContentsPartTemplate(content_right_page, content_left_page,
                                 page_number_format=NUMBER),
            FixedDocumentPartTemplate([IndexSection()],
                                      back_matter_right_page,
                                      back_matter_left_page)]


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', [], 'env')
    app.add_config_value('rinoh_stylesheet', default_stylesheet, 'html')
    app.add_config_value('rinoh_paper_size', LETTER, 'html')
    app.add_config_value('rinoh_document_parts', default_document_parts, 'html')
    app.add_config_value('rinoh_logo', None, 'html')
    app.add_config_value('rinoh_domain_indices', True, 'html')
