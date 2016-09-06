
<li><pre>gunicorn -w 4 --env CMD='shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_viridis temp[k=@max]' myapp_request_pyferret_01:app</pre>
<li><pre>gunicorn -w 4 --env CMD='shade/lev=(-inf)(-10,30,1)(inf)/pal=mpl_PSU_plasma temp[k=@var]' myapp_request_pyferret_01:app</pre>
<li><pre>gunicorn -w 4 --env CMD='shade/lev=(-inf)(20,40,1)(inf)/pal=mpl_PSU_inferno salt[k=1]' myapp_request_pyferret_01:app</pre>


<li><a href="http://www.opengeospatial.org/standards/wms" target="_blank">OpenGIS® Web Map Service Interface Standard (WMS)</a>
<li><a href="http://ferret.pmel.noaa.gov/Ferret/documentation/pyferret" target="_blank">pyferret</a>
<li><a href="http://gunicorn.org/" target="_blank">gunicorn: a Python WSGI HTTP Server</a>
<li><a href="http://leafletjs.com/examples/wms/wms.html" target="_blank">WMS in Leaflet</a>
<li><a href="http://nwjs.io/" target="_blank">Node-Webkit</a>

