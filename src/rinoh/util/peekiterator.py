

class PeekIterator(object):
    """An _iterator that allows inspecting the next element"""

    def __init__(self, iterable):
        self.next = None
        self._iterator = iter(iterable)
        self._at_end = False
        self._advance()

    def _advance(self):
        result = self.next
        try:
            self.next = next(self._iterator)
        except StopIteration:
            self.next = None
            self._at_end = True
        return result

    def __iter__(self):
        return self

    def __next__(self):
        if self._at_end:
            raise StopIteration  # OK to raise this; not a generator (no yield)
        return self._advance()
