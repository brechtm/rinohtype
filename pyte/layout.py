
#from pslib import PS_get_value, PS_set_value, PS_rect, PS_fill_stroke, PS_stroke, PS_setcolor

import psg.drawing.box
from psg.exceptions import EndOfBox

from pyte.dimension import Dimension
from pyte.unit import pt
from pyte.paragraph import Paragraph


class EndOfPage(Exception):
    def __init__(self):
        pass


class TextTarget(object):
    def __init__(self):
        self.__paragraphs = []

    def addParagraph(self, paragraph):
        assert isinstance(paragraph, Paragraph)
        self.__paragraphs.append(paragraph)

    def paragraphs(self):
        return self.__paragraphs

    def typeset(self):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


class Container(TextTarget):
    def __init__(self, parent, left=0*pt, top=0*pt,
                 width=None, height=Dimension(0), right=None, bottom=None,
                 chain=None):
        # height = None  AND  bottom = None   ->    height depends on contents
        # width  = None  AND  right  = None   ->    use all available space
        # TODO: assert ....
        TextTarget.__init__(self)
        assert parent != self
        if parent:
            assert isinstance(parent, Container)
            parent.__children.append(self)
        self.__parent = parent
        assert isinstance(left, Dimension)
        assert isinstance(top, Dimension)
        self.__left = left
        self.__top = top
        if bottom:
            self.__height = bottom - self.top()
        else:
            self.__height = height
        if right:
            self.__width = right - self.left()
        elif width:
            self.__width = width
        else:
            self.__width = self.__parent.width() - self.left()
        self.__children = []
        self.__paragraphs = []
        if chain:
            assert isinstance(chain, Chain)
            self.chain = chain
            chain.addContainer(self)
        else:
            self.chain = None

    # TODO: remove getter functions, make variables public
    def top(self):
        return self.__top

    def absTop(self):
        if self.__parent:
            return self.__parent.absTop() + self.top()
        else:
            return self.top()

    def bottom(self):
        return self.top() + self.height()

    def absBottom(self):
        return self.absTop() + self.height()

    def left(self):
        return self.__left

    def absLeft(self):
        if self.__parent:
            return self.__parent.absLeft() + self.left()
        else:
            return self.left()

    def right(self):
        return self.left() + self.width()

    def absRight(self):
        return self.absLeft() + self.width()

    def height(self):
        return self.__height
        if self.__height:
            return self.__height
        else:
            # TODO: NotImplementedError
            return Dimension(0)

    def width(self):
        if self.__width:
            return self.__width

