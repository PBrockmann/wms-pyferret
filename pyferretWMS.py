#!/usr/bin/env python

from __future__ import print_function

import multiprocessing

import gunicorn.app.base
from gunicorn.six import iteritems

import os, sys
import re
import shutil
import tempfile
import pyferret
from paste.request import parse_formvars
import subprocess

from jinja2 import Template
import itertools
from PIL import Image

#==============================================================
def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

#==============================================================
def handler_app(environ, start_response):

    fields = parse_formvars(environ)
    if environ['REQUEST_METHOD'] == 'GET':
        
        try:
		if fields['SERVICE'] != 'WMS':
			raise

        	COMMAND = fields['COMMAND']
        	VARIABLE = fields['VARIABLE']

        	pyferret.run('go ' + envScript)                 # load the environment (dataset to open + variables definition)

                tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
                tmpname = os.path.basename(tmpname)

		#print(fields['REQUEST'] + ': ' + COMMAND + ' ' + VARIABLE)
		if fields['REQUEST'] == 'GetColorBar':
                	pyferret.run('set window/aspect=1/outline=0')
                	pyferret.run('go margins 2 4 3 3')
                	pyferret.run(COMMAND + '/set_up ' + VARIABLE)
                	pyferret.run('ppl shakey 1, 0, 0.15, , 3, 9, 1, `($vp_width)-1`, 1, 1.25 ; ppl shade')
                	pyferret.run('frame/format=PNG/transparent/xpixels=400/file="' + tmpdir + '/key' + tmpname + '"')

                	im = Image.open(tmpdir + '/key' + tmpname)
                	box = (0, 325, 400, 375)
                	area = im.crop(box)
                	area.save(tmpdir + '/' + tmpname, "PNG")

		elif fields['REQUEST'] == 'GetMap':
        		WIDTH = int(fields['WIDTH'])
        		HEIGHT = int(fields['HEIGHT'])

        		# BBOX=xmin,ymin,xmax,ymax
        		BBOX = fields['BBOX'].split(',')

        		HLIM = '/hlim=' + BBOX[0] + ':' + BBOX[2]
        		VLIM = '/vlim=' + BBOX[1] + ':' + BBOX[3]

        		pyferret.run('set window/aspect=1/outline=5')           # outline=5 is a strange setting but works otherwise get outline around polygons
        		pyferret.run('go margins 0 0 0 0')
                	pyferret.run(COMMAND +  '/noaxis/nolab/nokey' + HLIM + VLIM + ' ' + VARIABLE)
                	pyferret.run('frame/format=PNG/transparent/xpixels=' + str(WIDTH) + '/file="' + tmpdir + '/' + tmpname + '"')

		else:
			raise

                if os.path.isfile(tmpdir + '/' + tmpname):
                        ftmp = open(tmpdir + '/' + tmpname, 'rb')
                        img = ftmp.read()
                        ftmp.close()
                        os.remove(tmpdir + '/' + tmpname)
      
                start_response('200 OK', [('content-type', 'image/png')])
                return iter(img) 
    
        except:
                return iter('Exception caught')

#==============================================================
class myArbiter(gunicorn.arbiter.Arbiter):

    def halt(self):
	# Close pyferret
        pyferret.stop()

	print('Removing temporary directory: ', tmpdir)
	shutil.rmtree(tmpdir)

        super(myArbiter, self).halt()


#==============================================================
class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):

	# Start pyferret	
        pyferret.start(journal=False, unmapped=True, quiet=True, verify=False)

	master_pid = os.getpid()
	print('---------> gunicorn master pid: ', master_pid)

	if not serverOnly:		# nw will be launched 
		listSynchroMapsToSet = list(itertools.permutations(range(1,nbMaps+1), 2))

		instance_WMS_Client = Template(template_WMS_client())
		instance_NW_Package = Template(template_nw_package())

		with open(tmpdir + '/index.html', 'wb') as f:
    			f.write(instance_WMS_Client.render(cmdArray=cmdArray, gunicornPID=master_pid, 
							   listSynchroMapsToSet=listSynchroMapsToSet,
							   mapWidth=mapWidth, mapHeight=mapHeight, 
							   mapCenter=mapCenter, mapZoom=mapZoom))
		with open(tmpdir + '/package.json', 'wb') as f:
    			f.write(instance_NW_Package.render(nbMaps=nbMaps,
							   mapWidth=mapWidth, mapHeight=mapHeight))

		# Launch NW.js
    		proc = subprocess.Popen(['nw', tmpdir])
    		print('Client nw process: ', proc.pid)

        self.options = options or {}
        self.application = app

        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# if control before exiting is needed
    def run(self):
        try:
            myArbiter(self).run()
        except RuntimeError as e:
            print('\nError: %s\n' % e, file=sys.stderr)
            sys.stderr.flush()
	    sys.exit(1)

