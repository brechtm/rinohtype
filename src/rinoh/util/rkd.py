from collections.abc import MutableMapping
from weakref import ref



# http://stackoverflow.com/a/3387975/438249
class RefKeyDictionary(MutableMapping):
    """A dictionary that compares keys based on their id (address). Hence, the
    keys can be mutable."""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, obj):
        obj_weakref, value = self.store[id(obj)]
        assert obj_weakref() is obj
        return value

    def __setitem__(self, obj, value):
        self.store[id(obj)] = ref(obj), value

    def __delitem__(self, obj):
        self[obj]   # check the weakref
        del self.store[id(obj)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)
