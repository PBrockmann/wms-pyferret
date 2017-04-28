#!/usr/bin/env python

from __future__ import print_function
from flask import Flask, render_template, request, Response, session
import os, subprocess
import datetime

#==============================================================
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'

serverProcess = None 

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
@app.route('/pyferretWMS_status', methods=['GET'])
def pyferretWMS_status():
    if serverProcess :
	serverStatus = 'on'
    else:
	serverStatus = 'off'
    return serverStatus

#--------------------------------------------------------------
@app.route('/pyferretWMS_toggle', methods=['GET'])
def pyferretWMS_toggle():
    global serverProcess

    cmd = request.args['cmd']

    if cmd == 'on' and not serverProcess:
    	print("start pyferretWMS_server")
    	cmd = ["./pyferretWMS_server.py", "--port=8001"]
    	serverProcess = subprocess.Popen(cmd)
    	print(serverProcess.pid)

    if cmd == 'off' and serverProcess:
    	print("stop pyferretWMS_server")
    	serverProcess.kill()
	serverProcess = None

    return Response(iter(''), status=204)

#--------------------------------------------------------------
@app.route('/logout')
def logout():
    global serverProcess	
	
    print("logout")
    if serverProcess:
    	print("stop pyferretWMS_server")
    	serverProcess.kill()
	serverProcess = None 

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
