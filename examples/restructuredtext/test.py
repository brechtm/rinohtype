from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import AdmonitionTitles
from rinoh.stylesheets import sphinx
from rinoh.template import DocumentOptions, TemplateConfiguration
from rinoh.templates import ArticleTemplate
from rinoh.templates.article import template_conf as article_conf


if __name__ == '__main__':
    strings = (AdmonitionTitles(important='IMPORTANT:',
                                tip='TIP:'),
               )

    template_conf = TemplateConfiguration(article_conf)
    template_conf('title page',
                  top_margin=2*CM)

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        doc_options = DocumentOptions(stylesheet=sphinx)
        document = ArticleTemplate(flowables, strings=strings,
                                   template_configuration=template_conf,
                                   options=doc_options, backend=pdf)
        document.render(name)
