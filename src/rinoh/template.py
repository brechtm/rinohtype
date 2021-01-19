# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from collections import OrderedDict
from functools import partial
from itertools import chain

from . import styleds, reference
from .attribute import (Bool, Integer, Attribute, AttributesDictionary,
                        RuleSet, RuleSetFile, WithAttributes, AttributeType,
                        OptionSet, AcceptNoneAttributeType, OverrideDefault,
                        Configurable, DefaultValueException,
                        VariableNotDefined)
from .dimension import Dimension, CM, PT, PERCENT
from .document import Document, Page, PageOrientation, PageType
from .element import create_destination
from .image import BackgroundImage, Image
from .flowable import Flowable, StaticGroupedFlowables
from .language import Language, EN
from .layout import (Container, DownExpandingContainer, UpExpandingContainer,
                     FlowablesContainer, FootnoteContainer, ChainedContainer,
                     BACKGROUND, CONTENT, HEADER_FOOTER, CHAPTER_TITLE,
                     PageBreakException, Chain)
from .number import NumberFormat
from .paper import Paper, A4
from .paragraph import Paragraph
from .reference import (Field, SECTION_NUMBER, SECTION_TITLE,
                        PAGE_NUMBER, NUMBER_OF_PAGES)
from .resource import Resource
from .text import StyledText, Tab
from .strings import StringCollection, Strings
from .structure import Header, Footer, HorizontalRule, NewChapterException
from .style import StyleSheet, Specificity, DocumentLocationType
from .stylesheets import sphinx
from .util import NamedDescriptor


__all__ = ['SimplePage', 'TitlePage', 'PageTemplate', 'TitlePageTemplate',
           'ContentsPartTemplate', 'FixedDocumentPartTemplate',
           'Option', 'AbstractLocation', 'DocumentTemplate',
           'TemplateConfiguration', 'TemplateConfigurationFile']


class Option(Attribute):
    """Descriptor used to describe a document option"""


class DefaultOptionException(Exception):
    pass


class AbstractLocation(OptionSet):
    """Where to place the article's abstract"""

    values = 'title', 'front matter'


class Template(AttributesDictionary, NamedDescriptor):
    @classmethod
    def get_ruleset(self, document):
        return document.configuration


class Templated(Configurable):
    configuration_class = Template

    def configuration_name(self, document):
        return self.template_name


class PageTemplateBase(Template):
    page_size = Option(Paper, A4, 'The format of the pages in the document')
    page_orientation = Option(PageOrientation, 'portrait',
                              'The orientation of pages in the document')
    left_margin = Option(Dimension, 3*CM, 'The margin size on the left of the '
                                          'page')
    right_margin = Option(Dimension, 3*CM, 'The margin size on the right of '
                                           'the page')
    top_margin = Option(Dimension, 3*CM, 'The margin size at the top of the '
                                         'page')
    bottom_margin = Option(Dimension, 3*CM, 'The margin size at the bottom of '
                                            'the page')
    background = Option(BackgroundImage, None, 'An image to place in the '
                                               'background of the page')
    after_break_background = Option(BackgroundImage, None, 'An image to place '
                                    'in the background after a page break')

    def page(self, document_part, page_number, chain, after_break, **kwargs):
        raise NotImplementedError


class FlowablesList(AcceptNoneAttributeType):
    @classmethod
    def check_type(cls, value):
        if not (super().check_type(value) or isinstance(value, (list, tuple))):
            return False
        return value is None or all(isinstance(val, Flowable) for val in value)

    @classmethod
    def parse_string(cls, string, source):
        locals = {}
        locals.update(reference.__dict__)
        locals.update(styleds.__dict__)
        flowables = eval(string, {'__builtins__':{}}, locals)    # TODO: parse!
        return [StaticGroupedFlowables(flowables, source=source)]

    @classmethod
    def doc_format(cls):
        return ('Python source code that represents a list of '
                ':class:`.Flowable`\\ s')


