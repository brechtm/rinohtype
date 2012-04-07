
from pyte.backend.pdf.reader import PDFReader



if __name__ == '__main__':
    pdf = PDFReader('../examples/rfic2009/fig2.pdf')
    print(pdf.root.target)
    print(pdf.trailer['Info'].target)
    print(pdf.root['Pages']['Kids'][0].target)
    print(pdf.root['Pages']['Kids'][0]['Contents'].target)