#    def addChild(self, child):
#        assert isinstance(child, Container)
#        self.__children.append(child)
#        child.__parent = self

    def page(self):
        if self.__parent:
            return self.__parent.page()
        else:
            return self

    def next(self):
        return self.__next

    def render(self, parentCanvas):
        left = float(self.absLeft())
        bottom = float(self.page().height() - self.absBottom())
        width = float(self.width())
        height = float(self.height())
        dynamic = False
        if height == 0:
            dynamic = True
            height = bottom
            bottom = 0

        pageCanvas = parentCanvas.page.canvas()
        thisCanvas = psg.drawing.box.canvas(pageCanvas, left, bottom, width, height)
        pageCanvas.append(thisCanvas)

        for child in self.__children:
            child.render(thisCanvas)

        totalHeight = 0

        if self.paragraphs():
            textHeight = self.typeset(thisCanvas)
            if dynamic:
                self.height().add(textHeight*pt)
        elif self.chain:
            self.chain.typeset(parentCanvas)

        self._draw_box(pageCanvas)

    def _draw_box(self, pageCanvas):
        print("gsave", file=pageCanvas)

        left = float(self.absLeft())
        bottom = float(self.page().height() - self.absBottom())
        width = float(self.width())
        height = float(self.height())
        print("newpath", file=pageCanvas)
        print("%f %f moveto" % ( left, bottom, ), file=pageCanvas)
        print("%f %f lineto" % ( left, bottom + height, ), file=pageCanvas)
        print("%f %f lineto" % ( left + width, bottom + height, ), file=pageCanvas)
        print("%f %f lineto" % ( left + width, bottom, ), file=pageCanvas)
        print("closepath", file=pageCanvas)
        print("[2 2] 0 setdash", file=pageCanvas)
        print("stroke", file=pageCanvas)
        print("grestore", file=pageCanvas)


    def typeset(self, psgCanvas):
        dynamic = False
        left   = float(self.absLeft())
        bottom = float(self.page().height() - self.absBottom())
        width  = float(self.width())
        height = float(self.height())
        dynamic = False
        if height == 0:
            dynamic = True
            height = bottom
            bottom = 0

        totalHeight = 0
        prevParHeight = 0
        for paragraph in self.paragraphs():
            # TODO: cater for multiple paragraphs
            spaceAbove = float(paragraph.style.spaceAbove)
            spaceBelow = float(paragraph.style.spaceBelow)
            boxheight = paragraph.typeset(psgCanvas, totalHeight)
            print("boxheight = {}".format(boxheight))
            prevParHeight = spaceAbove + boxheight + spaceBelow
            print("prevParHeight=", prevParHeight)
            totalHeight += prevParHeight
##            if dynamic:
##                enlarge = (spaceAbove + boxheight + spaceBelow) * pt
##                self.height().add(enlarge)
##                #print "bh", boxheight, self.height(), self.height()._Dimension__factor

        return totalHeight


class Chain(TextTarget):
    def __init__(self):
        TextTarget.__init__(self)
        self.__containers = []
        self.__typeset = False

    def typeset(self, parentCanvas):
        if self.__typeset:
            return
        self.__typeset = True
        contIter = iter(self.__containers)
        container = next(contIter)
        totalHeight = 0
        prevParHeight = 0
        for paragraph in self.paragraphs():
            parentCanvas = container.page().canvas
            # TODO: use (EndOfBox) exception to skip to next container
            # also use exception for signaling a full page
            try:
                spaceAbove = float(paragraph.style.spaceAbove)
                spaceBelow = float(paragraph.style.spaceBelow)
                # TODO: probably bad behaviour with spaceAbove/Below
                #       when skipping to next container
                left   = float(container.absLeft())
                bottom = float(container.page().height() - container.absBottom())
                width  = float(container.width())
                height = float(container.height())
                height = height - spaceAbove

                pageCanvas = parentCanvas.page.canvas()
                thisCanvas = psg.drawing.box.canvas(pageCanvas, left, bottom, width, height)
                pageCanvas.append(thisCanvas)

                boxheight = paragraph.typeset(thisCanvas, totalHeight)
                prevParHeight = spaceAbove + boxheight + spaceBelow
                totalHeight += prevParHeight
            except EndOfBox:
                print("NEXT container")
                try:
                    container = next(contIter)
                except StopIteration:
                    print("StopIteration - End of page")
                    raise EndOfPage
                totalHeight = 0
                prevParHeight = 0
                totalHeight = 0

                spaceAbove = 0
                parentCanvas = container.page().canvas
                left   = float(container.absLeft())
                bottom = float(container.page().height() - container.absBottom())
                width  = float(container.width())
                height = float(container.height())
                height = height - spaceAbove

                pageCanvas = parentCanvas.page.canvas()
                thisCanvas = psg.drawing.box.canvas(pageCanvas, left, bottom, width, height)
                pageCanvas.append(thisCanvas)

                boxheight = paragraph.typeset(thisCanvas, totalHeight)
                prevParHeight = spaceAbove + boxheight + spaceBelow
                totalHeight += prevParHeight

        return totalHeight

    def addContainer(self, container):
        assert isinstance(container, Container)
        self.__containers.append(container)

