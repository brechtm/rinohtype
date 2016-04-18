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

from rinoh.dimension import CM
from rinoh.index import IndexSection
from rinoh.number import NUMBER, ROMAN_LC
from rinoh.structure import TableOfContentsSection
from rinoh.style import StyleSheetFile
from rinoh.template import (TitlePageTemplate, PageTemplate, DocumentOptions,
                            DocumentTemplate, FixedDocumentPartTemplate,
                            ContentsPartTemplate)

from ...backend import pdf

from ..rst import ReStructuredTextReader

from rinohlib.stylesheets.sphinx import stylesheet as sphinx_stylesheet

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
        rinoh_document.metadata['title'] = doctree.settings.title
        rinoh_document.metadata['author'] = doctree.settings.author
        outfilename = path.join(self.outdir, os_path(targetname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)


DEFAULT_STYLESHEET = sphinx_stylesheet

title_page_template = TitlePageTemplate(top_margin=8 * CM)
page_template = PageTemplate()
DEFAULT_DOCUMENT_PARTS = [FixedDocumentPartTemplate(title_page_template),
                          FixedDocumentPartTemplate(
                              page_template, [TableOfContentsSection()],
                              page_number_format=ROMAN_LC),
                          ContentsPartTemplate(
                              page_template, page_number_format=NUMBER),
                          FixedDocumentPartTemplate(
                              page_template, [IndexSection()])]


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_documents', [], 'env')
    app.add_config_value('rinoh_stylesheet', lambda config: DEFAULT_STYLESHEET,
                         'html')
    app.add_config_value('rinoh_document_parts', DEFAULT_DOCUMENT_PARTS, 'html')
