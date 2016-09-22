
Patrick Brockmann - LSCE

####Display synchronous slippy maps from ferret variables

```
Usage: pyferretWMS.py [--env=script.jnl] [--width=400] [--height=400] [--center=[0,0]] [--zoom=1]
                              'cmd/qualifiers variable; cmd/qualifiers variable'

'cmd/qualifiers variable' is a classic ferret call (no space allowed except to
separate the variable from the command and its qualifiers). The semi-colon character ';'
is the separator between commands and will determine the number of maps to be drawn.
The qualifiers can include the title qualifier considering that the space character
is not allowed since used to distinguish the cmd/qualifiers and the variable(s).
For this, you can use the HTML code '&nbsp' for the non-breaking space (without the ending semi-colon).
For example: 'shade/lev=20/title="Simulation&nbspA" varA; shade/lev=20/title="Simulation&nbspB" varB'

Options:
  --version        show program's version number and exit
  -h, --help       show this help message and exit
  --width=WIDTH    200 < map width <= 600
  --height=HEIGHT  200 < map height <= 600
  --env=ENVSCRIPT  ferret script to set the environment
                   (default=pyferretWMS.jnl). It contains datasets to open,
                   variables definition.
  --center=CENTER  Initial center of maps as [lat, lon] (default=[0,-40])
  --zoom=ZOOM      Initial zoom of maps (default=1)
```

####Examples
* Using the levitus climatology dataset:
```./pyferretWMS.py 'shade/x=-180:180/y=-90:90/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_inferno temp[k=@max]; shade/x=-180:180/y=-90:90/lev=(-inf)(0,140,5)(inf)/pal=mpl_Seq1_RdPu temp[k=@var]; shade/x=-180:180/y=-90:90/lev=(-inf)(30,40,0.5)(inf)/pal=mpl_PSU_viridis salt[k=1]'```

![Screencast](https://github.com/PBrockmann/wms-pyferret/raw/master/screencast.gif)

* Using a NEMO configuration (curvilinear grid) focussed on Mediterranean sea:
```./pyferretWMS.py --zoom 3 --center [40,15] --width 500 --env MED8.jnl 'shade/lev=20v/pal=mpl_PSU_inferno/title="O2" O2, nav_lon, nav_lat; shade/lev=20v/pal=mpl_PSU_viridis/title="NO3" NO3, nav_lon, nav_lat'```

![Capture](https://github.com/PBrockmann/wms-pyferret/raw/master/capture.png)

Palettes used are available from: http://www.pmel.noaa.gov/maillists/tmap/ferret_users/fu_2015/msg00475.html
or from https://github.com/PBrockmann/fast

####Requirements
* **pyferret** that can be installed from usual way from http://ferret.pmel.noaa.gov/Ferret/downloads/pyferret/
or from conda-forge channel from https://anaconda.org/conda-forge/pyferret
* **gunicorn** (http://gunicorn.org) at 19.6.0 release to be installed from conda:
```
conda install gunicorn
```
* **nwjs** (http://nwjs.io/downloads/), choose LTS.

####Installation notes
* on Mac OS X: nwjs should be renamed nw and accessible with the $PATH environment variable (or changed in pyferretWMS.py)

####Releases notes
<hr>
2016/09/21

* Add map center and zoom option
* Change call to allow curvilinear grid plot (shade command with 3 arguments) 


<hr>
2016/09/20

An environment script is loaded from the master process. All datasets loaded and variables defined are
then available from the different workers.
Depending the number of commands separated by ; passed as argument, you can now get until 4 synchronous maps
with colorbars (keys) made from qualifiers specified.

<hr>
2016/09/16

Slippy map is now made from multiple workers. Problem: the dataset and variables if defined
should be passed somehow to the workers. I haven't found yet how to enherit from the calling
environment.

Also how this should be called ? From a external function ? As a new command ?

Speed for creating tiles is also an issue especially when you work with a curvilinear grid quite large
(1440x1021), even with several workers.

<hr>
2016/09/09

You can now get slippy maps by a simple ```import pyferretWMS``` and a call to ```pyferretWMS.slippyMap()```.
It is made possible because the gunicorn is now launched directly from python and not anymore from command line. 
All temporary files (png tiles and the html + package.json for the nw application)
are cleaned properly when exiting (either by closing the client application or by typing "CTRL+C" when launched from a python script).

Test it quicky from:
```python pyferretWMS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@max]'```

<hr>
2016/09/06

The idea developed in this early prototype is to render variables read and computed from pyferret as slippy maps.
This can be done directly from the memory without having to save them in netCDF files 
and expose them through a Thredds server to get a Web Map Service.

The tiles are generated by "workers" from a gunicorn server, a python WSGI HTTP server,
and they use pyferret for the rendering. You can then use the classic ferret syntax to display
your variable in a fully pan-and-zoom environment.

Slippy maps avoid the command-line typing and display loops and hopefully will help us on model analysis. 
Moreover, considering that nowdays models are becoming incredibily refined with sometimes resolutions at 1/12°.
That makes the pan/zoom navigation even more useful.

Next steps:
- Read variables and start the gunicorn server directly from pyferret ([Custom Application](http://docs.gunicorn.org/en/stable/custom.html)).
- Propose synchronous maps when 2 (or more) variables are requested to allow direct spatial intercomparison.

Examples of calls:
- ```./slippy_map.bash 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_viridis temp[k=@max]'```
- ```./slippy_map.bash 'shade/lev=(-inf)(30,40,1)(inf)/pal=mpl_PSU_inferno salt[k=1]'```

####Work based on
- [OpenGIS® Web Map Service Interface Standard (WMS)] (http://www.opengeospatial.org/standards/wms)
- [pyferret] (http://ferret.pmel.noaa.gov/Ferret/documentation/pyferret)
- [gunicorn: a Python WSGI HTTP Server] (http://gunicorn.org)
- [WMS in Leaflet] (http://leafletjs.com/examples/wms/wms.html)
- [Node-Webkit] (http://nwjs.io)
