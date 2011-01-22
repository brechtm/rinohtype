#from pfb2pfa_orig import pfb2pfa
from pfb2pfa import pfb2pfa
import timeit

pfb = open('../../../examples/rfic2009/qtmr.pfb', 'rb')
pfa = open('qtmr.pfa', 'w')

def b2a():
    pfb2pfa(pfb, pfa)

time = timeit.timeit(b2a, number=1)

print('{} seconds'.format(time))

pfa.close()
pfb.close()