class PageTemplate(PageTemplateBase):
    header_footer_distance = Option(Dimension, 14*PT, 'Distance of the '
                                    'header and footer to the content area')
    columns = Option(Integer, 1, 'The number of columns for the body text')
    column_spacing = Option(Dimension, 1*CM, 'The spacing between columns')
    header_text = Option(StyledText, Field(SECTION_NUMBER(1))
                         + ' ' + Field(SECTION_TITLE(1)),
                         'The text to place in the page header')
    footer_text = Option(StyledText, Tab() + Field(PAGE_NUMBER)
                         + '/' + Field(NUMBER_OF_PAGES),
                         'The text to place in the page footer')
    chapter_header_text = Option(StyledText, None, 'The text to place in the '
                                 'header on a page that starts a new chapter')
    chapter_footer_text = Option(StyledText, None, 'The text to place in the '
                                 'footer on a page that starts a new chapter')
    chapter_title_flowables = Option(FlowablesList, None,
                                     'Generator that yields the flowables to '
                                     'represent the chapter title')
    chapter_title_height = Option(Dimension, 150*PT, 'The height of the '
                                  'container holding the chapter title')

    def page(self, document_part, page_number, chain, after_break, **kwargs):
        return SimplePage(document_part, self.name, page_number, chain,
                          after_break, **kwargs)


class PageBase(Page, Templated):
    configuration_class = PageTemplateBase

    def __init__(self, document_part, template_name, page_number, after_break):
        get_option = partial(self.get_config_value,
                             document=document_part.document)
        self.template_name = template_name
        paper = get_option('page_size')
        orientation = get_option('page_orientation')
        super().__init__(document_part, page_number, paper, orientation)
        self.left_margin = get_option('left_margin')
        self.right_margin = get_option('right_margin')
        self.top_margin = get_option('top_margin')
        self.bottom_margin = get_option('bottom_margin')
        self.body_width = self.width - (self.left_margin + self.right_margin)
        self.body_height = self.height - (self.top_margin + self.bottom_margin)
        background = get_option('background')
        after_break_background = get_option('after_break_background')
        bg = after_break_background or background
        if after_break and bg:
            self.background = FlowablesContainer('background', BACKGROUND, self)
            self.background << bg
        elif background:
            self.background = FlowablesContainer('background', BACKGROUND, self)
            self.background << background


class SimplePage(PageBase):
    configuration_class = PageTemplate

    def __init__(self, document_part, template_name, page_number, chain,
                 new_chapter):
        super().__init__(document_part, template_name, page_number, new_chapter)
        get_option = partial(self.get_config_value, document=self.document)
        num_cols = get_option('columns')
        header_footer_distance = get_option('header_footer_distance')
        column_spacing = get_option('column_spacing')
        total_column_spacing = column_spacing * (num_cols - 1)
        column_width = (self.body_width - total_column_spacing) / num_cols
        self.body = Container('body', self, self.left_margin, self.top_margin,
                              self.body_width, self.body_height)
        footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                           self.body.height)
        float_space = DownExpandingContainer('floats', CONTENT, self.body, 0, 0,
                                             max_height=self.body_height / 2)
        self.body.float_space = float_space
        if get_option('chapter_title_flowables') and new_chapter:
            height = get_option('chapter_title_height')
            self.chapter_title = FlowablesContainer('chapter title',
                                                    CHAPTER_TITLE, self.body,
                                                    0, 0, height=height)
            column_top = self.chapter_title.bottom
            header = get_option('chapter_header_text')
            footer = get_option('chapter_footer_text')
        else:
            self.chapter_title = None
            column_top = float_space.bottom
            header = get_option('header_text')
            footer = get_option('footer_text')
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
        create_destination(heading.section, self.chapter_title, False)
        create_destination(heading, self.chapter_title, False)
        descender = None
        for flowable in self.get_config_value('chapter_title_flowables',
                                              self.document):
            _, _, descender = flowable.flow(self.chapter_title, descender)


