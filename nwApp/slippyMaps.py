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
import json

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

        	FILE = fields['FILE']
		try:
        		COMMAND = fields['COMMAND']
		except:
        		COMMAND = None
		try:
        		VARIABLE = fields['VARIABLE'].replace('%2B','+')
		except:
        		VARIABLE = None
		try:
        		PATTERN = fields['PATTERN']
		except:
        		PATTERN = None

        	pyferret.run('use ' + FILE)

                tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
                tmpname = os.path.basename(tmpname)

		#---------------------------------------------------------
		if fields['REQUEST'] == 'GetVariables':
			varnamesdict = pyferret.getstrdata('..varnames')
			variables = varnamesdict['data'].flatten().tolist()

			#print(json.dumps(variables))
			start_response('200 OK', [('content-type', 'application/json')])
			return iter(json.dumps(variables))

		#---------------------------------------------------------
		elif fields['REQUEST'] == 'GetColorBar':
                	pyferret.run('set window/aspect=1/outline=0')
                	pyferret.run('go margins 2 4 3 3')
                	pyferret.run(COMMAND + '/set_up ' + VARIABLE)
                	pyferret.run('ppl shakey 1, 0, 0.15, , 3, 9, 1, `($vp_width)-1`, 1, 1.25 ; ppl shade')
                	pyferret.run('frame/format=PNG/transparent/xpixels=400/file="' + tmpdir + '/key' + tmpname + '"')

                	im = Image.open(tmpdir + '/key' + tmpname)
                	box = (0, 325, 400, 375)
                	area = im.crop(box)
                	area.save(tmpdir + '/' + tmpname, "PNG")

		#---------------------------------------------------------
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

	        	if os.path.isfile(tmpdir + '/' + tmpname):
				if PATTERN:
					img = Image.open(tmpdir + '/' + tmpname)
	        	        	pattern = Image.open(PATTERN)
					img = Image.composite(img, pattern, pattern)
					img.save(tmpdir + '/' + tmpname)
	
		#---------------------------------------------------------
		else:
			raise

		if os.path.isfile(tmpdir + '/' + tmpname):
			ftmp = open(tmpdir + '/' + tmpname, 'rb')
			img = ftmp.read()
			ftmp.close()
			os.remove(tmpdir + '/' + tmpname)

		start_response('200 OK', [('content-type', 'image/png')])		# for GetColorBar and GetMap
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
	
	instance_WMS_Client = Template(template_WMS_client())
	instance_NW_Package = Template(template_nw_package())
	
	with open(tmpdir + '/index.html', 'wb') as f:
		f.write(instance_WMS_Client.render(gunicornPID=master_pid, 
						   mapWidth=mapWidth, mapHeight=mapHeight, 
						   mapCenter=mapCenter, mapZoom=mapZoom, port=port))
	with open(tmpdir + '/package.json', 'wb') as f:
		f.write(instance_NW_Package.render())

	# Copy icon
	path = os.path.dirname(os.path.realpath(__file__))	
	shutil.copy(path + "/icon.png", tmpdir)

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

    <script src='http://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js'></script>

    <link href='http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/css/bootstrap.min.css' rel="stylesheet"/>
    <script src='http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js'></script>

    <script src='http://rawgit.com/gesquive/bootstrap-add-clear/master/bootstrap-add-clear.min.js'></script>

    <link href='http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.min.css' rel="stylesheet"/>
    <script src='http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js'></script>

    <link href='http://cdnjs.cloudflare.com/ajax/libs/leaflet/1.2.0/leaflet.css' rel="stylesheet"/>
    <script src='http://cdnjs.cloudflare.com/ajax/libs/leaflet/1.2.0/leaflet.js'></script>

    <script src='http://cdn.rawgit.com/turban/Leaflet.Sync/master/L.Map.Sync.js'></script>
    
    <style type='text/css'>
        html, body { font-family: 'arial' }
        .mapContainer { display: inline-block ; margin-left: 10px; margin-top: 10px;}
        .title { font-size: 12px; float: left; }
	.map { width: {{ mapWidth }}px; height: {{ mapHeight }}px; }
        .key { text-align: center; margin: auto; }
        .key img { max-width: 400px; max-height: 50px; }		/* colorbar is 400x50 */
	.leaflet-bar a, .leaflet-bar a:hover {
    		height: 16px;
    		line-height: 16px;
    		width: 16px;
	}
	.leaflet-control-zoom-in, .leaflet-control-zoom-out {
    		font-size: 14px;
		text-indent: 0px;
	}
	.close {
		opacity: 0.0;
	}
	.mapContainer:hover > .header > .close {
		opacity: 0.5;
	}
	#dialog {
		display: none;
		font-size: 12px;
	}
	#commandLine {
                width: 100%;
		font-size: 12px;
	}
	#addMap {
                left: 220px;
		position: relative;
		margin-top: 15px;
	}
	.ui-dialog { z-index: 1000 !important; }
	.ui-dialog-title { font-size: 12px !important; }
	.ui-icon-gripsmall-diagonal-se { z-index: 1000 !important; }
   	.ui-icon-closethick { margin-top: 0; }
	.forSelect {
                width: 500px;
                left: 30px;
		position: relative;
	}
	.forSelect label {
                left: -20px;
		position: relative;
		margin-top: 5px;
	}
    </style>
