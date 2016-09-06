import os
import tempfile
import pyferret

from paste.request import parse_formvars

pyferret.start(quiet=True, journal=False, unmapped=True)
(errval, errmsg) = pyferret.run('use levitus_climatology')
#pyferret.showdata() 

def app(environ, start_response):

    fields = parse_formvars(environ)
    if environ['REQUEST_METHOD'] == 'GET':

	VARIABLE = fields['VARIABLE']
	CMD = fields['CMD']
	HEIGHT = int(fields['HEIGHT'])
	WIDTH = int(fields['WIDTH'])

	# BBOX=xmin,ymin,xmax,ymax
	bbox = fields['BBOX'].split(',')

	hlim = "/hlim=" + bbox[0] + ":" + bbox[2]
	vlim = "/vlim=" + bbox[1] + ":" + bbox[3]

	try:
        	pyferret.run('set window/outline=5/aspect=1')		# outline=5 is a strange setting but works otherwise get outline around polygons
        	pyferret.run('go margins 0 0 0 0')
		
		#print CMD +  "/x=-180:180/y=-90:90/noaxis/nolab/nokey" + hlim + vlim + " " + VARIABLE
		pyferret.run(CMD +  "/x=-180:180/y=-90:90/noaxis/nolab/nokey" + hlim + vlim + " " + VARIABLE) 

		tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
		pyferret.saveplot(tmpname, xpix=WIDTH, qual='/format=PNG/transparent')			# could be faster if saveplot would allow stringIO (ie buffer)

		if os.path.isfile(tmpname):
			ftmp = open(tmpname, "rb")
			img = ftmp.read()
			ftmp.close()
			os.remove(tmpname)
      
		start_response('200 OK', [('content-type', 'image/png')])
		return iter(img) 

	except:
		return iter("Exception caught")
