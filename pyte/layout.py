
from .dimension import Dimension, NIL
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
        flowable.document = self.document
        self.flowables.append(flowable)

    def render(self):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)


class Container(RenderTarget):
    def __init__(self, parent, left=NIL, top=NIL,
                 width=None, height=NIL, right=None, bottom=None,
                 chain=None):
        # height = None  AND  bottom = None   ->    height depends on contents
        # width  = None  AND  right  = None   ->    use all available space
        super().__init__()
        if parent:
            parent.children.append(self)
        self.parent = parent
        self.left = left
        self.top = top
        self.height = bottom - self.top if bottom else height
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

    def render(self, canvas):
        left = float(self.abs_left)
        bottom = float(self.page.height - self.abs_bottom)
        width = float(self.width)
        height = float(self.height)
        dynamic = False
        if height == 0:
            dynamic = True
            height = bottom
            bottom = 0

        this_canvas = self.page.canvas.append_new(left, bottom, width, height)

        end_of_page = None
        for child in self.children:
            try:
                child.render(this_canvas)
            except EndOfPage as e:
                end_of_page = e

        if self.flowables:
            total_height = 0
            previous_height = 0
            for flowable in self.flowables:
                flowable.parent = self
                space_above = float(flowable.get_style('spaceAbove'))
                space_below = float(flowable.get_style('spaceBelow'))
                box_height = flowable.render(this_canvas, total_height)
                previous_height = space_above + box_height + space_below
                total_height += previous_height
            if dynamic:
                self.height.add(total_height * pt)
        elif self.chain:
            self.chain.render()

        if end_of_page is not None:
            raise end_of_page


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
            left   = float(container.abs_left)
            bottom = float(container.page.height - container.abs_bottom)
            width  = float(container.width)
            height = float(container.height)

            total_height = 0
            prev_height = 0
            try:
                for flowable in self.flowables[self._flowable_index:]:
                    flowable.parent = container
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
