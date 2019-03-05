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
from jiwer import wer
from difflib import SequenceMatcher
from datetime import datetime
import time
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client
from signalwire.voice_response import VoiceResponse

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

# Receive request to upload to db and display - Call functions to upload to DB display on screen
@app.route('/UploadTestCaseToDB',methods = ['POST'])
def submitFileToDB():
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		uploadTestCaseToDB(f.filename)
		createJSONStringForTestCases()
	return readTestCasesFromDB()

# Upload test case information to Database
def uploadTestCaseToDB(uploadedFileName):
	with open(uploadedFileName, "r") as ins:
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		i=0
		for line in ins:
			TestCaseLine = line.split(",")
			caseID = TestCaseLine[0]
			caseStepID = TestCaseLine[1]
			actionType = TestCaseLine[2]
			inputType = TestCaseLine[3]
			inputValue = TestCaseLine[4]
			inputPause = TestCaseLine[5]
			expectedValue = TestCaseLine[6]
			promptDuration = TestCaseLine[7]
			expectedConfidence = TestCaseLine[8]
			uploadDatetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence, uploaded_date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			args = (caseID,caseStepID,actionType,inputType,inputValue,inputPause,expectedValue,promptDuration,expectedConfidence,uploadDatetime)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""

#Get test case details from Database and display in HTML page
def readTestCasesFromDB():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution</title><body><table border="1"><tr><th>Testcase ID</th><th>Step No</th><th>Action</th><th>Input Type</th><th>Input Value</th><th>Pause</th><th>Expected Prompt</th><th>Expected Prompt Duration</th><th>Min Confidence</th><th>Actual Prompt</th><th>Result</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	testcaseid=""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[9])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[11])+'</td><td>'+validateString(r[12])+'</td></tr>'
		testcaseid=r[0]
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase?TestCaseId='+testcaseid+'" method="post" enctype="multipart/form-data"><input type="text" name="numberofcalls" value="Number of calls"><input type="submit" value="Execute Test Case" name="submit"></form>'</form></body></html>'
	return fileContent

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem:
		return ""
	return testCaseItem

#Intitate create calls for testcase
@app.route('/ExecuteTestCase', methods = ['POST'])
def ExecuteTestCase():
	testcaseid = request.values.get("TestCaseId", None)
	numberofCalls = request.form['numberofcalls']
	for count in range(numberofCalls):
		#makecallfortestcase(testcaseid)
		print('Testcase ID: ' +testcaseid)
		print('Creating call: #', count+1, end='\r')
		print('Creating call: Completed')
	return ""

#Create Json of Testcase details and insert to table
def createJSONStringForTestCases():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT testcaseid, action, input_type, input_value, pause_break, expected_prompt_duration FROM ivr_test_case_master")
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"R2==>"+r[2]+"R3==>"+r[3]+"R4==>"+r[4]+"R5==>"+r[5])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3]+"|"+r[4]+"|"+r[5])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'", "test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[0]+'","input_type":"'+splittedTestCaseItem[1]+'","input_value":"'+splittedTestCaseItem[2]+'","pause":"'+splittedTestCaseItem[3]+'","prompt_duration":"'+splittedTestCaseItem[4]+'"},'
	jsonTestCaseString=jsonTestCaseString[:-1]
	jsonTestCaseString=jsonTestCaseString+']}'
	query = "INSERT INTO ivr_test_case_json(test_case_id, test_case_json) values (%s,%s)"
	args = (testCaseid,jsonTestCaseString)
	cur.execute(query,args)
	conn.commit()
	cur.close()
	conn.close()
	filename = testCaseid + ".json"
	f = open(filename, "w")
	f.write(jsonTestCaseString)
	return ""

#############################################################Record Utterances################################################################
#Receive the POST request from Execute Test Case
#@app.route('/start', methods=['GET','POST'])
def makecallfortestcase(testcaseid):
	# Get testcase details as string
	filename = testcaseid + ".json"
	session['currentCount']=0
	currentStepCount=0
	with open(filename) as json_file:
		testCaseJSON = json.load(json_file)
		test_case_id = testCaseJSON["test_case_id"]
		dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
	print(dnis, cli, test_case_id, max_length)
	#Twilio API call
	#client = Client(account_sid, auth_token)
	#Signalwire API call
	client = signalwire_client(account_sid, auth_token, signalwire_space_url=signalwire_space_url)
	call = client.calls.create(to=dnis, from_=cli, url=url_for('.input_action', StepNumber=1, test_case_id=[test_case_id], prompt_duration=[max_length], _external=True))
	return ""

# Twilio/Signalwire functions for record and TTS
@app.route("/input_action", methods=['GET', 'POST'])
def input_action():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	print("CurrentStepCount is " + currentStepCount)
	testcaseid = request.values.get("TestCaseId", None)
	print("testcaseid is " +testcaseid)
	Callid =  request.values.get("sid", None)
	CallStatus = request.values.get("status", None)
		
	#Get values from json file
	filename = testcaseid + ".json"
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
		print("Input Value is =>" + pause)
	
	#Check for pause or break needed
	if pause!="":
		response.pause(length=int(pause))
		print("I have paused")
	
	if "Reply" in action:
		if "DTMF" in input_type:
			print("i am at DTMF input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.play(digits=input_value)
			response.redirect(url_for('.input_action', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid], _external=True))
			
		if "Say" in input_type:
			print("i am at Say input step")
			currentStepCount=int(currentStepCount)+1
			session['currentCount']=str(currentStepCount)
			response.say(input_value, voice="alice", language="en-US")
			response.redirect(url_for('.input_action', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid], _external=True))
	
	if "Hangup" in action:
		print ("I am at hangup")
		print ("Testcaseid is " + currentTestCaseid)
		response.hangup()
		print ("I am after hangup")
		execution_status = "completed"
		execution_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		query = "INSERT INTO ivr_load_test_case_master set call_id = %s, call_status = %s, execution_datetime = %s where testcaseid = %s"
		args = (str(Callid), str(CallStatus), str(execution_status), str(execution_datetime))
		cur.execute(query,args)
	return str(response)

# Show testcase execution result in HTML page
@app.route('/ShowTestResult', methods=['GET','POST'])
def ShowTestResult():
	response = VoiceResponse()
	testcaseid = request.values.get("TestCaseId", None)
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT * FROM ivr_load_test_case_master where testcaseid=%s"
	args = (str(testcaseid))
	cur.execute(query,args)
	fileContent = """<html><title>IVR load test Execution Result</title><body><table border="1"><tr><th>Call ID</th><th>Call Status</th><th>Execution Status</th><th>Execution Date</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td></tr>'
	cur.close()
	conn.close()
	fileContent = fileContent + '</body></html>'
	return fileContent

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
	
