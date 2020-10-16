# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.document import DocumentTree, FakeContainer
from rinoh.flowable import StaticGroupedFlowables
from rinoh.image import Image
from rinoh.paragraph import Paragraph
from rinoh.reference import ReferencingParagraph
from rinoh.templates import Article


stylesheet = None
document = None


def test_select_by_id():
    paragraph1 = Paragraph('A paragraph with an ID.', id='par')
    paragraph2 = Paragraph('A paragraph with another ID.', id='another')
    paragraph3 = Paragraph('A paragraph without ID.')

    selector1 = Paragraph.like(id='par')
    selector2 = Paragraph.like(id='another')
    selector3 = Paragraph

    assert selector1.match(paragraph1, stylesheet, document)
    assert selector2.match(paragraph2, stylesheet, document)
    assert selector3.match(paragraph1, stylesheet, document)
    assert selector3.match(paragraph2, stylesheet, document)
    assert selector3.match(paragraph3, stylesheet, document)

    assert not selector1.match(paragraph2, stylesheet, document)
    assert not selector1.match(paragraph3, stylesheet, document)
    assert not selector2.match(paragraph1, stylesheet, document)
    assert not selector2.match(paragraph3, stylesheet, document)


def test_select_groupedflowables():
    empty = StaticGroupedFlowables([])
    not_empty = StaticGroupedFlowables([empty])

    empty_selector = StaticGroupedFlowables.like(empty=True)
    not_empty_selector = StaticGroupedFlowables.like(empty=False)

    assert empty_selector.match(empty, stylesheet, document)
    assert not_empty_selector.match(not_empty, stylesheet, document)

    assert not empty_selector.match(not_empty, stylesheet, document)
    assert not not_empty_selector.match(empty, stylesheet, document)


def test_select_image():
    nix_image1 = Image('dir/image.png')
    nix_image2 = Image('dir/subdir/image.png')
    win_image1 = Image(r'dir\image.png')
    win_image2 = Image(r'dir\subdir\image.png')
    nix_selector1 = Image.like(filename='dir/image.png')
    nix_selector2 = Image.like(filename='dir/subdir/image.png')
    win_selector1 = Image.like(filename=r'dir\image.png')
    win_selector2 = Image.like(filename=r'dir\subdir\image.png')
    assert nix_selector1.match(nix_image1, stylesheet, document)
    assert nix_selector2.match(nix_image2, stylesheet, document)
    assert nix_selector1.match(win_image1, stylesheet, document)
    assert nix_selector2.match(win_image2, stylesheet, document)
    assert win_selector1.match(nix_image1, stylesheet, document)
    assert win_selector2.match(nix_image2, stylesheet, document)
    assert win_selector1.match(win_image1, stylesheet, document)
    assert win_selector2.match(win_image2, stylesheet, document)

    assert not nix_selector1.match(nix_image2, stylesheet, document)
    assert not nix_selector2.match(nix_image1, stylesheet, document)
    assert not win_selector1.match(nix_image2, stylesheet, document)
    assert not win_selector2.match(nix_image1, stylesheet, document)


def test_select_referencingparagraph():
    paragraph = Paragraph('A paragraph with some text.', style='boxed')
    paragraph.classes.append('cls1')
    paragraph_with_id = Paragraph('A paragraph with an ID.', id='par')
    paragraph_with_id.classes.extend(['cls2', 'cls3'])
    refpar = ReferencingParagraph(paragraph)
    refpar_by_id = ReferencingParagraph('par')
    doctree = DocumentTree([paragraph, paragraph_with_id, refpar, refpar_by_id])
    document = Article(doctree)
    container = FakeContainer(document)
    document.prepare(container)
    stylesheet = document.stylesheet

    refpar_match1 = ReferencingParagraph.like(target_style='boxed')
    refpar_match2 = ReferencingParagraph.like(target_has_class='cls1')
    refpar_match3 = ReferencingParagraph.like(target_style='boxed',
                                              target_has_class='cls1')
    refpar_by_id_match = ReferencingParagraph.like(target_has_classes=['cls2', 'cls3'])
    bad_match = ReferencingParagraph.like(target_style='boxed',
                                          target_has_class='cls2')

    assert refpar_match1.match(refpar, stylesheet, document)
    assert refpar_match2.match(refpar, stylesheet, document)
    assert refpar_match3.match(refpar, stylesheet, document)
    assert refpar_by_id_match.match(refpar_by_id, stylesheet, document)

    assert not refpar_match1.match(refpar_by_id, stylesheet, document)
    assert not refpar_match2.match(refpar_by_id, stylesheet, document)
    assert not refpar_match3.match(refpar_by_id, stylesheet, document)
    assert not refpar_by_id_match.match(refpar, stylesheet, document)

    assert not bad_match.match(paragraph, stylesheet, document)
    assert not bad_match.match(paragraph_with_id, stylesheet, document)
    assert not bad_match.match(refpar, stylesheet, document)
    assert not bad_match.match(refpar_by_id, stylesheet, document)
