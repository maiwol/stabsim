#!/usr/bin/python

import cgi
import cgitb
import circuit_drawer
import os
import json
cgitb.enable()

def typehtml():
	print "Content-type: text/html\n"

def typejson():
	print 'Content-type: application/json\n'	

def params():
	files = [f for f in os.listdir('inputs') if f[0] != '.']
	return json.dumps({'filenames':files})

def main():
	form = cgi.FieldStorage()	

	if form.has_key('param_request'):
		typejson()
		print params()
		return

	typehtml()

	if form.has_key('filename'):
		filename = form.getvalue('filename')
		if filename == 'undefined':
			filename = None
		print circuit_drawer.draw(filename)

main()
