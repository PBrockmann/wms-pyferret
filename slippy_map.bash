#!/bin/bash

#-------------------------------------
# Example: 
# ./slippy_map.bash 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_viridis temp[k=@max]'
# ./slippy_map.bash 'shade/lev=(-inf)(30,40,1)(inf)/pal=mpl_PSU_inferno salt[k=1]'

#-------------------------------------
# launch NodeWebkit with slippy_map.html (package.json)
nw . &

#-------------------------------------
# launch gunicorn to render tiles from pyferret
gunicorn -w 4 --env CMD="$1" myapp_request_pyferret_01:app
