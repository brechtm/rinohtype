
from .dimension import Dimension, NIL
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
        assert isinstance(flowable, Flowable)
        flowable.document = self.document
        self.flowables.append(flowable)

    def render(self):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


# TODO: DownwardExpandingContainer & UpwardExpandingContainer?
class Container(RenderTarget):
    def __init__(self, parent, left=NIL, top=NIL,
                 width=None, height=NIL, right=None, bottom=None,
                 chain=None, upward=False):
        # height = NIL   AND  bottom = None   ->    height depends on contents
        # width  = None  AND  right  = None   ->    use all available space
        super().__init__()
        if parent:
            parent.children.append(self)
        self.parent = parent
        self.left = left
        self.top = top
        self.height = bottom - self.top if bottom else height
        self.dynamic = self.height == 0
        self.upward = upward
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
        if self.dynamic:
            bottom = 0
            height = float(self.page.height - self.abs_bottom)
        else:
            bottom = float(self.page.height - self.abs_bottom)
            height = float(self.height)
        return self.page.canvas.new(left, bottom, width, height)

    def render(self, canvas):
        end_of_page = None
        for child in self.children:
            try:
                child.render(self.canvas)
            except EndOfPage as e:
                end_of_page = e

        if self.flowables:
            offset = 0
            for flowable in self.flowables:
                offset += flowable.flow(self, offset)
            if self.dynamic:
                self.height.add(offset * pt)
                if self.upward:
                    self.top.add(- offset * pt)
            self.place()
        elif self.chain:
            self.chain.render()

        if end_of_page is not None:
            raise end_of_page

    def place(self):
        if self.dynamic and self.upward:
            self.page.canvas.save_state()
            self.page.canvas.translate(0, float(self.height))
        self.page.canvas.append(self.canvas)
        if self.dynamic and self.upward:
            self.page.canvas.restore_state()


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
        offset = 0
        while self._container_index < len(self._containers):
            container = self._containers[self._container_index]
            self._container_index += 1
            offset = 0
            try:
                while self._flowable_index < len(self.flowables):
                    flowable = self.flowables[self._flowable_index]
                    offset += flowable.flow(container, offset, continued)
                    self._flowable_index += 1
                    continued = False
            except EndOfContainer:
                continued = True
                if self._container_index > len(self._containers) - 1:
                    raise EndOfPage(self)
            finally:
                container.place()
        return offset

    def add_container(self, container):
        assert isinstance(container, Container)
        self._containers.append(container)
