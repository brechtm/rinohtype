
from .dimension import Dimension
from .flowable import Flowable
from .unit import pt


class EndOfContainer(Exception):
    pass


class EndOfPage(Exception):
    pass


class RenderTarget(object):
    def __init__(self):
        self.flowables = []

    @property
    def document(self):
        raise NotImplementedError

    def add_flowable(self, flowable):
        assert isinstance(flowable, Flowable)
        self.flowables.append(flowable)

    def render(self):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


class Container(RenderTarget):
    def __init__(self, parent, left=0*pt, top=0*pt,
                 width=None, height=Dimension(0), right=None, bottom=None,
                 chain=None):
        # height = None  AND  bottom = None   ->    height depends on contents
        # width  = None  AND  right  = None   ->    use all available space
        # TODO: assert ....
        super().__init__()
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
        self.__flowables = []
        if chain:
            assert isinstance(chain, Chain)
            self.chain = chain
            chain.add_container(self)
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

    @property
    def page(self):
        if self.__parent:
            return self.__parent.page
        else:
            return self

    @property
    def document(self):
        return self.page._document

    def _draw_box(self, pageCanvas):
        print("gsave", file=pageCanvas)

        left = float(self.absLeft())
        bottom = float(self.page.height() - self.absBottom())
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

    def render(self, canvas):
        left = float(self.absLeft())
        bottom = float(self.page.height() - self.absBottom())
        width = float(self.width())
        height = float(self.height())
        dynamic = False
        if height == 0:
            dynamic = True
            height = bottom
            bottom = 0

        this_canvas = self.page.canvas.append_new(left, bottom, width, height)

        for child in self.__children:
            child.render(this_canvas)

        if self.flowables:
            total_height = 0
            previous_height = 0
            for flowable in self.flowables:
                space_above = float(flowable.get_style('spaceAbove'))
                space_below = float(flowable.get_style('spaceBelow'))
                box_height = flowable.render(this_canvas, total_height)
                previous_height = space_above + box_height + space_below
                total_height += previous_height
            if dynamic:
                self.height().add(total_height * pt)
        elif self.chain:
            self.chain.render()
        #self._draw_box(page_canvas)


class Chain(RenderTarget):
    def __init__(self, document):
        super().__init__()
        self._document = document
        self._containers = []
        self._container_index = 0
        self._flowable_index = 0

    @property
    def document(self):
        return self._document

    def render(self):
        total_height = 0
        first_container_index = self._container_index
        last_container_index = len(self._containers)
        for index in range(first_container_index, last_container_index):
            container = self._containers[index]
            # TODO: bad behaviour with spaceAbove/Below
            #       when skipping to next container
            left   = float(container.absLeft())
            bottom = float(container.page.height() - container.absBottom())
            width  = float(container.width())
            height = float(container.height())

            total_height = 0
            prev_height = 0
            try:
                for flowable in self.flowables[self._flowable_index:]:
                    space_above = float(flowable.get_style('spaceAbove'))
                    space_below = float(flowable.get_style('spaceBelow'))

                    this_canvas = container.page.canvas.append_new(
                                    left, bottom, width, height - space_above)

                    box_height = flowable.render(this_canvas, total_height)
                    prev_height = space_above + box_height + space_below
                    total_height += prev_height
                    self._flowable_index += 1
            except EndOfContainer:
                self._container_index += 1
                if self._container_index > len(self._containers) - 1:
                    raise EndOfPage(self)

        return total_height

    def add_container(self, container):
        assert isinstance(container, Container)
        self._containers.append(container)
