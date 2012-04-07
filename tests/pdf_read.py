
from pyte.backend.pdf.reader import PDFReader



if __name__ == '__main__':
    pdf = PDFReader('../examples/rfic2009/fig2.pdf')
    print(pdf.catalog)
    print(pdf.info)
    print(pdf.catalog['Pages']['Kids'][0].target)
    print(pdf.catalog['Pages']['Kids'][0]['Contents'].target)
    pdf.write('../examples/rfic2009/fig2_out.pdf')