class TitlePageTemplate(PageTemplateBase):
    show_date = Option(Bool, True, "Show or hide the document's date")
    show_author = Option(Bool, True, "Show or hide the document's author")
    extra = Option(StyledText, None, 'Extra text to include on the title '
                                     'page below the title')

    def page(self, document_part, page_number, chain, after_break, **kwargs):
        return TitlePage(document_part, self.name, page_number, after_break)


class TitlePage(PageBase):
    configuration_class = TitlePageTemplate

    def __init__(self, document_part, template_name, page_number, after_break):
        super().__init__(document_part, template_name, page_number,
                         after_break)
        get_option = partial(self.get_config_value, document=self.document)
        metadata = self.document.metadata
        get_metadata = self.document.get_metadata
        self.title = DownExpandingContainer('title', CONTENT, self,
                                            self.left_margin, self.top_margin,
                                            self.body_width)

        if 'logo' in metadata:
            self.title << HorizontalRule(style='title page rule')
            self.title << Image(get_metadata('logo'),
                                style='title page logo',
                                limit_width=100*PERCENT)
        if 'title' in metadata:
            self.title << Paragraph(get_metadata('title'),
                                    style='title page title')
        if 'subtitle' in metadata:
            self.title << Paragraph(get_metadata('subtitle'),
                                    style='title page subtitle')
        if 'author' in metadata and get_option('show_author'):
            self.title << Paragraph(get_metadata('author'),
                                    style='title page author')
        try:
            abstract_location = self.document.get_option('abstract_location')
            if ('abstract' in metadata
                    and abstract_location == AbstractLocation.TITLE):
                self.title << metadata['abstract']
        except KeyError:
            pass
        if get_option('show_date'):
            date = metadata['date']
            try:
                self.title << Paragraph(date.strftime('%B %d, %Y'),
                                        style='title page date')
            except AttributeError:
                self.title << Paragraph(date, style='title page date')
        extra = get_option('extra')
        if extra:
            self.title << Paragraph(extra, style='title page extra')


class DocumentPartTemplate(Template):
    """A template that produces a document part

    The document part is created given a set of flowables, and page templates.
    The latter are looked up in the :class:`TemplateConfiguration` where this
    part template was.

    """

    page_number_format = Option(NumberFormat, 'number', "The format for page "
                                "numbers in this document part. If it is "
                                "different from the preceding part's number "
                                "format, numbering restarts at 1")
    end_at_page = Option(PageType, 'any', 'The type of page to end this '
                                          'document part on')
    drop_if_empty = Option(Bool, True, 'Exclude this part from the document '
                                       'if it is empty (no flowables)')

    @property
    def doc_repr(self):
        doc = ('**{}** (:class:`{}.{}`)\n\n'
               .format(self.name, type(self).__module__, type(self).__name__))
        for name, default_value in self.items():
            doc += '  - *{}*: ``{}``\n'.format(name, default_value)
        return doc

    def prepare(self, fake_container):
        for flowable in self.all_flowables(fake_container.document):
            flowable.prepare(fake_container)

    def _flowables(self, document):
        """Return a list of :class:`rinoh.flowable.Flowable`\\ s that make up
        the document part"""
        raise NotImplementedError

    def all_flowables(self, document):
        extra_flowables = document._to_insert.get(self.name, ())
        flowables = [flowable for flowable in self._flowables(document)]
        for flowable, position in extra_flowables:
            flowables.insert(position, flowable)
        return flowables

    def document_part(self, document):
        flowables = self.all_flowables(document)
        if flowables or not self.drop_if_empty:
            return DocumentPart(self, document, flowables)


