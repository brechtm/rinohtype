# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
from os import path

import docutils

from sphinx.builders import Builder
from sphinx.util.console import bold, darkgreen, brown
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import ensuredir, os_path

from ...backend import pdf
from ...dimension import PT
from ...style import StyleSheet
from ...styles import ParagraphStyle
from ..rst import ReStructuredTextParser, CustomElement

from rinohlib.templates.book import Book, BookOptions

from . import nodes


for cls_name in nodes.__all__:
    cls = getattr(nodes, cls_name)
    CustomElement.MAPPING[cls.__name__.lower()] = cls


class RinohBuilder(Builder):
    """Renders to a PDF using RinohType."""

    name = 'rinoh'
    format = 'pdf'
    supported_image_types = ['application/pdf']

    # def init(self):
    #     pass

    def get_outdated_docs(self):
        return 'all documents'

    def get_target_uri(self, docname, typ=None):
        return docname

    # def get_relative_uri(self, from_, to, typ=None):
    #     # ignore source path
    #     return self.get_target_uri(to, typ)

    def prepare_writing(self, docnames):
        # toc = self.env.get_toctree_for(self.config.master_doc, self, False)
        pass

    def assemble_doctree(self):
        master = self.config.master_doc
        tree = self.env.get_doctree(master)
        tree = inline_all_toctrees(self, set(), master, tree, darkgreen)
        tree['docname'] = master
        self.env.resolve_references(tree, master, self)
        self.fix_refuris(tree)
        return tree

    def fix_refuris(self, tree):
        # fix refuris with double anchor
        fname = self.config.master_doc #+ self.out_suffix
        for refnode in tree.traverse(docutils.nodes.reference):
            if 'refuri' not in refnode:
                continue
            refuri = refnode['refuri']
            hashindex = refuri.find('#')
            if hashindex < 0:
                continue
            refnode['refuri'] = refuri[hashindex+1:]
            # import pdb; pdb.set_trace()
            continue
            hashindex = refuri.find('#', hashindex+1)
            if hashindex >= 0:
                refnode['refuri'] = fname + refuri[hashindex:]

    def write(self, *ignored):
        docnames = self.env.all_docs

        self.info(bold('preparing documents... '), nonl=True)
        self.prepare_writing(docnames)
        self.info('done')

        self.info(bold('assembling single document... '), nonl=True)
        doctree = self.assemble_doctree()
        self.info()
        self.info(bold('writing... '))
        self.write_doc_serialized(self.config.master_doc, doctree)
        self.write_doc(self.config.master_doc, doctree)
        self.info('done')

    def write_doc(self, docname, doctree):
        os.chdir(self.srcdir)
        parser = ReStructuredTextParser()
        rinoh_tree = parser.from_doctree(doctree)
        rinoh_document = Book(rinoh_tree, backend=pdf,
                              options=self.config.rinoh_manual_options)
        outfilename = path.join(self.outdir, os_path(docname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)

    # def finish(self):
    #     pass


def setup(app):
    app.add_builder(RinohBuilder)
    app.add_config_value('rinoh_manual_options', BookOptions(), None)
