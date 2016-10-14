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
	global tmpdir
        tmpdir = tempfile.mkdtemp()
	print('Temporary directory to remove: ', tmpdir)

	# Start pyferret	
        pyferret.start(journal=False, unmapped=True, quiet=True, verify=False)

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

usage = "%prog [--env=script.jnl]"

version = "%prog 0.9.3"

parser = OptionParser(usage=usage, version=version)

parser.add_option("--env", dest="envScript", default="pyferretWMS.jnl", 
		help="ferret script to set the environment (default=pyferretWMS.jnl). It contains datasets to open, variables definition.")

(options, args) = parser.parse_args()

if len(args) != 0:
        parser.error("wrong number of arguments")
	parser.print_help()

if not os.path.isfile(options.envScript):
	parser.error("Environment script option missing")
	parser.print_help()
	sys.exit(1)

envScript = options.envScript

tmpdir = ''

options = {
    'bind': '%s:%s' % ('127.0.0.1', '8000'),
    'workers': number_of_workers(),
    'worker_class': 'sync',
    'threads': 1 
}
StandaloneApplication(handler_app, options).run()

sys.exit(1)