#==============================================================
def template_WMS_client():

    return '''
<!doctype html>
<html>
<head>
    <meta charset='utf-8'>
    <title>Slippy maps with WMS from pyferret</title>

    <script src='https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.min.js'></script>
    <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.min.css' />
    <script src='https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js'></script>

    <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.0.1/leaflet.css' />
    <script src='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.0.1/leaflet.js'></script>

    <script src='https://unpkg.com/leaflet.sync@0.0.5'></script>

    <style type='text/css'>
        html, body { font-family: 'arial' }
        .mapContainer { display: inline-block ; margin-left: 10px; margin-top: 10px;}
        .title { font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width:  {{ mapWidth }}px; }
        .map { width: {{ mapWidth }}px; height: {{ mapHeight }}px; }
        .key { text-align: center; margin: auto; }
        .key img { width: {{ mapWidth }}px; height: auto; max-width: 400px; }
	.leaflet-bar a, .leaflet-bar a:hover {
    		height: 16px;
    		line-height: 16px;
    		width: 16px;
	}
	.leaflet-control-zoom-in, .leaflet-control-zoom-out {
    		font-size: 14px;
		text-indent: 0px;
	}
    </style>
</head>

<body>

{% for aDict in cmdArray -%}
<div class='mapContainer'>
   <div id='title{{ loop.index }}' class='title'></div>
   <div id='map{{ loop.index }}' class='map'></div>
   <div id='key{{ loop.index }}' class='key'><img /></div>
</div>
{% endfor -%}

<script type='text/javascript'>

//===============================================
var crs = L.CRS.EPSG4326;

{% for aDict in cmdArray -%}
//===============================================
var wmspyferret{{ loop.index }} = L.tileLayer.wms('http://localhost:8000', {
	command: '{{ aDict.command }}',
	variable: '{{ aDict.variable }}',
    	crs: crs,
	format: 'image/png',
	transparent: true,
    	uppercase: true
});
var frontiers{{ loop.index }} = L.tileLayer.wms('http://www.globalcarbonatlas.org:8080/geoserver/GCA/wms', {
	layers: 'GCA:GCA_frontiersCountryAndRegions',
	format: 'image/png',
    	crs: crs,
	transparent: true
});

var map{{ loop.index }} = L.map('map{{ loop.index }}', {
    layers: [wmspyferret{{ loop.index }}, frontiers{{ loop.index }}],
    crs: crs,
    center: {{ mapCenter }},
    zoom: {{ mapZoom }},
    attributionControl: false
});
{% endfor %}

//===============================================
// Set up synchro between maps
{% for synchro in listSynchroMapsToSet -%}
map{{ synchro[0] }}.sync(map{{ synchro[1] }});
{% endfor %}

//===============================================
{% for aDict in cmdArray -%}
$('#title{{ loop.index }}').html('{{ aDict.title }}');   
$('#title{{ loop.index }}').attr('title', wmspyferret{{ loop.index }}.wmsParams.command + ' ' + wmspyferret{{ loop.index }}.wmsParams.variable);   
$('#key{{ loop.index }}').children('img').attr('src', 'http://localhost:8000/?SERVICE=WMS&REQUEST=GetColorBar' + 
                                                '&COMMAND=' + wmspyferret{{ loop.index }}.wmsParams.command +  
                                                '&VARIABLE=' + wmspyferret{{ loop.index }}.wmsParams.variable);
{% endfor %}

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
  "name": "Slippy maps with WMS from pyferret",
  "main": "index.html",
  "window": {
          "toolbar": false,
          "width": {{ nbMaps*mapWidth + nbMaps*10 + 60 }},
          "height": {{ mapHeight + 100 }} 
          }
}
'''