</head>

<body>

<div id="dialog">
	<div id="fileOpen"></div>
	<input id="commandLine" type="text" placeholder="New command">
</div>

<div class="forSelect">
   <label for="file">File to open:</label>
   <input type="text" class="form-control" id="file" list="list_file" type="search"
		placeholder="Enter a dataset"
		value="levitus_climatology"> 
   <datalist id="list_file">
	<option value="levitus_climatology" selected="selected">
	<option value="monthly_navy_winds">
   </datalist>
</div>

<div class="forSelect">
   <label for="command">Command to run:</label>
   <input type="text" class="form-control" id="command" list="list_command" type="search"
		placeholder="Enter a command"
		value="shade/x=-180:180/y=-90:90/lev=10v/pal=mpl_PSU_inferno"> 
   <datalist id="list_command">
	<option value="shade/x=-180:180/y=-90:90/lev=10v/pal=mpl_PSU_inferno" selected="selected">
	<option value="shade/x=-180:180/y=-90:90/lev=10v/pal=mpl_PSU_plasma">
	<option value="shade/x=-180:180/y=-90:90/lev=10v/pal=mpl_PSU_viridis">
	<option value="shade/x=-180:180/y=-90:90/lev=10v/pal=mpl_PSU_magma">
	<option value="shade/x=-180:180/y=-90:90/lev=20/pal=mpl_Div_PRGn">
	<option value="shade/x=-180:180/y=-90:90/lev=20/pal=mpl_Div_RdBu">
	<option value="shade/x=-180:180/y=-90:90/lev=20/pal=default">
   </datalist>
</div>

<div class="forSelect">
   <label for="variable">Variable to display:</label>
   <input type="text" class="form-control" id="variable" list="list_variable" type="search"
		placeholder="Enter a variable"
		value="TEMP[k=1,l=1]"> 
   <datalist id="list_variable">
	<option value="TEMP[k=1,l=1]" selected="selected">
	<option value="SALT[k=1,l=1]">
   </datalist>
</div>

<p>
<button type="button" class="btn btn-default" id="addMap">Insert a map</button>
</p>

<div id="mapSpace"></div>

<script type='text/javascript'>

//===============================================
var crs = L.CRS.EPSG4326;

var Id = 0;
var map = {};			// associative array
var wmspyferret = {};
var frontiers = {};
var width = {{ mapWidth }};
var height = {{ mapHeight }};

var wmsserver = 'http://localhost:{{ port }}';

//===============================================
$("input:text").addClear({                      // https://github.com/gesquive/bootstrap-add-clear
        showOnLoad: true,
        onClear: function() {
                $("#addMap").prop('disabled', true);
        }
});

$("input:text").on('input', function() {
        if ($(this).val().length != 0) {
                $("#addMap").prop('disabled', false);
        }
});

$("#file").on('input', function() {
	$.ajax({
  		dataType: "json",
  		url: wmsserver,
		data: 'SERVICE=WMS' + '&REQUEST=GetVariables' + '&FILE=' + $(this).val(),
		success: function(data) { 
			for (i in data) {
				dataEntry =  data[i] + '[k=1,l=1]';
				optionExists = ($('#list_variable option[value="' + dataEntry + '"]').length > 0);
				if (!optionExists) { $('#list_variable').append('<option value="' + dataEntry + '">'); }
				if (i==0) { $("#variable").val(dataEntry); }				// preselect the 1st variable
			}
		}
	});
});

