
This idea is to render variables read and computed from pyferret as slippy maps. 

It is very useful since it avoids the command typing and display loops. 
Moreover considering that nowdays models are becoming incredibily refined with sometimes resolutions at 1/12°.
That makes the pan/zoom navigation even more useful.

Prerequisites:
- pyferret 7.0
- gunicorn
- nw.js

Examples:
- ```./slippy_map 'shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_viridis temp[k=@max]'```
- ```./slippy_map 'shade/lev=(-inf)(30,40,1)(inf)/pal=mpl_PSU_inferno salt[k=1]'```

- [OpenGIS® Web Map Service Interface Standard (WMS)] (http://www.opengeospatial.org/standards/wms)
- [pyferret] (http://ferret.pmel.noaa.gov/Ferret/documentation/pyferret)
- [gunicorn: a Python WSGI HTTP Server] (http://gunicorn.org)
- [WMS in Leaflet] (http://leafletjs.com/examples/wms/wms.html)
- [Node-Webkit] (http://nwjs.io)
