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
#import custom modules
import transcribe

#Initiate Flask app
app = Flask(__name__)

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY

# Declare global variables
cli = os.environ["cli"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Receive the POST request
@app.route('/start', methods=['GET','POST'])
def start():
	# Get testcase details as string
	testcaseid = request.values.get("TestCaseId", None)
	filename = testcaseid + ".json"
	with open(filename) as json_file:
		testCaseJSON = json.loads(json_file)
		test_case_id = testCaseJSON["test_case_id"]
		dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
		print(dnis, cli)
		session['currentCount']=0
		currentStepCount=0
		client = Client(account_sid, auth_token)
		call = client.calls.create(to=dnis, from_=cli, url=url_for('.record_welcome', test_case_id=[test_case_id], _external=True))
	return ""

# Record Welcome prompt
@app.route("/record_welcome", methods=['GET', 'POST'])
def record_welcome():
	response = VoiceResponse()
	currentTestCaseid=request.values.get("test_case_id", None)
	response.record(trim="trim-silence", action="/recording?StepNumber=1", timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	return str(response)

# Twilio/Signalwire functions for record and TTS
@app.route("/recording", methods=['GET', 'POST'])
def recording():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	print("CurrentStepCount is " + currentStepCount)
	with open('details.json') as json_file:
		testCaseJSON = json.loads(json_file)
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
			response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
		if "Say" in input_type:
			print("i am at Say input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.say(input_value, voice="alice", language="en-US")
			response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", playBeep="false", recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
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
	#updateResultToDB(RecordingUrl, RecordingDuration, testCaseID, StepNumber)
	updateResultToDB(RecordingUrl, Recognized_text, testCaseID, StepNumber)
	print("testCaseID==>"+str(testCaseID))
	print ("RecordingUrl==>"+RecordingUrl+"\nRecognizedText==>"+Recognized_text+"\nStep number==>"+str(StepNumber))
	return ""

# Update recording metadata to Database
def updateResultToDB(recordingURL,recognizedText,testcaseID,testCaseStep):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	print(str(recordingURL)+"||"+str(recognizedText)+"||"+testcaseID+"||"+testCaseStep)
	query = "UPDATE ivr_test_case_master set recording_url = %s, actual_value = %s where testcaseid=%s and testcasestepid = %s"
	args = (recordingURL,str(recognizedText),str(testcaseID),testCaseStep)
	cur.execute(query,args)
	print("Rows Affected==>"+str(cur.rowcount))
	conn.commit()
	cur.close()	
	conn.close()
	return ""
		
if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
