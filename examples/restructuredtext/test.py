from rst import ReStructuredTextDocument, STYLESHEET


if __name__ == '__main__':
#    for name in ('quickstart', 'FAQ', 'THANKS'):
    for name in ('optionlist', ):
        document = ReStructuredTextDocument(name + '.txt', STYLESHEET)
        document.render(name)
