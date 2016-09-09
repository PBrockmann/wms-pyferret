
# python test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@max]'

import sys
import pyferret, pyferretWMS

pyferret.start(quiet=True, journal=False, unmapped=True)

pyferret.run('use levitus_climatology')
pyferretWMS.slippyMap(sys.argv[1])
