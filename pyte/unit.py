
from pyte.dimension import Dimension

_pt = {
       'pt'  :   1,
       'inch':   72,
       'cm'  :   72/2.54,
       'mm'  :   72/25.4,
       'm'   :   72/0.0254,
      }

pt   = Dimension(1)
inch = Dimension(_pt['inch'])
cm   = Dimension(_pt['cm'])
mm   = Dimension(_pt['mm'])
m    = Dimension(_pt['m'])
