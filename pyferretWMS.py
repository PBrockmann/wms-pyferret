
from __future__ import print_function

import multiprocessing

import gunicorn.app.base
from gunicorn.six import iteritems

import os, sys
import shutil
import tempfile
import pyferret
from paste.request import parse_formvars
import subprocess

from jinja2 import Template

#==============================================================
# Global variables
cmd = ''
tmpdir = ''

#==============================================================
def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1		# 	get "Error 13: Permission denied" on the dataset when more than 1 worker ??


#==============================================================
def handler_app(environ, start_response):

    fields = parse_formvars(environ)
    if environ['REQUEST_METHOD'] == 'GET':
        
        CMDarr = cmd.split()
        CMD = CMDarr[0]                             # get the ferret command to append needed qualifiers
        VARIABLE = ' '.join(CMDarr[1:])             # 1 variable or 3 variables as var2D, lon2D, lat2D for curvilinear grids

        HEIGHT = int(fields['HEIGHT'])
        WIDTH = int(fields['WIDTH'])
    
        # BBOX=xmin,ymin,xmax,ymax
        BBOX = fields['BBOX'].split(',')

        hlim = "/hlim=" + BBOX[0] + ":" + BBOX[2]
        vlim = "/vlim=" + BBOX[1] + ":" + BBOX[3]

        try:
                pyferret.run('set window/outline=5/aspect=1')           # outline=5 is a strange setting but works otherwise get outline around polygons
                pyferret.run('go margins 0 0 0 0')
                
                #print(CMD +  "/x=-180:180/y=-90:90/noaxis/nolab/nokey" + hlim + vlim + " " + VARIABLE)
                pyferret.run(CMD +  "/x=-180:180/y=-90:90/noaxis/nolab/nokey" + hlim + vlim + " " + VARIABLE)
       
                tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
                #pyferret.saveplot(tmpname, xpix=WIDTH, qual='/format=PNG/transparent')         # could be faster if saveplot would allow stringIO (ie buffer)
                tmpname = os.path.basename(tmpname)
                pyferret.run("frame/format=PNG/transparent/xpixels=" + str(WIDTH) + "/file=" + tmpname)

                if os.path.isfile(tmpname):
                        ftmp = open(tmpname, "rb")
                        img = ftmp.read()
                        ftmp.close()
                        os.remove(tmpname)
      
                start_response('200 OK', [('content-type', 'image/png')])
                return iter(img) 
    
        except:
                return iter("Exception caught")

#==============================================================
class myArbiter(gunicorn.arbiter.Arbiter):

    def halt(self):
	print("Removing temporary directory: ", tmpdir)
	shutil.rmtree(tmpdir)
        super(myArbiter, self).halt()


#==============================================================
class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
	global tmpdir
        tmpdir = tempfile.mkdtemp()
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
	master_pid = os.getppid()
	print("---------> gunicorn master pid: ", master_pid)

	instance_WMS_Client = Template(template_WMS_client())
	instance_NW_Package = Template(template_nw_package())
	with open(tmpdir + "/index.html", "wb") as f:
    		f.write(instance_WMS_Client.render(cmd=cmd, gunicornPID=master_pid))
	with open(tmpdir + "/package.json", "wb") as f:
    		f.write(instance_NW_Package.render())
	print("Temporary directory to remove: ", tmpdir)
	
    	proc = subprocess.Popen(['nw', tmpdir])
    	print('Client nw process: ', proc.pid)

        return self.application

# if control before exiting is needed
    def run(self):
        try:
            myArbiter(self).run()
        except RuntimeError as e:
            print("\nError: %s\n" % e, file=sys.stderr)
            sys.stderr.flush()
	    sys.exit(1)

#==============================================================
def slippyMap(cmdRequested):

    global cmd 

    cmd = cmdRequested

    options = {
        'bind': '%s:%s' % ('127.0.0.1', '8000'),
        'workers': 1,
        #'workers': number_of_workers(),		# 	get "Error 13: Permission denied" on the dataset when more than 1 worker ??
        'worker_class': 'sync',
        'threads': 1 
    }
    StandaloneApplication(handler_app, options).run()

#==============================================================
def template_WMS_client():

    return '''
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Slippy map with WMS from pyferret</title>

    <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/leaflet/1.0.0-rc.3/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.0.0-rc.3/leaflet.js"></script>

    <style type="text/css">
        html, body { font-family: "arial" }
        #cmd { font-size: 12px; margin-left: 50px; }
        #map1 { float: left; width: 600px; height: 400px; margin-left: 50px; margin-top: 10px; }
    </style>
</head>

<body>

    <div id="cmd">{{ cmd }}</div>
    <div id="map1"></div>

    <script type="text/javascript">

    //===============================================
    var crs = L.CRS.EPSG4326;
    //var crs = L.CRS.EPSG3857;

    //===============================================
    // Only in EPSG:4326
    var wmspyferret = L.tileLayer.wms("http://localhost:8000", {
        crs: crs,
    	format: 'image/png',
    	transparent: true,
    	attribution: 'pyferret',
	uppercase: true
    });

    //===============================================
    // Following services are available in EPSG:4326 
    //var layer = L.tileLayer('http://server.arcgisonline.com/ArcGis/rest/services/ESRI_StreetMap_World_2D/MapServer/tile/{z}/{y}/{x}');
    //var layer = L.tileLayer('http://server.arcgisonline.com/ArcGis/rest/services/ESRI_Imagery_World_2D/MapServer/tile/{z}/{y}/{x}');

    // Following services are available in EPSG:3857
    //var layer = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}');

    //===============================================
    // Following service is available in EPSG:3857 and EPSG:4326
    var frontiers = L.tileLayer.wms("http://www.globalcarbonatlas.org:8080/geoserver/GCA/wms", {
    	layers: 'GCA:GCA_frontiersCountryAndRegions',
    	format: 'image/png',
        crs: crs,
    	transparent: true
    });

    //===============================================
    var map1 = L.map('map1', {
        //layers: [layer, wmspyferret],
        layers: [wmspyferret, frontiers],
        crs: crs,
        center: [0, 0],
        zoom: 2 
    });

    //===============================================
    var exec = require('child_process').exec,child;

    process.stdout.write('Starting NW application\\n');
    process.on('exit', function (){
  	process.stdout.write('Exiting from NW application, now killing the gunicorn server\\n');
  	process.kill({{ gunicornPID }});			// kill gunicorn server
    });

    </script>
</body>
</html>
'''

#==============================================================
def template_nw_package():

    return '''
{
  "name": "Slippy maps from pyferret",
  "main": "index.html",
  "window": {
          "toolbar": false,
          "width": 700,
          "height": 500
          }
}
'''
