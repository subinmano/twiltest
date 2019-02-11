#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import io
import pymysql
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import sys
import requests
import json
import urllib
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client
from signalwire.voice_response import VoiceResponse
# Import custom modules
import uploadtodb
import testcasedisplay
import createjson

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY

# Render Homepage to upload test cases
@app.route('/TestCaseUpload')
def load_TestCaseUploadPage():
	return render_template("FileUpload.html")

# Receive Post request to invoke upload test case to db
@app.route('/UploadTestCaseToDB',methods = ['POST'])
def submitFileToDB():
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		uploadtodb.uploadTestCaseToDB(f.filename)
		createjson.createJSONStringForTestCases()
	return testcasedisplay.readTestCasesFromDB()

# Submit POST request
@app.route('/ExecuteTestCase', methods = ['POST'])
def ExecuteTestCaseUpdateResult():
	testcaseid = request.values.get("TestCaseId", None)
	hostname = request.url_root
	print(hostname)
	return redirect(hostname + 'start?TestCaseId='+testcaseid+'', code=307)

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
