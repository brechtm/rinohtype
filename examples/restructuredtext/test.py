
from rst import ReStructuredTextDocument


if __name__ == '__main__':
    for name in ('quickstart', ):
        document = ReStructuredTextDocument(name + '.txt')
        document.render(name)
