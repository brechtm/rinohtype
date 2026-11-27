# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.dimension import PT
from rinoh.layout import (Container, EndOfContainer, FlowContext,
                          FlowablesContainer, InlineDownExpandingContainer,
                          MaybeContainer, CONTENT, HEADER_FOOTER)


class FakeDocumentPart(object):
    document = None


class FakePage(Container):
    """A page that is not backed by an output document"""

    register_with_parent = False

    def __init__(self):
        self._document_part = FakeDocumentPart()
        self.width = self.height = 100*PT
        self.context = FlowContext(self, None)
        self._empty = True
        self.footnote_space = object()
        self.float_space = object()
        super().__init__('PAGE', None, 0*PT, 0*PT, 100*PT, 100*PT)

    def empty_canvas(self):
        pass

    @property
    def document_part(self):
        return self._document_part

    @property
    def document(self):
        return self.document_part.document


@pytest.fixture
def page():
    return FakePage()


def nested_containers(parent, depth=10):
    """Wrap `parent` in containers that are not placed on a page"""
    container = parent
    for i in range(depth):
        container = InlineDownExpandingContainer('NESTED', container,
                                                 0*PT, 100*PT,
                                                 advance_parent=False,
                                                 place=False)
    return container


def test_mark_page_nonempty_content(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    nested_containers(content).mark_page_nonempty()
    assert not page._empty


def test_mark_page_nonempty_header_footer(page):
    header = FlowablesContainer('header', HEADER_FOOTER, page, 0*PT, 0*PT,
                                100*PT, 50*PT)
    # a flowable in the header does not make the page's content nonempty
    nested_containers(header).mark_page_nonempty()
    assert page._empty


def test_footnote_space_from_page(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    container = nested_containers(content)
    assert container.footnote_space is page.footnote_space
    assert container.float_space is page.float_space


def test_missing_page_attribute(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    del page.footnote_space
    with pytest.raises(AttributeError):
        content.footnote_space


def test_cursor_includes_advancing_sub_container(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    inline = InlineDownExpandingContainer('inline', content, 0*PT, 100*PT)
    inline.advance(10*PT)
    assert content.cursor == pytest.approx(10)
    inline.advance(5*PT)
    assert content.cursor == pytest.approx(15)
    # the advance is folded into the parent's own cursor when it advances
    content.advance(5*PT)
    assert content.cursor == pytest.approx(20)
    assert content._child is None


def test_discarded_sub_container_leaves_no_advance(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    inline = InlineDownExpandingContainer('inline', content, 0*PT, 100*PT)
    inline.advance(10*PT)
    content._discard(inline)
    assert content.cursor == pytest.approx(0)


def test_failed_maybe_container_rolls_back(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)

    class State(object):
        initial = True

    with pytest.raises(EndOfContainer):
        with MaybeContainer(content) as maybe_container:
            maybe_container.advance(10*PT)
            raise EndOfContainer(State())
    assert content.cursor == pytest.approx(0)


def test_inline_container_limit_follows_parent(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    inline = InlineDownExpandingContainer('inline', content, 0*PT, 100*PT)
    assert inline.remaining_height == pytest.approx(100)
    content._limit = float(content._limit) - 40    # the page geometry shrunk
    assert inline.remaining_height == pytest.approx(60)


def test_advance_beyond_limit(page):
    content = FlowablesContainer('content', CONTENT, page, 0*PT, 0*PT,
                                 100*PT, 100*PT)
    assert content.advance2(60*PT)
    assert not content.advance2(50*PT)
    assert content.cursor == pytest.approx(60)
    assert content.advance2(50*PT, ignore_overflow=True)
    assert content.cursor == pytest.approx(100)
    with pytest.raises(Exception):
        content.advance(10*PT)
