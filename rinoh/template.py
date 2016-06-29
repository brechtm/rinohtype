# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import OrderedDict
from types import FunctionType

from .dimension import DimensionBase, CM, PT
from .document import (Document, DocumentSection, DocumentPart,
                       Page, PageOrientation, PORTRAIT)
from .element import create_destination
from .float import BackgroundImage, Image
from .layout import (FootnoteContainer, DownExpandingContainer,
                     ChainedContainer, UpExpandingContainer, Container,
                     FlowablesContainer, BACKGROUND, CONTENT, HEADER_FOOTER)
from .paper import Paper, A4
from .paragraph import Paragraph
from .reference import (Variable, SECTION_NUMBER, SECTION_TITLE, PAGE_NUMBER,
                        NUMBER_OF_PAGES, Reference, NUMBER, TITLE)
from .text import StyledText, Tab
from .strings import StringField
from .structure import Header, Footer, SectionTitles
from .style import StyleSheet, Bool, Integer, AttributeType
from .stylesheets import sphinx
from .util import NamedDescriptor, WithNamedDescriptors, NotImplementedAttribute


__all__ = ['SimplePage', 'TitlePage', 'PageTemplate', 'TitlePageTemplate',
           'ContentsPartTemplate', 'FixedDocumentPartTemplate',
           'DocumentTemplate', 'DocumentOptions', 'Option']


class Option(NamedDescriptor):
    """Descriptor used to describe a document option"""
    def __init__(self, accepted_type, default_value, description):
        self.accepted_type = accepted_type
        self.default_value = default_value
        self.description = description

    def __get__(self, document_options, type=None):
        try:
            return document_options.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, options, value):
        if not self.accepted_type.check_type(value):
            raise TypeError('{} option has wrong type: {}'
                            .format(type(options).__name__, self.name))
        options[self.name] = value

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)\n'
                ':default: {}'
                .format(self.description, self.accepted_type.__name__,
                        self.default_value))


class Templated(object):
    def get_option(self, option, document):
        name = self.template_name
        return document.template_configuration.get_option(name, option)


# TODO: consolidate Style/Template(Meta) classes
class TemplateMeta(WithNamedDescriptors):
    def __new__(cls, classname, bases, cls_dict):
        options = cls_dict['_options'] = {}
        for name, attr in cls_dict.items():
            if isinstance(attr, Option):
                options[name] = attr
        supported_options = set(name for name in options)
        for base_class in bases:
            try:
                supported_options.update(base_class._supported_attributes)
            except AttributeError:
                pass
        cls_dict['_supported_options'] = supported_options
        return super().__new__(cls, classname, bases, cls_dict)


class Template(dict, metaclass=TemplateMeta):
    def __init__(self, base=None, **options):
        self.base = base
        for name, value in options.items():
            option_descriptor = getattr(type(self), name, None)
            if not isinstance(option_descriptor, Option):
                raise AttributeError('Unsupported page template option: {}'
                                     .format(name))
            if not option_descriptor.accepted_type.check_type(value):
                raise TypeError('Page template option has wrong type: {}'
                                .format(name))
            self[name] = value

    @classmethod
    def _get_default(cls, option):
        """Return the default value for `option`.

        If no default is specified in this style, get the default from the
        nearest superclass.
        If `option` is not supported, raise a :class:`KeyError`."""
        try:
            for klass in cls.__mro__:
                if option in klass._options:
                    return klass._options[option].default_value
        except AttributeError:
            raise KeyError("No option '{}' in {}".format(option, cls))


class TemplateConfiguration(OrderedDict):
    def __init__(self, base=None):
        self.base = base

    def __call__(self, template_name, **kwargs):
        template_class = self._get_template_class(template_name)
        self[template_name] = template_class(**kwargs)

    def _get_template_class(self, template_name):
        try:
            return type(self[template_name])
        except KeyError:
            if not self.base:
                raise
            return self.base._get_template_class(template_name)

    def find_template(self, name):
        try:
            return self[name]
        except KeyError:
            return self.base[name]

    def get_option(self, template_name, option_name):
        template = self.find_template(template_name)
        try:
            return template[option_name]
        except KeyError:
            if not self.base:
                return template._get_default(option_name)
            return self.base.get_option(template_name, option_name)


class PageTemplateBase(Template):
    page_size = Option(Paper, A4, 'The format of the pages in the document')
    page_orientation = Option(PageOrientation, PORTRAIT,
                              'The orientation of pages in the document')
    left_margin = Option(DimensionBase, 3*CM, 'The margin size on the left of '
                                              'the page')
    right_margin = Option(DimensionBase, 3*CM, 'The margin size on the right '
                                               'of the page')
    top_margin = Option(DimensionBase, 3*CM, 'The margin size at the top of '
                                              'the page')
    bottom_margin = Option(DimensionBase, 3*CM, 'The margin size at the bottom '
                                                'of the page')
    background = Option(BackgroundImage, None, 'An image to place in the '
                                             'background of the page')
    after_break_background = Option(BackgroundImage, None, 'An image to place '
                                    'in the background after a page break')

    def page(self, template_name, document_part, chain, after_break, **kwargs):
        raise NotImplementedError


