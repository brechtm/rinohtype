import pytest

from rinoh.index import IndexSee, IndexSeeAlso, IndexTarget, IndexTerm


class DummyDocument(object):
    def __init__(self):
        self.ids_by_element = {}
        self.index_entries = {}

    def register_element(self, _element):
        return None


class DummyFlowableTarget(object):
    def __init__(self, document):
        self.document = document


def _node(targets=None, subentries=None, sees=None, see_alsoes=None):
    return {'targets': targets or [],
            'subentries': subentries or {},
            'sees': sees or [],
            'see_alsoes': see_alsoes or []}


def _prepare(document, index_terms):
    index_target = IndexTarget(index_terms)
    index_target.id = 'index-target'
    index_target.prepare(DummyFlowableTarget(document))
    return index_target


def test_index_see_construction():
    assert tuple(IndexSee('term', 'reference')) == ('term', 'reference')
    assert tuple(IndexSeeAlso('term', 'reference')) == ('term', 'reference')


def test_target_index_entries():
    document = DummyDocument()
    index_target = _prepare(document, [
        IndexTerm('single_term1', 'single_term2', 'single_term3'),
        IndexTerm('single_term4'),
        IndexTerm('pair_term1', 'pair_term2'),
        IndexTerm('pair_term2', 'pair_term1'),
        IndexTerm('module', 'search' + ' ' + 'path'),
        IndexTerm('search', 'path' + ', ' + 'module'),
        IndexTerm('path', 'module' + ' ' + 'search'),
    ])

    single_term1 = ('single_term1', _node(
        subentries={
            'single_term2': ('single_term2', _node(
                subentries={
                    'single_term3': ('single_term3', _node(
                        targets=[(IndexTerm('single_term1', 'single_term2',
                                            'single_term3'), index_target)]
                    ))
                }
            ))
        }
    ))
    single_term4 = ('single_term4', _node(
        targets=[(IndexTerm('single_term4'), index_target)]
    ))
    pair_term1 = ('pair_term1', _node(
        subentries={
            'pair_term2': ('pair_term2', _node(
                targets=[(IndexTerm('pair_term1', 'pair_term2'),
                          index_target)]
            ))
        }
    ))
    pair_term2 = ('pair_term2', _node(
        subentries={
            'pair_term1': ('pair_term1', _node(
                targets=[(IndexTerm('pair_term2', 'pair_term1'),
                          index_target)]
            ))
        }
    ))
    module = ('module', _node(
        subentries={
            'search path': ('search path', _node(
                targets=[(IndexTerm('module', 'search' + ' ' + 'path'),
                          index_target)]
            ))
        }
    ))
    search = ('search', _node(
        subentries={
            'path, module': ('path, module', _node(
                targets=[(IndexTerm('search', 'path' + ', ' + 'module'),
                          index_target)]
            ))
        }
    ))
    path = ('path', _node(
        subentries={
            'module search': ('module search', _node(
                targets=[(IndexTerm('path', 'module' + ' ' + 'search'),
                          index_target)]
            ))
        }
    ))

    assert document.index_entries == {'single_term1': single_term1,
                                      'single_term4': single_term4,
                                      'pair_term1': pair_term1,
                                      'pair_term2': pair_term2,
                                      'module': module,
                                      'search': search,
                                      'path': path}


def test_target_index_cross_references():
    document = DummyDocument()
    index_target = _prepare(document, [
        IndexTerm('term'),
        IndexSee('term', 'synonym_term'),
        IndexSeeAlso('term', 'related_term'),
        IndexSeeAlso('other_term', 'another_term'),
    ])

    assert document.index_entries == {
        'term': ('term', _node(targets=[(IndexTerm('term'), index_target)],
                               sees=['synonym_term'],
                               see_alsoes=['related_term'])),
        'other_term': ('other_term', _node(see_alsoes=['another_term'])),
    }


def test_index_terms_are_not_interpreted_as_metadata():
    # index terms resembling internal bookkeeping must not be dropped
    document = DummyDocument()
    _prepare(document, [IndexTerm('_index_see'), IndexTerm('_index_seealso'),
                        IndexTerm('targets')])
    entry_data = document.index_entries['_index_see'][1]

    assert 'targets' in document.index_entries
    assert entry_data['targets'][0][0] == IndexTerm('_index_see')
    assert entry_data['sees'] == []
    assert entry_data['see_alsoes'] == []


def _index_entry_parts(entry_type, entry_name):
    """Split an index entry value as the Sphinx frontend does"""
    sphinx_nodes = pytest.importorskip('rinoh.frontend.sphinx.nodes')
    return sphinx_nodes.Index._index_entry_parts(entry_type, entry_name)


def test_index_entry_parts():
    assert _index_entry_parts('single', 'term') == ['term']
    assert _index_entry_parts('single', 'term; subterm') == \
        ['term', 'subterm']
    assert _index_entry_parts('pair', 'one; two') == ['one', 'two']
    assert _index_entry_parts('triple', 'one; two; three') == \
        ['one', 'two', 'three']


def test_index_entry_parts_with_semicolons_in_reference():
    # only the first semicolon separates the term from the reference
    assert _index_entry_parts('see', 'term; first; second') == \
        ['term', 'first; second']
    assert _index_entry_parts('seealso', ' term ; reference ') == \
        ['term', 'reference']
