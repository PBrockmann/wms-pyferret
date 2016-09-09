
Patrick Brockmann - LSCE

<hr>
2016/09/09

You can now call pyferretWMS.py from pyferret because the gunicorn is now launched from python and
not anymore from command line. All tempory files are properly cleaned when either closing the client application
or either typing a "CTRL+C" when launching from command line.

Test it quicky from a test script:
```python pyferretWPS_test.py 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@max]'```
```

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

![Capture](https://github.com/PBrockmann/wms-pyferret/raw/master/capture_01.png)

![Screencast](https://github.com/PBrockmann/wms-pyferret/raw/master/screencast_01.mkv)

Next steps:
- Read variables and start the gunicorn server directly from pyferret ([Custom Application](http://docs.gunicorn.org/en/stable/custom.html)).
- Propose synchronous maps when 2 (or more) variables are requested to allow direct spatial intercomparison.

Prerequisites:
- pyferret 7.0
- gunicorn
- nw.js

Examples of calls:
- ```./slippy_map.bash 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_viridis temp[k=@max]'```
- ```./slippy_map.bash 'shade/lev=(-inf)(30,40,1)(inf)/pal=mpl_PSU_inferno salt[k=1]'```

Work based on:
- [OpenGIS® Web Map Service Interface Standard (WMS)] (http://www.opengeospatial.org/standards/wms)
- [pyferret] (http://ferret.pmel.noaa.gov/Ferret/documentation/pyferret)
- [gunicorn: a Python WSGI HTTP Server] (http://gunicorn.org)
- [WMS in Leaflet] (http://leafletjs.com/examples/wms/wms.html)
- [Node-Webkit] (http://nwjs.io)