def chapter_title_flowables(section_id):
    yield Paragraph(StringField(SectionTitles, 'chapter'))
    yield Paragraph(Reference(section_id, NUMBER))
    yield Paragraph(Reference(section_id, TITLE))



class Function(AttributeType):
    @classmethod
    def check_type(cls, value):
        return isinstance(value, (FunctionType, type(None)))



class PageTemplate(PageTemplateBase):
    header_footer_distance = Option(DimensionBase, 14*PT, 'Distance of the '
                                    'header and footer to the content area')
    columns = Option(Integer, 1, 'The number of columns for the body text')
    column_spacing = Option(DimensionBase, 1*CM, 'The spacing between columns')
    header_text = Option(StyledText, Variable(SECTION_NUMBER(1))
                                     + ' ' + Variable(SECTION_TITLE(1)),
                         'The text to place in the page header')
    footer_text = Option(StyledText, Tab() + Variable(PAGE_NUMBER)
                                     + '/' + Variable(NUMBER_OF_PAGES),
                         'The text to place in the page footer')
    chapter_header_text = Option(StyledText, None, 'The text to place in the '
                                 'header on a page that starts a new chapter')
    chapter_footer_text = Option(StyledText, None, 'The text to place in the '
                                 'footer on a page that starts a new chapter')
    chapter_title_flowables = Option(Function, chapter_title_flowables,
                                     'Generator that yields the flowables to '
                                     'represent the chapter title')
    chapter_title_height = Option(DimensionBase, 150*PT, 'The height of the '
                                  'container holding the chapter title')

    def page(self, document_part, template_name, chain, after_break, **kwargs):
        return SimplePage(document_part, template_name, chain, self,
                          after_break, **kwargs)


class PageBase(Page, Templated):
    def __init__(self, document_part, template_name, options, after_break):
        self.template_name = template_name
        document = document_part.document
        paper = self.get_option('page_size', document)
        orientation = self.get_option('page_orientation', document)
        super().__init__(document_part, paper, orientation)
        self.template = options
        self.left_margin = self.get_option('left_margin', document)
        self.right_margin = self.get_option('right_margin', document)
        self.top_margin = self.get_option('top_margin', document)
        self.bottom_margin = self.get_option('bottom_margin', document)
        self.body_width = self.width - (self.left_margin + self.right_margin)
        self.body_height = self.height - (self.top_margin + self.bottom_margin)
        background = self.get_option('background', document)
        after_break_background = self.get_option('after_break_background', document)
        bg = after_break_background or background
        if after_break and bg:
            self.background = FlowablesContainer('background', BACKGROUND, self)
            self.background << bg
        elif background:
            self.background = FlowablesContainer('background', BACKGROUND, self)
            self.background << background


class SimplePage(PageBase):
    def __init__(self, document_part, template_name, chain, options, new_chapter):
        super().__init__(document_part, template_name, options, new_chapter)
        document = document_part.document
        num_cols = self.get_option('columns', document)
        header_footer_distance = self.get_option('header_footer_distance', document)
        column_spacing = self.get_option('column_spacing', document)
        total_column_spacing = column_spacing * (num_cols - 1)
        column_width = (self.body_width - total_column_spacing) / num_cols
        self.body = Container('body', self, self.left_margin, self.top_margin,
                              self.body_width, self.body_height)
        footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                           self.body.height)
        float_space = DownExpandingContainer('floats', CONTENT, self.body, 0, 0,
                                             max_height=self.body_height / 2)
        self.body.float_space = float_space
        if self.get_option('chapter_title_flowables', document) and new_chapter:
            height = self.get_option('chapter_title_height', document)
            self.chapter_title = FlowablesContainer('chapter title', CONTENT,
                                                    self.body, 0, 0,
                                                    height=height)
            column_top = self.chapter_title.bottom
            header = self.get_option('chapter_header_text', document)
            footer = self.get_option('chapter_footer_text', document)
        else:
            self.chapter_title = None
            column_top = float_space.bottom
            header = self.get_option('header_text', document)
            footer = self.get_option('footer_text', document)
        self.columns = [ChainedContainer('column{}'.format(i + 1), CONTENT,
                                         self.body, chain,
                                         left=i * (column_width
                                                   + column_spacing),
                                         top=column_top, width=column_width,
                                         bottom=footnote_space.top)
                        for i in range(num_cols)]
        for column in self.columns:
            column._footnote_space = footnote_space

        if header:
            header_bottom = self.body.top - header_footer_distance
            self.header = UpExpandingContainer('header', HEADER_FOOTER, self,
                                               left=self.left_margin,
                                               bottom=header_bottom,
                                               width=self.body_width)
            self.header.append_flowable(Header(header))
        if footer:
            footer_vpos = self.body.bottom + header_footer_distance
            self.footer = DownExpandingContainer('footer', HEADER_FOOTER, self,
                                                 left=self.left_margin,
                                                 top=footer_vpos,
                                                 width=self.body_width)
            self.footer.append_flowable(Footer(footer))

    def create_chapter_title(self, heading):
        descender = None
        section_id = heading.section.get_id(self.document)
        create_destination(heading.section, self.chapter_title, False)
        create_destination(heading, self.chapter_title, False)
        chapter_title_flowables = self.get_option('chapter_title_flowables',
                                                  self.document)
        for flowable in chapter_title_flowables(section_id):
            _, _, descender = flowable.flow(self.chapter_title, descender)


