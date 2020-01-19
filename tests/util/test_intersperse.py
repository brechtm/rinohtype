import pytest
from rinoh.util import intersperse
import time

separator = "."
letters = [127, 0, 0, 1]


def testSimple():

    for i in intersperse(letters, separator):
        print(i, end="")
