# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.
from collections import OrderedDict

from .attribute import (Bool, Integer, Function, Attribute,
                        AttributesDictionary, RuleSet, WithAttributes)
from .dimension import DimensionBase, CM, PT
from .document import (Document, DocumentSection, DocumentPart,
                       Page, PageOrientation, PORTRAIT)
from .element import create_destination
from .float import BackgroundImage, Image
from .layout import (Container, DownExpandingContainer, UpExpandingContainer,
                     FlowablesContainer, FootnoteContainer, ChainedContainer,
                     BACKGROUND, CONTENT, HEADER_FOOTER, CHAPTER_TITLE)
from .paper import Paper, A4
from .paragraph import Paragraph
from .reference import (Variable, SECTION_NUMBER, SECTION_TITLE, PAGE_NUMBER,
                        NUMBER_OF_PAGES, Reference, NUMBER, TITLE)
from .resource import Resource
from .text import StyledText, Tab
from .strings import StringField
from .structure import Header, Footer, SectionTitles
from .style import StyleSheet
from .stylesheets import sphinx
from .util import NamedDescriptor, WithNamedDescriptors, NotImplementedAttribute


__all__ = ['SimplePage', 'TitlePage', 'PageTemplate', 'TitlePageTemplate',
           'ContentsPartTemplate', 'FixedDocumentPartTemplate',
           'DocumentTemplate', 'DocumentOptions', 'Option']


class Option(Attribute):
    """Descriptor used to describe a document option"""


class DefaultOptionException(Exception):
    pass


class Templated(object):
    def get_option(self, option, document):
        configuration = document.configuration
        return configuration.get_template_option(self.template_name, option)


class Template(AttributesDictionary, NamedDescriptor):
    def get_value(self, attribute, template_configuration):
        try:
            return super().get_value(attribute, template_configuration)
        except KeyError:
            bases = []
            if isinstance(self.base, str):
                iter = template_configuration._find_templates(self.base)
                bases.extend(iter)
            elif self.base is not None:
                bases.append(self.base)
            for base_template in bases:
                return base_template.get_value(attribute, template_configuration)
            else:
                raise KeyError


class TemplateConfigurationMeta(WithAttributes):
    def __new__(mcls, classname, bases, cls_dict):
        cls = super().__new__(mcls, classname, bases, cls_dict)
        page_templates = []
        for name, attr in cls_dict.items():
            if isinstance(attr, Template):
                attr_type = type(attr)
                template_doc = ('  {}: Defaults for :class:`{}.{}`:\n\n'
                                .format(name, attr_type.__module__,
                                        attr_type.__name__))
                for name, value in attr.items():
                    if isinstance(value, StyledText):
                        value = "'" + (str(value).replace('\n', '\\n')
                                                 .replace('\t', '\\t')) + "'"
                    template_doc += ('    - **{}** = ``{}``\n'.format(name,
                                                                      value))
                page_templates.append(template_doc)
                attr.template_configuration = cls
        if page_templates:
            cls.__doc__ += '\n\nAttributes:\n\n'
            cls.__doc__ += '\n'.join(page_templates)
        return cls


class TemplateConfiguration(RuleSet, AttributesDictionary,
                            metaclass=TemplateConfigurationMeta):
    stylesheet = Attribute(StyleSheet, sphinx, 'The stylesheet to use for '
                                               'styling document elements')
    paper_size = Attribute(Paper, A4, 'The default paper size')

    def _find_templates(self, name):
        """Yields all :class:`Template`\ s in the template hierarchy:

        - template matching `name` in this TemplateConfiguration
        - templates in base TemplateConfigurations (recursively)
        - the default template"""
        for template in self._find_templates_recursive(name):
            yield template
        yield getattr(self, name)   # the default template

    def _find_templates_recursive(self, name):
        if name in self:
            yield self[name]
        if self.base:
            for template in self.base._find_templates_recursive(name):
                yield template

    def get_option(self, option_name):
        try:
            return self[option_name]
        except KeyError:
            return getattr(type(self), option_name).default_value

    def get_template_option(self, template_name, option_name):
        for template in self._find_templates(template_name):
            try:
                return template.get_value(option_name, self)
            except KeyError:
                continue
        return template._get_default(option_name)  # FIXME: possibly never reached

    @classmethod
    def get_entry_class(cls, name):
        return type(getattr(cls, name))

    def _get_variable(self, name, accepted_type):
        return self.get_option(name)


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
            self.chapter_title = FlowablesContainer('chapter title',
                                                    CHAPTER_TITLE, self.body,
                                                    0, 0, height=height)
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
        document = self.document
        metadata = document.metadata
        self.title = DownExpandingContainer('title', CONTENT, self,
                                            self.left_margin, self.top_margin,
                                            self.body_width)
        if 'logo' in metadata:
            self.title << Image(metadata['logo'],
                                style='title page logo')
        self.title << Paragraph(metadata['title'],
                                style='title page title')
        if 'subtitle' in metadata:
            self.title << Paragraph(metadata['subtitle'],
                                    style='title page subtitle')
        if 'author' in metadata and self.get_option('show_author', document):
            self.title << Paragraph(metadata['author'],
                                    style='title page author')
        config = self.document.configuration
        try:
            abstract_location = config.get_option('abstract_location')
            if 'abstract' in metadata and abstract_location == TITLE:
                self.title << metadata['abstract']
        except AttributeError:
            pass
        if self.get_option('show_date', document):
            date = metadata['date']
            try:
                self.title << Paragraph(date.strftime('%B %d, %Y'),
                                        style='title page date')
            except AttributeError:
                self.title << Paragraph(date, style='title page date')
        extra = self.get_option('extra', document)
        if extra:
            self.title << Paragraph(extra, style='title page extra')


