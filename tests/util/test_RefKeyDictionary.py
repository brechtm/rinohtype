# This unit test exists partially to explore how RefKeyDictionary works.
# TODO: do we even need this class?

import pytest
from rinoh.util import RefKeyDictionary


class Foo:
    def __init__(self, value):
        self.value = value


def testConstruction():
    one = Foo("one")
    two = Foo("two")
    foos = {one: 1, two: 2}
    print("Foos:", foos)
    simple = dict(foos)

    rkd = RefKeyDictionary(foos)
    print(f"Simple dictionary: {simple}")
    print(f"RefKeyDictionary: {rkd}")

    one.value = "uno"

    for item in simple.items():
        print("item:", item)

    for item in rkd.items():
        print("item:", item)  # Gives KeyError

    return rkd

