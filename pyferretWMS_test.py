
# python pyferretWMS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@max]'

import sys
import pyferret, pyferretWMS

pyferretWMS.slippyMap(sys.argv[1])
