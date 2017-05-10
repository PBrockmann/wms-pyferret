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

		try:
        		FILE = fields['FILE']
		except:
        		FILE = None
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


		#---------------------------------------------------------
		if fields['REQUEST'] == 'GetVariables':
        		pyferret.run('use ' + FILE)
			varnamesdict = pyferret.getstrdata('..varnames')
			variables = varnamesdict['data'].flatten().tolist()

			#print(json.dumps(variables))
			start_response('200 OK', [('content-type', 'application/javascript')])
			return iter('newVariables(' + json.dumps(variables) + ')')			# return jsonp

		#---------------------------------------------------------
		elif fields['REQUEST'] == 'GetDatasets':
                	tmpname = tempfile.NamedTemporaryFile(suffix='.txt').name
                	tmpname = os.path.basename(tmpname)

            		pyferret.run('set redirect /clobber /file="%s" stdout' % (tmpdir + '/' + tmpname))
			pyferret.run('show data')
			pyferret.run('cancel redirect')

			if os.path.isfile(tmpdir + '/' + tmpname):
				ftmp = open(tmpdir + '/' + tmpname, 'rb')
				txt = ftmp.read()
				ftmp.close()
				#os.remove(tmpdir + '/' + tmpname)

			print(os.getpid())

			start_response('200 OK', [('content-type', 'text/plain')])
			return iter('displayDatasets(' + json.dumps(txt) + ')') 

		#---------------------------------------------------------
		elif fields['REQUEST'] == 'GetColorBar':
        		pyferret.run('use ' + FILE)
                	tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
                	tmpname = os.path.basename(tmpname)

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
        		pyferret.run('use ' + FILE)
                	tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
                	tmpname = os.path.basename(tmpname)

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
	pyferret.start(journal=False, unmapped=True, quiet=True, verify=False, memsize=50)
	
	master_pid = os.getpid()
	print('---------> gunicorn master pid: ', master_pid)
	
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
from optparse import OptionParser

#------------------------------------------------------
usage = "%prog [--port=8000]"

version = "%prog 0.5.0"

#------------------------------------------------------
parser = OptionParser(usage=usage, version=version)

parser.add_option("--port", type="int", dest="port", default=8000,
		help="Server port number (default=8000)")

(options, args) = parser.parse_args()

port = options.port

#------------------------------------------------------
# Global variables
tmpdir = tempfile.mkdtemp()

print('Temporary directory to remove: ', tmpdir)

#------------------------------------------------------
if len(args) != 0:
        parser.error("No argument needed")
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

