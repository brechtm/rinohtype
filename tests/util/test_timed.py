import pytest
from rinoh.util import timed
import time

@timed
def doSomething(sec):
    print(f"sleeping for {sec}")
    time.sleep(sec)



def testSimple():
    doSomething(1)

