import pytest
from rinoh.util import intersperse
import time


def testIntersperse():
    separator = "."
    letters = [127, 0, 0, 1]

    for i in intersperse(letters, separator):
        print(i, end="")

    localhost = list(intersperse(letters, separator))

    assert [127, ".", 0, ".", 0, ".", 1] == localhost
