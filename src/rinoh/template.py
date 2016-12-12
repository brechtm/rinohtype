# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re

from collections import OrderedDict
from functools import partial
from itertools import chain

from . import styleds, reference
from .attribute import (Bool, Integer, Attribute, AttributesDictionary,
                        RuleSet, RuleSetFile, WithAttributes, AttributeType,
                        OptionSet, AcceptNoneAttributeType, VariableNotDefined,
                        OverrideDefault)
from .dimension import Dimension, CM, PT, PERCENT
from .document import Document, DocumentPart, Page, PageOrientation, PageType
from .element import create_destination
from .image import BackgroundImage, Image
from .flowable import Flowable
from .language import Language, EN
from .layout import (Container, DownExpandingContainer, UpExpandingContainer,
                     FlowablesContainer, FootnoteContainer, ChainedContainer,
                     BACKGROUND, CONTENT, HEADER_FOOTER, CHAPTER_TITLE)
from .number import NumberFormat
from .paper import Paper, A4
from .paragraph import Paragraph
from .reference import (Field, SECTION_NUMBER, SECTION_TITLE,
                        PAGE_NUMBER, NUMBER_OF_PAGES)
from .resource import Resource
from .text import StyledText, Tab
from .strings import StringField, StringCollection, Strings
from .structure import Header, Footer, SectionTitles, HorizontalRule
from .style import StyleSheet, CharIterator, parse_string
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


class Templated(object):
    def get_option(self, option, document):
        return document.get_template_option(self.template_name, option)


class Template(AttributesDictionary, NamedDescriptor):
    def get_value(self, attribute, document):
        try:
            return super().get_value(attribute, document.configuration)
        except KeyError:
            bases = []
            if isinstance(self.base, str):
                iter = document._find_templates(self.base)
                try:
                    bases.extend(iter)
                except KeyError:
                    raise ValueError("Could not find the base template '{}' "
                                     "for the '{}' page template."
                                     .format(self.base, self.name))
            elif self.base is not None:
                bases.append(self.base)
            for base_template in bases:
                try:
                    return base_template.get_value(attribute, document)
                except KeyError:
                    continue
        raise KeyError


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
    def parse_string(cls, string):
        locals = {}
        locals.update(reference.__dict__)
        locals.update(styleds.__dict__)
        return eval(string, {'__builtins__':{}}, locals)

    @classmethod
    def doc_format(cls):
        return ('Python source code that represents a list of '
                ':class:`.Flowable`\ s')


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
    def __init__(self, document_part, template_name, page_number, after_break):
        get_option = partial(self.get_option, document=document_part.document)
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
    def __init__(self, document_part, template_name, page_number, chain,
                 new_chapter):
        super().__init__(document_part, template_name, page_number, new_chapter)
        get_option = partial(self.get_option, document=document_part.document)
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
        for flowable in self.get_option('chapter_title_flowables',
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
    def __init__(self, document_part, template_name, page_number, after_break):
        super().__init__(document_part, template_name, page_number,
                         after_break)
        get_option = partial(self.get_option, document=self.document)
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
        doc = ('**{}** (:class:`{}.{}`)\n\n'\
               .format(self.name, type(self).__module__, type(self).__name__))
        for name, default_value in self.items():
            doc += '  - *{}*: ``{}``\n'.format(name, default_value)
        return doc

    def prepare(self, fake_container):
        for flowable in self.all_flowables(fake_container.document):
            flowable.prepare(fake_container)

    def _flowables(self, document):
        """Return a list of :class:`rinoh.flowable.Flowable`\ s that make up
        the document part"""
        raise NotImplementedError

    def all_flowables(self, document):
        extra_flowables = document._to_insert.get(self.name, ())
        flowables = [flowable for flowable in self._flowables(document)]
        for flowable, position in extra_flowables:
            flowables.insert(position, flowable)
        return flowables

    def document_part(self, document, first_page_number):
        flowables = self.all_flowables(document)
        if flowables or not self.drop_if_empty:
            return DocumentPart(self, document, flowables)


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

    def __init__(self, name, base=None, template=None, description=None,
                 **options):
        if template:
            if isinstance(template, str):
                template = DocumentTemplate.from_string(template)
            assert self.template in (None, template)
            self.template = template
        if isinstance(options.get('stylesheet'), str):
            filename = os.path.join(self._stylesheet_search_path,
                                    options['stylesheet'])
            if os.path.isfile(filename):
                options['stylesheet'] = filename
        tmpl_cls = self.template
        for attr, value in options.items():
            options[attr] = tmpl_cls.validate_attribute(attr, value, True)
        super().__init__(name, base=base, **options)
        self.description = description

    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            return self.template._get_default(name)

    @property
    def _stylesheet_search_path(self):
        return os.getcwd()

    def _find_templates_recursive(self, name): # FIXME: duplicates __getitem__?
        if name in self:
            yield self[name]
        if self.base:
            for template in self.base._find_templates_recursive(name):
                yield template

    def get_entry_class(self, name):
        try:
            template = self.template.get_default_template(name)
        except KeyError:
            raise ValueError("'{}' is not a template used by {}"
                             .format(name, self.template))
        return type(template)

    def get_variable(self, name, accepted_type):
        try:
            return super().get_variable(name, accepted_type)
        except VariableNotDefined:
            try:
                return self.template.variables[name]
            except KeyError:
                raise

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

    @property
    def _stylesheet_search_path(self):
        return os.path.dirname(self.filename)

    def process_section(self, section_name, classifier, items):
        if section_name in StringCollection.subclasses:
            collection_cls = StringCollection.subclasses[section_name]
            strings = self.setdefault('strings', Strings())
            collection_items = {name: parse_string(CharIterator(value))
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
    def parse_string(cls, string):
        return cls(*string.split())

    @classmethod
    def doc_repr(cls, value):
        space = '\ ``\N{NO-BREAK SPACE}``\ '
        return space.join(':attr:`{}`'.format(part)
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

    variables = dict(paper_size=A4)

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
        self.part_templates = [next(self._find_templates(name))
                               for name in parts]
        self._defaults = OrderedDict()
        self._to_insert = {}

    def _find_templates(self, name):
        """Yields all :class:`Template`\ s in the template hierarchy:

        - template matching `name` in this TemplateConfiguration
        - templates in base TemplateConfigurations (recursively)
        - the default template defined in the DocumentTemplate class

        """
        for template in self.configuration._find_templates_recursive(name):
            yield template
        yield self.get_default_template(name)

    RE_PAGE = re.compile('^(.*)_(right|left)_page$')

    @classmethod
    def get_default_template(cls, template_name):
        try:
            return cls._get_default_template_recursive(template_name)
        except KeyError:
            m = cls.RE_PAGE.match(template_name)
            if m:
                general_template = m.group(1) + '_page'
                return cls._get_default_template_recursive(general_template)

    @classmethod
    def _get_default_template_recursive(cls, template_name):
        for mro_cls in cls.__mro__:
            try:
                templates = mro_cls._templates
            except AttributeError:
                break
            else:
                if template_name in templates:
                    return templates[template_name]
        raise KeyError("No '{}' template found", template_name)

    def get_option(self, option_name):
        return self.configuration[option_name]

    def get_template_option(self, template_name, option_name):
        for template in self._find_templates(template_name):
            try:
                return template.get_value(option_name, self)
            except KeyError:
                continue
        return template._get_default(option_name)

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

    def prepare(self):
        class FakeContainer(object):    # TODO: clean up
            document = self

        for part_template in self.part_templates:
            part_template.prepare(FakeContainer)