class DocumentPartTemplate(object):
    """A template that produces a doument part, given a set of flowables,
    page templates and a page number format.

    Args:
        name (:class:`str`): a descriptive name for this document part template
        right_page_template (:class:`PageTemplateBase`): the page template
            for right pages
        left_page_template (:class:`PageTemplateBase`): the page template
            for left pages. If not given, `right_page_template` is used.
        page_number_format (:class:`rinoh.number.NumberFormat`): the number
             format used to style the page numbers in this document part. If it
             is different from the preceding part's number format, page
             numbering restarts at 1.
    """

    skip_if_no_flowables = True

    def __init__(self, name, right_page_template, left_page_template=None,
                 page_number_format=NUMBER):
        self.name = name
        self.page_template = right_page_template
        self.left_page_template = left_page_template
        self.page_number_format = page_number_format

    @property
    def doc_kwargs(self):
        def link(page_template):
            conf = page_template.template_configuration
            return ':attr:`{}.{}`'.format(conf.__name__, page_template.name)

        kwargs = OrderedDict()
        if self.left_page_template:
            kwargs['right_page_template'] = link(self.page_template)
            kwargs['left_page_template'] = link(self.left_page_template)
        else:
            kwargs['page_template'] = link(self.page_template)
        kwargs['page_number_format'] = '``{}``'.format(self.page_number_format
                                                       .upper())
        return kwargs

    @property
    def doc_repr(self):
        doc = ('**{}** (:class:`{}.{}`)\n\n'\
               .format(self.name, type(self).__module__, type(self).__name__))
        for key, value in self.doc_kwargs.items():
            doc += '  - *{}*: {}\n'.format(key, value)
        return doc

    def flowables(self, document):
        """Return a list of :class:`rinoh.flowable.Flowable`\ s that make up
        the document part"""
        raise NotImplementedError

    def document_part(self, document_section, extra_flowables=None):
        flowables = [flowable
                     for flowable in self.flowables(document_section.document)]
        for flowable, position in (extra_flowables or []):
            flowables.insert(position, flowable)
        if flowables or not self.skip_if_no_flowables:
            return DocumentPart(document_section,
                                self.page_template, self.left_page_template,
                                flowables)


class TitlePartTemplate(DocumentPartTemplate):
    """The title page of a document."""

    skip_if_no_flowables = False

    def flowables(self, document):
        return iter([])


class ContentsPartTemplate(DocumentPartTemplate):
    """The body of a document.

    Renders all of the content present in the
    :class:`rinoh.document.DocumentTree` passed to a :class:`DocumentTemplate`.
    """

    def flowables(self, document):
        yield document.document_tree


class FixedDocumentPartTemplate(DocumentPartTemplate):
    """A document part template that renders a fixed list of flowables.

    Args:
        flowables (:class:`list`): a list of flowables to include in the
            document part
    """

    def __init__(self, name, flowables, right_page_template,
                 left_page_template=None, page_number_format=NUMBER):
        super().__init__(name, right_page_template, left_page_template,
                         page_number_format=page_number_format)
        self._flowables = flowables

    @property
    def doc_kwargs(self):
        kwargs = OrderedDict()
        kwargs['flowables'] = '``{}``'.format(self._flowables)
        kwargs.update(super().doc_kwargs)
        return kwargs

    def flowables(self, document):
        return self._flowables


class DocumentOptions(dict, metaclass=WithNamedDescriptors):
    """Collects options to customize a :class:`DocumentTemplate`. Options are
    specified as keyword arguments (`options`) matching the class's
    attributes."""

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


class DocumentTemplateMeta(type):
    def __new__(cls, classname, bases, cls_dict):
        if 'parts' in cls_dict and not isinstance(cls_dict['parts'],
                                                  NotImplementedAttribute):
            doc = (cls_dict['__doc__'] + '\n\n'
                   if '__doc__' in cls_dict else '')
            doc += ('This template builds a document consisting of the '
                    'following parts:\n\n')
            for part in cls_dict['parts']:
                doc += '- {}\n'.format(part.doc_repr)
            cls_dict['__doc__'] = doc
        return super().__new__(cls, classname, bases, cls_dict)


class DocumentTemplate(Document, Resource, metaclass=DocumentTemplateMeta):
    resource_type = 'template'

    Configuration = NotImplementedAttribute()

    parts = NotImplementedAttribute()
    """List of :class:`DocumentPartTemplate`\ s that make up the document."""

    options_class = DocumentOptions

    def __init__(self, document_tree, strings=None, configuration=None,
                 options=None, backend=None):
        self.configuration = configuration or self.Configuration()
        self.options = options or self.options_class()
        stylesheet = self.configuration.get_option('stylesheet')
        super().__init__(document_tree, stylesheet, strings=strings, backend=backend)
        self._to_insert = {}

    def insert(self, document_part_name, flowable, position):
        docpart_flowables = self._to_insert.setdefault(document_part_name, [])
        docpart_flowables.append((flowable, position))

    @property
    def sections(self):
        last_section_number_format = None
        for i, document_part_tmpl in enumerate(self.parts):
            number_format = document_part_tmpl.page_number_format
            if i == 0 or number_format != last_section_number_format:
                if i > 0:
                    yield current_section
                current_section = DocumentTemplateSection(self, number_format)
            extra_flowables = self._to_insert.get(document_part_tmpl.name)
            part = document_part_tmpl.document_part(current_section,
                                                    extra_flowables)
            if part:
                current_section._parts.append(part)
                last_section_number_format = document_part_tmpl.page_number_format
        if current_section._parts:
            yield current_section
