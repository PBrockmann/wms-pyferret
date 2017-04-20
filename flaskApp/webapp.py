#!/usr/bin/env python

from __future__ import print_function
from flask import Flask, render_template, request, Response
import os, subprocess

#==============================================================
app = Flask(__name__)

serverProcess = 0

#--------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#--------------------------------------------------------------
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#--------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

#--------------------------------------------------------------
@app.route('/maps')
def maps():
    return render_template('maps.html', port='8001')

#--------------------------------------------------------------
@app.route('/pyferretWMS_toggle', methods=['GET'])
def pyferretWMS_toggle():
    global serverProcess

    toStart = request.args['toStart'] == 'true'			# to cast 'true'/'false' to python
    print(toStart)
    if toStart:
    	print("start pyferretWMS_server")
    	cmd = ["./pyferretWMS_server.py", "--port=8001"]
    	serverProcess = subprocess.Popen(cmd)
    	print(serverProcess.pid)
    else:
    	print("stop pyferretWMS_server")
    	serverProcess.kill()

    return Response(iter(''), status=204)

#--------------------------------------------------------------
@app.route('/help')
def help():
    return render_template('help.html')

#--------------------------------------------------------------
@app.route('/contact')
def contact():
    return render_template('contact.html')

#==============================================================
if __name__ == "__main__":
    app.run(host='localhost', port=5000)
