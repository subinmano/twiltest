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
import transcribe
import updateresult
import uploadtodb
import testcasedisplay
import createjson

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY

# Declare global variables
cli = os.environ["cli"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
signalwire_space_url = os.environ["signalwire_space_url"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

########################################################### Upload Test Case ###########################################################################
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
 
#############################################################Record Utterances################################################################
#Receive the POST request from Execute Test Case
@app.route('/start', methods=['GET','POST'])
def start():
	# Get testcase details as string
	testcaseid = request.values.get("TestCaseId", None)
	filename = testcaseid + ".json"
	session['currentCount']=0
	currentStepCount=0
	with open(filename) as json_file:
		testCaseJSON = json.load(json_file)
		test_case_id = testCaseJSON["test_case_id"]
		dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
		print(dnis, cli)
		#Twilio API call
		#client = Client(account_sid, auth_token)
		#Signalwire API call
		client = signalwire_client(account_sid, auth_token, signalwire_space_url=signalwire_space_url)
		call = client.calls.create(to=dnis, from_=cli, url=url_for('.record_welcome', test_case_id=[test_case_id], _external=True))
	return ""

# Record Welcome prompt
@app.route("/record_welcome", methods=['GET', 'POST'])
def record_welcome():
	response = VoiceResponse()
	currentTestCaseid=request.values.get("test_case_id", None)
	#response.record(trim="trim-silence", action="/recording?StepNumber=1,TestCaseId=currentTestCaseid", timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	response.record(trim="trim-silence", action=url_for('.recording', StepNumber=1, TestCaseId=[currentTestCaseid], _external=True), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	return str(response)

# Twilio/Signalwire functions for record and TTS
@app.route("/recording", methods=['GET', 'POST'])
def recording():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	testcaseid = request.values.get("TestCaseId", None)
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	Recognized_text = transcribe.goog_speech2text(RecordingUrl)
	if Recognized_text:
		#updateResultToDB(RecordingUrl, RecordingDuration, testCaseID, StepNumber)
		updateresult.updateResultToDB(RecordingUrl, Recognized_text, RecordingDuration, testcaseid, currentStepCount)
	print("testcaseid is " + testcaseid)
	print("Recording URL is => " + RecordingUrl)
	filename = testcaseid + ".json"
	print("CurrentStepCount is " + currentStepCount)
	with open(filename) as json_file:
		testCaseJSON = json.load(json_file)
		currentTestCaseid = testCaseJSON["test_case_id"]
		print ("Test Case ID ==>"+currentTestCaseid)
		action = testCaseJSON["steps"][int(currentStepCount)]["action"]
		print("Action is =>" + action)
		input_type = testCaseJSON["steps"][int(currentStepCount)]["input_type"]
		print("Input Type is =>" + input_type)
		input_value = testCaseJSON["steps"][int(currentStepCount)]["input_value"]
		print("Input Value is =>" + input_value)
		pause = testCaseJSON["steps"][int(currentStepCount)]["pause"]
	if pause!="":
		response.pause(length=int(pause))
		print("I have paused")
	if "Reply" in action:
		if "DTMF" in input_type:
			print("i am at DTMF input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.play(digits=input_value)
			response.record(trim="trim-silence", action=url_for('.recording', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid], _external=True), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
		if "Say" in input_type:
			print("i am at Say input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.say(input_value, voice="alice", language="en-US")
			response.record(trim="trim-silence", action=url_for('.recording', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid], _external=True), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	if "Hangup" in action:
		response.hangup()
	return str(response)

# Receive recordng metadata
@app.route("/recording_stat", methods=['GET', 'POST'])
def recording_stat():
	print("I am at recording callback event")
	req = request.get_json(silent=True, force=True)
	StepNumber = request.values.get("step", None)
	print("StepNumber==>"+str(StepNumber))
	testCaseID = request.values.get("currentTestCaseID", None)
	print("testCaseID==>"+str(testCaseID))
	AccountSid = request.values.get("AccountSid", None)
	CallSid =  request.values.get("CallSid", None)
	RecordingSid = request.values.get("RecordingSid", None)
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingStatus = request.values.get("RecordingStatus", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	RecordingChannels = request.values.get("RecordingChannels", None)
	RecordingStartTime = request.values.get("RecordingStartTime", None)
	RecordingSource	= request.values.get("RecordingSource", None)
	Recognized_text = transcribe.goog_speech2text(RecordingUrl)
	if Recognized_text:
		#updateResultToDB(RecordingUrl, RecordingDuration, testCaseID, StepNumber)
		updateresult.updateResultToDB(RecordingUrl, Recognized_text, testCaseID, StepNumber)
	print("testCaseID==>"+str(testCaseID))
	print ("RecordingUrl==>"+RecordingUrl+"\nRecognizedText==>"+Recognized_text+"\nStep number==>"+str(StepNumber))
	return ""

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
