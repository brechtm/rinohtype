#
import pytest
from rinoh.util import PeekIterator


def testNormal():
    a = [1, 2, 3]
    peekIterator = PeekIterator(a)
    print(f"Normal: -  next:{peekIterator.next}")

    for i in peekIterator:
        print(f"Normal: {i}, next:{peekIterator.next}")


def testSingle():
    a = [1]
    peekIterator = PeekIterator(a)
    print(f"Single: -  next:{peekIterator.next}")

    for i in peekIterator:
        print(f"Single: {i}, next:{peekIterator.next}")


def testEmpty():
    a = []
    peekIterator = PeekIterator(a)
    print(f"Empty: -  next:{peekIterator.next}")

    for i in peekIterator:
        print(f"Empty: {i}, next:{peekIterator.next}")