//===============================================
function syncMaps() {			// do all synchronizations (less efficient than a python itertools.permutations)
	listIds = Object.keys(map);
	//console.log(listIds);
	for (i in listIds) {
		for (j in listIds) {
			if (i != j) {
				map[listIds[i]].sync(map[listIds[j]]);
			}
		}
	}
}

//===============================================
function getTitle(aCommand, aVariable) {
	// Inspect command to get /title qualifier if present
	m = aCommand.match(/title=([\w&]+)/);		// equivalent to search in python
	if (m != null)
		title = m[1]
	else 
		title = aVariable 
	return title
}

//===============================================
$("body").on('click', ".title", function() {		// to get dynamically created divs
	id = $(this).attr('id');
	mapId = id.replace('title','');
        file = wmspyferret[mapId].wmsParams.file;
	$('#fileOpen').text(file);
	$('#commandLine').val($('#'+id).attr('title'));
	$('#commandLine').attr('mapId', mapId);
	$('#dialog').dialog({ title: 'Command of map #'+mapId, modal: false, width: 600, height: 100,
			      position: {my: "left+30 top+30", at: "left", of: this} });
});

//===============================================
$('#commandLine').on('keypress', function(event) {
    if(event.which === 13) {				// Enter key pressed
        file = wmspyferret[mapId].wmsParams.file;
        commandLine = $(this).val().split(' ');
        command = commandLine[0];
        commandLine.shift();
        variable = commandLine.join(' ');       
	mapId = $(this).attr('mapId');
        wmspyferret[mapId].setParams({ command: command, variable: variable.replace('+','%2B') });
	title = getTitle(command, variable);
        $('#title'+mapId).html(title);   
        $('#title'+mapId).attr('title', command + ' ' + variable);
	$('#key'+mapId).children('img').attr('src', wmsserver + '?SERVICE=WMS&REQUEST=GetColorBar' +
							'&FILE=' + file +
							'&COMMAND=' + command +
							'&VARIABLE=' + variable.replace('+','%2B'));
    }
});

//===============================================
$("#addMap").on('click', function() {

	file = $('#file').val();
	optionExists = ($('#list_file option[value="' + file + '"]').length > 0);			// Append only if not existing
	if (!optionExists) { $('#list_file').append('<option value="' + file + '">'); }

	command = $('#command').val();
	optionExists = ($('#list_command option[value="' + command + '"]').length > 0);
	if (!optionExists) { $('#list_command').append('<option value="' + command + '">'); }

	variable = $('#variable').val();
	optionExists = ($('#list_variable option[value="' + variable + '"]').length > 0);
	if (!optionExists) { $('#list_variable').append('<option value="' + variable + '">'); }

	Id++;
	divs = "<div class='mapContainer'>" + 
   			"<div id='mapHeader" + Id + "' class='header'>" +
   			    "<div id='title" + Id + "' class='title'></div>" +
   			    "<div id='close" + Id + "' class='close ui-icon ui-icon-closethick'></div>" +
   			"</div>" +
			"<div id='map" + Id + "' class='map'></div>" + 
   			"<div id='key" + Id + "' class='key'><img /></div>" +
   		"</div>";
	$('#mapSpace').append(divs);
	wmspyferret[Id] = L.tileLayer.wms(wmsserver, {
		file: file,
		command: command,
		variable: variable,
	    	crs: crs,
		format: 'image/png',
		transparent: true,
	    	uppercase: true
	});
	frontiers[Id] = L.tileLayer.wms('http://www.globalcarbonatlas.org:8080/geoserver/GCA/wms', {
		layers: 'GCA:GCA_frontiersCountryAndRegions',
		format: 'image/png',
    		crs: crs,
		transparent: true
	});
	map[Id] = L.map('map'+Id, {
		layers: [wmspyferret[Id], frontiers[Id]],
	    	crs: crs,
		center: {{ mapCenter }},
		zoom: {{ mapZoom }},
	    	attributionControl: false
	});
	$('#map'+Id).resizable();
	$('#map'+Id).width(width);
	$('#map'+Id).height(height);
	title = getTitle(wmspyferret[Id].wmsParams.command, wmspyferret[Id].wmsParams.variable.replace('%2B','+'));
	$('#title'+Id).html(title);
	$('#title'+Id).attr('title', wmspyferret[Id].wmsParams.command + ' ' + wmspyferret[Id].wmsParams.variable.replace('%2B','+'));   
	$('#key'+Id).children('img').css('width', width + 'px');
	$('#key'+Id).children('img').css('height', parseInt(width/8) + 'px');			// according to ratio 400/50 = 8
	$('#key'+Id).children('img').attr('src', wmsserver + '?SERVICE=WMS&REQUEST=GetColorBar' +
							'&FILE=' + wmspyferret[Id].wmsParams.file +
							'&COMMAND=' + wmspyferret[Id].wmsParams.command +
							'&VARIABLE=' + wmspyferret[Id].wmsParams.variable.replace('+','%2B'));
	syncMaps();

});