class DocumentPart(Templated, metaclass=DocumentLocationType):
    """Part of a document.

    Args:
        template (DocumentPartTemplate): the template that determines the
            contents and style of this document part
        document (Document): the document this part belongs to
        flowables (list[Flowable]): the flowables to render in this document
            part

    """

    configuration_class = DocumentPartTemplate

    def __init__(self, template, document, flowables):
        self.template = template
        self.template_name = template.name
        self.document = document
        self.pages = []
        self.chain = Chain(self)
        for flowable in flowables or []:
                self.chain << flowable

    @property
    def page_number_format(self):
        return self.template.page_number_format

    @property
    def number_of_pages(self):
        try:
            return self.document.part_page_counts[self.template.name].count
        except KeyError:
            return 0

    def prepare(self):
        for flowable in self._flowables(self.document):
            flowable.prepare(self)

    def render(self, first_page_number):
        self.add_page(self.first_page(first_page_number))
        for page_number, page in enumerate(self.pages, first_page_number + 1):
            try:
                page.render()
                break_type = None
            except NewChapterException as nce:
                break_type = nce.break_type
            except PageBreakException as pbe:
                break_type = None
            page.place()
            if self.chain and not self.chain.done:
                next_page_type = 'left' if page.number % 2 else 'right'
                page = self.new_page(page_number, next_page_type == break_type)
                self.add_page(page)     # this grows self.pages!
        next_page_type = 'right' if page_number % 2 else 'left'
        end_at_page = self.get_config_value('end_at_page', self.document)
        if next_page_type == end_at_page:
            self.add_page(self.first_page(page_number + 1))
        return len(self.pages)

    def add_page(self, page):
        """Append `page` (:class:`Page`) to this :class:`DocumentPart`."""
        self.pages.append(page)

    def first_page(self, page_number):
        return self.new_page(page_number, new_chapter=True)

    def new_page(self, page_number, new_chapter, **kwargs):
        """Called by :meth:`render` with the :class:`Chain`s that need more
        :class:`Container`s. This method should create a new :class:`Page` which
        contains a container associated with `chain`."""
        right_template = self.document.get_page_template(self, 'right')
        left_template = self.document.get_page_template(self, 'left')
        page_template = right_template if page_number % 2 else left_template
        return page_template.page(self, page_number, self.chain, new_chapter,
                                  **kwargs)

    @classmethod
    def match(cls, styled, container):
        if isinstance(container.document_part, cls):
            return Specificity(0, 1, 0, 0, 0)
        else:
            return None


class TitlePartTemplate(DocumentPartTemplate):
    """The title page of a document."""

    drop_if_empty = OverrideDefault(False)

    def _flowables(self, document):
        return iter([])


class ContentsPartTemplate(DocumentPartTemplate):
    """The body of a document.

    Renders all of the content present in the
    :class:`~.DocumentTree` passed to the :class:`DocumentTemplate`.

    """

    def _flowables(self, document):
        yield document.document_tree


class FixedDocumentPartTemplate(DocumentPartTemplate):
    """A document part template that renders a fixed list of flowables"""

    flowables = Option(FlowablesList, [], 'The list of flowables to include '
                                          'in this document part')

    @property
    def doc_kwargs(self):
        kwargs = OrderedDict()
        kwargs['flowables'] = '``{}``'.format(self._flowables)
        kwargs.update(super().doc_kwargs)
        return kwargs

    def _flowables(self, document):
        return document.get_template_option(self.name, 'flowables')


