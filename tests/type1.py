

from rinoh.font.type1 import Type1Font


if __name__ == '__main__':
    pfb = Type1Font(r'..\examples\rfic2009\fonts\qtmr')
    print(pfb.header.decode('ascii'))
