# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
from os import path

import docutils

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.locale import _
from sphinx.util.console import bold, darkgreen, brown
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import ensuredir, os_path, SEP

from rinoh.dimension import INCH
from rinoh.index import IndexSection
from rinoh.number import NUMBER, ROMAN_LC
from rinoh.paper import LETTER
from rinoh.paragraph import Paragraph
from rinoh.reference import (Variable, Reference, PAGE_NUMBER, TITLE,
                             DOCUMENT_TITLE, DOCUMENT_SUBTITLE, REFERENCE,
                             SECTION_NUMBER, SECTION_TITLE)
from rinoh.structure import TableOfContentsSection
from rinoh.stylesheets import sphinx as sphinx_stylesheet
from rinoh.template import (TitlePageTemplate, PageTemplate, DocumentOptions,
                            DocumentTemplate, FixedDocumentPartTemplate,
                            ContentsPartTemplate)
from rinoh.text import Tab

from ...backend import pdf

from ..rst import ReStructuredTextReader

from . import nodes


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

    def transform_refuris(self, tree):
        """Transform internal refuri targets in reference nodes to refids."""
        def transform_id(id):
            return id if id.startswith('%') else '%' + docname + '#' + id

        for node in tree.traverse():
            if node.tagname == 'start_of_file':
                docname = node['docname']
                continue
            try:
                if 'refid' in node:
                    node['refid'] = transform_id(node['refid'])
                elif 'refuri' in node and node.get('internal', False):
                    node['refid'] = node.attributes.pop('refuri')
                ids, module_ids = [], []
                for id in node['ids']:
                    if id.startswith('module-'):
                        module_ids.append(id)
                    else:
                        ids.append(transform_id(id))
                node['ids'] = ids + module_ids
            except (TypeError, KeyError):
                pass

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
        return largetree

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
            doctree = self.assemble_doctree(docname)
            self.transform_refuris(doctree)

            self.info("rendering... ")
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            self.write_doc(self.config.master_doc, doctree, targetname)
            self.info("done")

    def write_doc(self, docname, doctree, targetname):
        os.chdir(self.srcdir)
        parser = ReStructuredTextReader()
        rinoh_tree = parser.from_doctree(doctree)
        options = DocumentOptions(stylesheet=self.config.rinoh_stylesheet)
        document_parts = self.config.rinoh_document_parts
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


def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph('CHAPTER ' + Reference(section_id, NUMBER, style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE),
                    style='body matter chapter title')


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
        PageTemplate(header_footer_distance=0,
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
        PageTemplate(header_footer_distance=0,
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
    app.add_config_value('rinoh_stylesheet', lambda config: sphinx_stylesheet,
                         'html')
    app.add_config_value('rinoh_paper_size', LETTER, 'html')
    app.add_config_value('rinoh_document_parts', default_document_parts, 'html')
    app.add_config_value('rinoh_logo', None, 'html')
