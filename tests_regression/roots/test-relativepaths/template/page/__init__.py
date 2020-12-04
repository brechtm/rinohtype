from pathlib import Path

from rinoh.dimension import PERCENT
from rinoh.image import Image
from rinoh.layout import DownExpandingContainer, CONTENT
from rinoh.template import PageTemplateBase, PageBase


class MyTitlePageTemplate(PageTemplateBase):
    def page(self, document_part, page_number, chain, after_break, **kwargs):
        return MyTitlePage(document_part, self.name, page_number, after_break)


class MyTitlePage(PageBase):
    configuration_class = MyTitlePageTemplate

    def __init__(self, document_part, template_name, page_number, after_break):
        super().__init__(document_part, template_name, page_number,
                         after_break)
        metadata = self.document.metadata
        get_metadata = self.document.get_metadata
        self.title = DownExpandingContainer('title', CONTENT, self,
                                            self.left_margin, self.top_margin,
                                            self.body_width)
        if 'logo' in metadata:
            self.title << Image(get_metadata('logo'),
                                style='title page logo',
                                limit_width=100*PERCENT)
        self.title << Image(Path(__file__).parent / 'page_template.png',
                            scale=2)
        self.title << self.document.TEMPLATE_IMAGE