//===============================================
$("body").on('click', ".close", function(event) {
    closeId = $(this)[0].id;
    selectedId = parseInt(closeId.replace('close',''));
    $('#map'+selectedId).parent().remove();
    delete map[selectedId];
    delete wmspyferret[selectedId];
    delete frontiers[selectedId];
});

//===============================================
$(document).on('resizestop', '.map', function() {
	width = $(this).width();
	height = $(this).height();
	for (mapId = 1; mapId <= Id ; mapId++) {
		$('#map'+mapId).width(width);
		$('#map'+mapId).height(height);
		$('#mapHeader'+mapId).width(width);
		$('#key'+mapId).children('img').css('width', width + 'px');
		$('#key'+mapId).children('img').css('height', parseInt(width/8) + 'px');		// according to ratio 400/50 = 8
	}
});

//===============================================
var exec = require('child_process').exec,child;

process.stdout.write('Starting NW application\\n');

//var zoomPercent = 75;
//var win = require("nw.gui").Window.get();
//win.zoomLevel = Math.log(zoomPercent/100) / Math.log(1.2);

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
          "toolbar": true,
          "width": 1250,
          "height": 800,
	  "icon": "icon.png"
          },
  "chromium-args": "--force-device-scale-factor" 
}
'''

#==============================================================
from optparse import OptionParser

#------------------------------------------------------
usage = "%prog [--port=8000]"

version = "%prog 0.5.0"

#------------------------------------------------------
parser = OptionParser(usage=usage, version=version)

parser.add_option("--width", type="int", dest="width", default=400,
                help="200 < map width <= 600")
parser.add_option("--height", type="int", dest="height", default=400,
                help="200 < map height <= 600")
parser.add_option("--size", type="int", dest="size",
                help="200 < map height and width <= 600")
parser.add_option("--center", type="string", dest="center", default='[0,-40]',
                help="Initial center of maps as [lat, lon] (default=[0,-40])")
parser.add_option("--zoom", type="int", dest="zoom", default=1,
                help="Initial zoom of maps (default=1)")
parser.add_option("--port", type="int", dest="port", default=8000,
		help="Server port number (default=8000)")

(options, args) = parser.parse_args()

if options.size:
        mapHeight = options.size
        mapWidth = options.size
else:
        mapHeight = options.height
        mapWidth = options.width

mapCenter = options.center
mapZoom = options.zoom
port = options.port

#------------------------------------------------------
# Check pyferret, gunicorn....


#------------------------------------------------------
# Global variables
tmpdir = tempfile.mkdtemp()

print('Temporary directory to remove: ', tmpdir)

#------------------------------------------------------
if len(args) != 0:
        parser.error("No argument needed")
	parser.print_help()
        sys.exit(1)

if (mapWidth < 200 or mapWidth > 600) or (mapHeight < 200 or mapHeight > 600):
	parser.error("Map size options incorrect (200 <= size,width,height <= 600)")
        parser.print_help()
        sys.exit(1)

#------------------------------------------------------
options = {
    'bind': '%s:%s' % ('127.0.0.1', port),
    'workers': number_of_workers(),
    'worker_class': 'sync',
    'threads': 1 
}
StandaloneApplication(handler_app, options).run()

sys.exit(1)