class TemplateConfiguration(RuleSet):
    """Stores a configuration for a :class:`DocumentTemplate`

    Args:
        name (str): a label for this template configuration
        base (TemplateConfiguration): the template configuration to extend
        template (DocumentTemplateMeta or str): the document template to
            configure
        description (str): a short string describing this style sheet
        **options: configuration values for the configuration attributes
            defined by the document :attr:`template`

    """

    template = None
    """The :class:`.DocumentTemplate` subclass to configure"""

    def __init__(self, name, base=None, source=None,
                 template=None, description=None, **options):
        if template:
            if isinstance(template, str):
                template = DocumentTemplate.from_string(template)
            assert self.template in (None, template)
            self.template = template
        tmpl_cls = self.template
        for attr, val in options.items():
            options[attr] = self._validate_attribute(tmpl_cls, attr, val)
        base = base or self.template
        super().__init__(name, base=base, source=source, **options)
        self.description = description

    def get_entries(self, name, document):
        if name in self:
            yield self[name]
        if self.base:
            yield from self.base.get_entries(name, document)
        raise KeyError(name)

    def get_attribute_value(self, name):
        if name in self:
            return self[name]
        return self.base.get_attribute_value(name)

    def get_entry_class(self, name):
        try:
            template = self.template.get_template(name)
        except KeyError:
            raise ValueError("'{}' is not a template used by {}"
                             .format(name, self.template))
        return type(template)

    def document(self, document_tree, backend=None):
        """Create a :class:`DocumentTemplate` object based on the given
        document tree and this template configuration

        Args:
            document_tree (DocumentTree): tree of the document's contents
            backend: the backend to use when rendering the document

        """
        return self.template(document_tree, configuration=self,
                             backend=backend)


class TemplateConfigurationFile(RuleSetFile, TemplateConfiguration):

    main_section = 'TEMPLATE_CONFIGURATION'

    def process_section(self, section_name, classifier, items):
        if section_name in StringCollection.subclasses:
            collection_cls = StringCollection.subclasses[section_name]
            strings = self.setdefault('strings', Strings())
            collection_items = {name: StyledText.from_string(value)
                                for name, value in items}
            strings[collection_cls] = collection_cls(**collection_items)
        else:
            template_class = self.get_entry_class(section_name)
            self[section_name] = template_class(**dict(items))


class DocumentTemplateMeta(WithAttributes):
    def __new__(mcls, classname, bases, cls_dict):
        templates = cls_dict['_templates'] = OrderedDict()
        cls = super().__new__(mcls, classname, bases, cls_dict)
        for name, attr in cls_dict.items():
            if isinstance(attr, Template):
                templates[name] = attr
        if templates:
            doc = []
            for name, template in templates.items():
                attr_type = type(template)
                base = (':attr:`{}`'.format(template.base)
                        if template.base else '``None``')
                tmpl_doc = ('{} (:class:`.{}`): base: {}'
                            .format(name, attr_type.__name__, base))
                if template:
                    defaults = []
                    for name, value in template.items():
                        defaults.append('- :attr:`~.{}.{}` = ``{}``'
                                        .format(attr_type.__name__, name,
                                                value))
                    tmpl_doc += ('\n\n         Overrides these defaults:'
                                 '\n\n            '
                                 + '\n            '.join(defaults) + '\n')
                doc.append(tmpl_doc)
                template.template_configuration = cls

            templ_doc = '\n        '.join(chain(['\n\n    Attributes:'], doc))
            cls.__doc__ += templ_doc

        cfg_class_name = classname + 'Configuration'
        cfg_class = type(cfg_class_name, (TemplateConfiguration, ),
                         dict(template=cls))
        # assign this document template's configuration class a name at the
        # module level so that Sphinx can pickle instances of it
        cls.Configuration = globals()[cfg_class_name] = cfg_class

        file_class_name = classname + 'ConfigurationFile'
        file_class = type(file_class_name, (TemplateConfigurationFile, ),
                          dict(template=cls))
        cls.ConfigurationFile = globals()[file_class_name] = file_class
        return cls

    def get_template(cls, name):
        try:
            for klass in cls.__mro__:
                if name in klass._templates:
                    return klass._templates[name]
        except AttributeError:
            pass
        raise KeyError(name)

    def get_attribute_value(cls, name):
        return cls._get_default(name)

    def get_entries(cls, name, document):
        if name in cls._templates:
            yield cls._templates[name]
        m = cls.RE_PAGE.match(name)
        if m:
            general_template = m.group(1) + '_page'
            yield cls._templates[general_template]

    def _get_value_recursive(cls, name, attribute):
        if name in cls._templates:
            template = cls._templates[name]
            if attribute in template:
                return template[attribute]
            elif isinstance(template.base, str):
                return cls._get_value_recursive(template.base, attribute)
            elif template.base is not None:
                return template.base[attribute]
        raise DefaultValueException