#==============================================================
from optparse import OptionParser

#------------------------------------------------------
usage = "%prog [--env=script.jnl] [--width=400] [--height=400] [--center=[0,0]] [--zoom=1] [--server]" + \
	"\n                              'cmd/qualifiers variable; cmd/qualifiers variable'" + \
	"\n\n'cmd/qualifiers variable' is a classic ferret call (no space allowed except to" + \
	"\nseparate the variable from the command and its qualifiers). The semi-colon character ';'" +\
	"\nis the separator between commands and will determine the number of maps to be drawn." + \
	"\nThe qualifiers can include the title qualifier considering that the space character" + \
	"\nis not allowed since used to distinguish the cmd/qualifiers and the variable(s)." + \
	"\nFor this, you can use the HTML code '&nbsp' for the non-breaking space (without the ending semi-colon)." + \
	"\nFor example: 'shade/lev=20/title=Simulation&nbspA varA; shade/lev=20/title=Simulation&nbspB varB'"

version = "%prog 0.9.4"

#------------------------------------------------------
parser = OptionParser(usage=usage, version=version)

parser.add_option("--width", type="int", dest="width", default=400,
		help="200 < map width <= 600")
parser.add_option("--height", type="int", dest="height", default=400,
		help="200 < map height <= 600")
parser.add_option("--env", dest="envScript", default="pyferretWMS.jnl",
		help="ferret script to set the environment (default=pyferretWMS.jnl). It contains datasets to open, variables definition.")
parser.add_option("--center", type="string", dest="center", default='[0,-40]',
		help="Initial center of maps as [lat, lon] (default=[0,-40])")
parser.add_option("--zoom", type="int", dest="zoom", default=1,
		help="Initial zoom of maps (default=1)")
parser.add_option("--server", dest="serverOnly", action="store_true", default=False,
		help="Server only (default=False)")

(options, args) = parser.parse_args()

mapWidth =  options.width
mapHeight = options.height
mapCenter = options.center
mapZoom = options.zoom
envScript = options.envScript
serverOnly = options.serverOnly

#------------------------------------------------------
# Global variables
nbMaps = 0
cmdArray = []
tmpdir = tempfile.mkdtemp()

print('Temporary directory to remove: ', tmpdir)

#------------------------------------------------------
if serverOnly:
	if len(args) != 0:
        	parser.error("No argument needed in mode server")
		parser.print_help()

else:
	if len(args) != 1:
        	parser.error("Wrong number of arguments")
		parser.print_help()

	if mapWidth < 200 or mapWidth > 600 or mapHeight < 200 or mapHeight > 600 :
		parser.error("Map size options incorrect")
		parser.print_help()
		sys.exit(1)
	
	if not os.path.isfile(envScript):
		parser.error("Environment script option missing")
		parser.print_help()
		sys.exit(1)
	
	cmdsRequested = args[0]
	
	cmds = cmdsRequested.split(';')		# get individual commands
	cmds = map(str.strip, cmds)  		# remove surrounding spaces if present
	
	nbMaps = len(cmds)
	print(str(nbMaps) + ' maps to draw')
	
	if nbMaps > 4:
		print("\n=======> Error: Maximum number of maps: 4\n")
		parser.print_help()
		sys.exit(1)
	
	# create array of dict {'command', 'variable', 'title'}
	for i,cmd in enumerate(cmds, start=1):
		# Get command
		command = cmd.split(' ')[0]			
		# Get variable
		variable = ' '.join(cmd.split(' ')[1:])
		# Inspect command to get /title qualifier if present
	        m = re.search('/title=([\w&]+)', command)	# [\w&] = alphanumeric and & (for html entities like &nbsp)
	        if m:
	           title = m.group(1)
	        else:
	           title = variable
		# Append to array
		cmdArray.append({'command': command, 'variable': variable, 'title': title})

#------------------------------------------------------
options = {
    'bind': '%s:%s' % ('127.0.0.1', '8000'),
    'workers': number_of_workers(),
    'worker_class': 'sync',
    'threads': 1 
}
StandaloneApplication(handler_app, options).run()

sys.exit(1)

