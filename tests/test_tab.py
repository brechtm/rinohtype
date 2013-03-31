

import unittest


from pyte.dimension import PT
from pyte.paragraph import TabStop, Line, LEFT, RIGHT, CENTER
from pyte.text import Tab, Spacer


class StyledTextStub(object):
    def __init__(self, width):
        self.width = float(width)

    def warn(self, message):
        pass

    def hyphenate(self):
        yield self, None


class TestTab(unittest.TestCase):

    def test__tab_space_exceeded(self):
        tab_stops = [TabStop(30*PT, LEFT),
                     TabStop(100*PT, CENTER),
                     TabStop(190*PT, RIGHT)]
        line = Line(tab_stops, width=200*PT, indent=0)
        self.assertEqual(line._cursor, 0)
        line.append(StyledTextStub(20*PT))
        self.assertFalse(line._has_tab)
        self.assertEqual(line._cursor, 20*PT)

        # jump to the first (LEFT) tab stop
        first_tab = Tab()
        line.append(first_tab)
        self.assertTrue(line._has_tab)
        self.assertEqual(line._cursor, 30*PT)
        line.append(StyledTextStub(20*PT))
        self.assertEqual(line._cursor, 50*PT)
        line.append(StyledTextStub(10*PT))
        self.assertEqual(line._cursor, 60*PT)

        # jump to the second (CENTER) tab stop
        second_tab = Tab()
        line.append(second_tab)
        self.assertEqual(line._cursor, 100*PT)
        self.assertEqual(second_tab.tab_width, 40*PT)
        line.append(StyledTextStub(20*PT))
        self.assertEqual(second_tab.tab_width, 30*PT)
        self.assertEqual(line._cursor, 110*PT)
        line.append(StyledTextStub(40*PT))
        self.assertEqual(second_tab.tab_width, 10*PT)
        self.assertEqual(line._cursor, 130*PT)
        # exceed the available space
        line.append(StyledTextStub(60*PT))
        self.assertEqual(second_tab.tab_width, 0)
        self.assertEqual(line._cursor, 180*PT)

        # jump to the third (RIGHT) tab stop
        line.append(Tab())
        self.assertEqual(line._cursor, 190*PT)
        spillover = line.append(StyledTextStub(30*PT))
        self.assertTrue(spillover)
