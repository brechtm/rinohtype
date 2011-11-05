
from psg.document.dsc import dsc_document


class Document(object):
    def __init__(self, title):
        self.psg_doc = dsc_document(title)

    def write(self, filename):
        fp = open(filename, "w", encoding="latin-1")
        self.psg_doc.write_to(fp)
        fp.close()


class Page(object):
    def __init__(self, ):
        pass


class Canvas(object):
    def __init__(self, ):
        pass
