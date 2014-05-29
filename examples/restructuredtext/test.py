from rst import ReStructuredTextDocument


if __name__ == '__main__':
#    for name in ('quickstart', 'FAQ', 'THANKS'):
    for name in ('optionlist', ):
        document = ReStructuredTextDocument(name + '.txt')
        document.render(name)
