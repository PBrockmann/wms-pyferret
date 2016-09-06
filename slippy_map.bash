#!/bin/bash

# launch NodeWebkit with slippy_map.html (package.json)
nw . &

# launch gunicorn to render tiles from pyferret
#gunicorn -w 4 --env CMD='shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@var]' myapp_request_pyferret_01:app
gunicorn -w 4 --env CMD="$1" myapp_request_pyferret_01:app
