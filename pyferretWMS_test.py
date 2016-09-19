
# 1 map
#python ./pyferretWMS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_inferno temp[k=@max]'

# 2 maps
#python ./pyferretWMS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_inferno temp[k=@max]; shade/lev=(-inf)(0,120,5)(inf)/pal=mpl_Seq1_YlOrBr temp[k=@var]'

# 3 maps
#python ./pyferretWMS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_inferno temp[k=@max]; shade/lev=(-inf)(0,120,5)(inf)/pal=mpl_Seq1_YlOrBr temp[k=@var]; shade/lev=(-inf)(30,40,0.5)(inf)/pal=mpl_PSU_viridis salt[k=1]'


import sys
import pyferretWMS

pyferretWMS.slippyMap(sys.argv[1])
