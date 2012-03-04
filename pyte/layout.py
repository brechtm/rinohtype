
from .dimension import Dimension
from .flowable import Flowable
from .unit import pt
from .util import cached_property


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
        #assert isinstance(flowable, Flowable)
        flowable.document = self.document
        self.flowables.append(flowable)

    def render(self):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


class Container(RenderTarget):
    def __init__(self, parent, left=0*pt, top=0*pt,
                 width=None, height=None, right=None, bottom=None,
                 chain=None):
        super().__init__()
        if parent:
            parent.children.append(self)
        self.parent = parent
        self.left = left
        if top:
            self.top = top
        self.height = height if height else bottom - self.top
        self.dynamic = self.height == 0
        if width:
            self.width = width
        elif right:
            self.width = right - self.left
        else:
            self.width = self.parent.width - self.left
        self.children = []
        self.flowables = []
        self.chain = chain
        if self.chain:
            chain.add_container(self)
        self._flowable_offset = 0

    def advance(self, height):
        self._flowable_offset += height
        if self._flowable_offset > self.height:
            raise EndOfContainer

    @property
    def cursor(self):
        return float(self.canvas.height) - self._flowable_offset

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def abs_left(self):
        try:
            return self.parent.abs_left + self.left
        except AttributeError:
            return self.left

    @property
    def abs_top(self):
        try:
            return self.parent.abs_top + self.top
        except AttributeError:
            return self.top

    @property
    def abs_right(self):
        return self.abs_left + self.width

    @property
    def abs_bottom(self):
        return self.abs_top + self.height

    @property
    def page(self):
        return self.parent.page

    @property
    def document(self):
        return self.page._document

    @cached_property
    def canvas(self):
        left = float(self.abs_left)
        width = float(self.width)
        return self.page.canvas.new(left, 0, width, 0)

    def flow(self, flowable, continued=False):
        from .float import Float
        if isinstance(flowable, Float):
            self._float_space.flow(flowable.flowable)
            return 0
        else:
            start_offset = self._flowable_offset
            flowable.container = self
            if not continued:
                self.advance(float(flowable.get_style('spaceAbove')))
            flowable.render(self.canvas)
            self.advance(float(flowable.get_style('spaceBelow')))
            return self._flowable_offset - start_offset

    def render(self, canvas):
        end_of_page = None
        for child in self.children:
            try:
                child.render(self.canvas)
            except EndOfPage as e:
                end_of_page = e

        if self.flowables:
            for flowable in self.flowables:
                self.flow(flowable)
        elif self.chain:
            try:
                self.chain.render()
            except EndOfPage as e:
                end_of_page = e

        if end_of_page is not None:
            raise end_of_page

    def place(self):
        for child in self.children:
            child.place()

        y_offset = float(self.page.height) - float(self.abs_top)
        self.page.canvas.save_state()
        self.page.canvas.translate(0, y_offset)
        self.page.canvas.append(self.canvas)
        self.page.canvas.restore_state()


class ExpandingContainer(Container):
    def __init__(self, parent, left=0*pt, top=0*pt, width=None, right=None,
                 max_height=None):
        super().__init__(parent, left, top, width=width, right=right,
                         height=0*pt)
        self.max_height = max_height

    def advance(self, height):
        self._flowable_offset += height
        if self.max_height and self._flowable_offset > self.max_height:
            raise EndOfContainer
        self.expand(height)

    def expand(self, height):
        self.height.add(height * pt)


class DownExpandingContainer(ExpandingContainer):
    def __init__(self, parent, left=0*pt, top=0*pt, width=None, right=None):
        super().__init__(parent, left, top, width=width, right=right)
##
##    def place(self):
##        from .draw import Rectangle
##        box = Rectangle((0, 0), float(self.width), - float(self.height))
##        box.render(self.canvas)
##        super().place()


class UpExpandingContainer(ExpandingContainer):
    def __init__(self, parent, left=0*pt, bottom=0*pt, width=None, right=None):
        self._bottom = bottom
        super().__init__(parent, left, top=None, width=width, right=right)

    @property
    def top(self):
        return self._bottom - self.height

    @property
    def bottom(self):
        return self._bottom

    def expand(self, height):
        super().expand(height)
        self.top.add(- height * pt)


class VirtualContainer(DownExpandingContainer):
    def __init__(self, parent, width):
        super().__init__(parent.page, 0*pt, 0*pt, width=width)

    def place(self):
        pass


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
        continued = False
        while self._container_index < len(self._containers):
            container = self._containers[self._container_index]
            self._container_index += 1
            try:
                while self._flowable_index < len(self.flowables):
                    flowable = self.flowables[self._flowable_index]
                    container.flow(flowable, continued)
                    self._flowable_index += 1
                    continued = False
            except EndOfContainer:
                continued = True
                if self._container_index > len(self._containers) - 1:
                    raise EndOfPage(self)

    def add_container(self, container):
        assert isinstance(container, Container)
        self._containers.append(container)
