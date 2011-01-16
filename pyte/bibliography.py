
# http://sourceforge.net/mailarchive/message.php?msg_id=25355232

# http://dret.net/bibconvert/tex2unicode

#from citeproc import

from lxml import objectify


class CustomDict(dict):
    def __init__(self, required, optional):
        attributes = optional
        attributes.update(required)
        for key, value in attributes.items():
            self[key] = value

    def __getattr__(self, name):
        return self[name]


class Reference(CustomDict):
    def __init__(self, id, type, title, authors, **optional):
        required = {'id': id, 'type': type, 'title': title, 'author': authors}
        super().__init__(required, optional)


class Name(CustomDict):
    def __init__(self, given, family, **optional):
        required = {'given': given, 'family': family}
        super().__init__(required, optional)


class Bibliography(list):
    def __init__(self, source, formatter):
        self.source = source
        self.formatter = formatter
        formatter.bibliography = self

    def cite(self, reference):
        self.append(reference)
        return self.formatter.format_citation(reference)

    def bibliography(self):
        raise NotImplementedError


class BibliographyFormatter(object):
    def format_citation(self, reference):
        raise NotImplementedError

    def format_bibliography(self, reference):
        raise NotImplementedError


class BibliographySource(dict):
    def add(self, entry):
        self[entry.id] = entry


class PseudoCSLDataXML(BibliographySource):
    def __init__(self, filename):
        self.xml = objectify.parse(filename)
        self.root = self.xml.getroot()
        for ref in self.root.ref:
            self.add(self.parse_reference(ref))

    def parse_reference(self, ref):
        authors = []
        for name in ref.author.name:
            authors.append(self.parse_name(name))
        return Reference(ref.attrib['id'], ref.type, ref.title, authors)

    def parse_name(self, name):
        return Name(name.given, name.family)


class BibTeX(BibliographySource):
    pass


class MODS(BibliographySource):
    pass