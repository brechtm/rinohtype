# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from os import path

from sphinx.builders import Builder
from sphinx.util.osutil import ensuredir, os_path

from ...backend import pdf
from ..rst import ReStructuredTextParser, CustomElement

from rinohlib.templates.manual import Manual
from rinohlib.stylesheets.ieee import styles as stylesheet

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

    def write_doc(self, docname, doctree):
        parser = ReStructuredTextParser()
        rinoh_tree = parser.from_doctree(doctree)
        rinoh_document = Manual(rinoh_tree, stylesheet, backend=pdf,
                                title=rinoh_tree.get('title'))
        outfilename = path.join(self.outdir, os_path(docname))
        ensuredir(path.dirname(outfilename))
        rinoh_document.render(outfilename)

    # def finish(self):
    #     pass


def setup(app):
    app.add_builder(RinohBuilder)