class PartsList(AttributeType, list):
    """Stores the names of the document part templates making up a document

    Args:
        *parts (list[str]): the names of the document parts

    """

    def __init__(self, *parts):
        super().__init__(parts)

    def __str__(self):
        return ' '.join(self.parts)

    @classmethod
    def check_type(cls, value):
        if not (super().check_type(value) or isinstance(value, list)):
            return False
        return all(isinstance(item, str) for item in value)

    @classmethod
    def parse_string(cls, string, source):
        return cls(*string.split())

    @classmethod
    def doc_repr(cls, value):
        return ' '.join(':attr:`{}`'.format(part)
                        for part in value) or '(empty list)'

    @classmethod
    def doc_format(cls):
        return 'a space-separated list of document part template names'



class DocumentTemplate(Document, AttributesDictionary, Resource,
                       metaclass=DocumentTemplateMeta):
    """Template for documents

    Args:
        document_tree (DocumentTree): a tree of the document's contents
        configuration (TemplateConfiguration): configuration for this template
        backend: the backend used for rendering the document

    """

    resource_type = 'template'

    language = Attribute(Language, EN, 'The main language of the document')
    strings = Attribute(Strings, None, 'Strings to override standard element '
                                       'names')
    stylesheet = Attribute(StyleSheet, sphinx, 'The stylesheet to use for '
                                               'styling document elements')

    parts = Attribute(PartsList, [], 'The parts making up this document')

    variables = {'paper_size': A4}      # default variable values

    def __init__(self, document_tree, configuration=None, backend=None):
        self.configuration = (configuration if configuration is not None
                              else self.Configuration('empty'))
        self.options = document_tree.options
        stylesheet = self.get_option('stylesheet')
        language = self.get_option('language')
        strings = self.get_option('strings')
        super().__init__(document_tree, stylesheet, language, strings=strings,
                         backend=backend)
        parts = self.get_option('parts')
        try:
            self.part_templates = [next(self._find_templates(name))
                                   for name in parts]
        except KeyError as exc:
            raise ValueError("The '{}' document template has no part named"
                             " '{}'".format(type(self).__name__, *exc.args))
        self._to_insert = {}

    def _find_templates(self, name):
        """Yields all :class:`Template`\\ s in the template hierarchy:

        - template matching `name` in this TemplateConfiguration
        - templates in base TemplateConfigurations (recursively)
        - the default template defined in the DocumentTemplate class

        """
        return self.configuration.get_entries(name, self)

    RE_PAGE = re.compile('^(.*)_(right|left)_page$')

    @classmethod
    def get_variable(cls, configuration_class, attribute, variable):
        try:
            value = cls.variables[variable.name]
        except KeyError:
            raise VariableNotDefined("Document template provides no default "
                                     "for variable '{}'".format(variable.name))
        return configuration_class.attribute_type(attribute).validate(value)

    def get_option(self, option_name):
        return self.configuration.get_attribute_value(option_name)

    def get_template_option(self, template_name, option_name):
        return self.configuration.get_value(template_name, option_name)

    def get_entry_class(self, name):
        template = next(self._find_templates(name))
        return type(template)

    def get_page_template(self, part, right_or_left):
        part_template_name = part.template.name
        label = '{}_page'.format(right_or_left) if right_or_left else 'page'
        templates = self._find_templates(part_template_name + '_' + label)
        return next(templates)

    def insert(self, document_part_name, flowable, position):
        docpart_flowables = self._to_insert.setdefault(document_part_name, [])
        docpart_flowables.append((flowable, position))

    def prepare(self, flowable_target):
        for part_template in self.part_templates:
            part_template.prepare(flowable_target)