class TitlePageTemplate(PageTemplateBase):
    show_date = Option(Bool, True, "Show or hide the document's date")
    show_author = Option(Bool, True, "Show or hide the document's author")
    extra = Option(StyledText, None, 'Extra text to include on the title '
                                     'page below the title')

    def page(self, document_part, template_name, chain, after_break, **kwargs):
        return TitlePage(document_part, template_name, self, after_break)


class TitlePage(PageBase):
    def __init__(self, document_part, template_name, options, after_break):
        super().__init__(document_part, template_name, options, after_break)
        document = document_part.document
        self.title = DownExpandingContainer('title', CONTENT, self,
                                            self.left_margin, self.top_margin,
                                            self.body_width)
        if 'logo' in self.document.metadata:
            self.title << Image(self.document.metadata['logo'],
                                style='title page logo')
        self.title << Paragraph(self.document.metadata['title'],
                                style='title page title')
        if 'subtitle' in self.document.metadata:
            self.title << Paragraph(self.document.metadata['subtitle'],
                                    style='title page subtitle')
        if 'author' in self.document.metadata and self.get_option('show_author', document):
            self.title << Paragraph(self.document.metadata['author'],
                                    style='title page author')
        if self.get_option('show_date', document):
            date = self.document.metadata['date']
            try:
                self.title << Paragraph(date.strftime('%B %d, %Y'),
                                        style='title page date')
            except AttributeError:
                self.title << Paragraph(date, style='title page date')
        extra = self.get_option('extra', document)
        if extra:
            self.title << Paragraph(extra, style='title page extra')


class DocumentPartTemplate(object):
    def __init__(self, right_page_template, left_page_template=None,
                 page_number_format=NUMBER):
        self.page_template = right_page_template
        self.left_page_template = left_page_template
        self.page_number_format = page_number_format

    def document_part(self, document_section):
        raise NotImplementedError


class ContentsPartTemplate(DocumentPartTemplate):
    def document_part(self, document_section):
        return DocumentPart(document_section,
                            self.page_template, self.left_page_template,
                            document_section.document.content_flowables)


class FixedDocumentPartTemplate(DocumentPartTemplate):
    def __init__(self, flowables, right_page_template, left_page_template=None,
                 page_number_format=NUMBER):
        super().__init__(right_page_template, left_page_template,
                         page_number_format=page_number_format)
        self.flowables = flowables

    def document_part(self, document_section):
        return DocumentPart(document_section,
                            self.page_template, self.left_page_template,
                            self.flowables)


class DocumentOptions(dict, metaclass=WithNamedDescriptors):
    """Collects options to customize a :class:`DocumentTemplate`. Options are
    specified as keyword arguments (`options`) matching the class's
    attributes."""

    stylesheet = Option(StyleSheet, sphinx, 'The stylesheet to use for '
                                            'styling document elements')

    def __init__(self, **options):
        for name, value in options.items():
            option_descriptor = getattr(type(self), name, None)
            if not isinstance(option_descriptor, Option):
                raise AttributeError('No such document option: {}'.format(name))
            setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)


class DocumentTemplateSection(DocumentSection):
    parts = []


class DocumentTemplate(Document):
    template_configuration = NotImplementedAttribute()
    parts = NotImplementedAttribute()
    options_class = DocumentOptions

    def __init__(self, flowables, strings=None, template_configuration=None,
                 options=None, backend=None):
        if template_configuration:
            self.template_configuration = template_configuration
        self.options = options or self.options_class()
        super().__init__(flowables, self.options['stylesheet'], strings=strings,
                         backend=backend)

    @property
    def sections(self):
        last_section_number_format = None
        for i, document_part_tmpl in enumerate(self.parts):
            number_format = document_part_tmpl.page_number_format
            if i == 0 or number_format != last_section_number_format:
                if i > 0:
                    yield current_section
                current_section = DocumentTemplateSection(self, number_format)
            part = document_part_tmpl.document_part(current_section)
            current_section._parts.append(part)
            last_section_number_format = document_part_tmpl.page_number_format
        yield current_section
