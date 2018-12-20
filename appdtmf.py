#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import pymysql
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import sys
import requests
import json
# Twilio Helper Library
#from twilio.rest import Client
#from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client
from signalwire.voice_response import VoiceResponse

# Declare global variables
#asr_lang = os.environ["asr_lang"]
#cli = os.environ["cli"]

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ.get("SECRET_KEY", default=None)
print("SECRET_KEY==>"+SECRET_KEY)
app.secret_key=SECRET_KEY

# Declare global variables
cli = os.environ["cli"]
dnis = os.environ["dnis"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

#Homepage
@app.route('/TestCaseUpload')
def load_TestCaseUploadPage():
	print("I am here")
	return render_template("FileUpload.html")

# Invoking Uploading testcases to database method from HTML page
@app.route('/UploadTestCaseToDB',methods = ['POST'])
def submitFileToDB():
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		uploadTestCaseToDB(f.filename)
	return readTestCasesFromDB()

# Return status of upload to database in HTML page
def readUploadedTestCaseFile(uploadedFileName):
	with open(uploadedFileName, "r") as ins:
		fileArray = []
		fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"> <col width="180">
  		<col width="380"><col width="280"><tr> <th>Input value </th> <th>Expected value</th><th>Outcome</th></tr>"""
		for line in ins:
			splittedTestCaseLine = line.split(",")
			fileArray.append(line)
			fileContent =  fileContent + '<tr><td>'+splittedTestCaseLine[0]+'</td><td>'+splittedTestCaseLine[1]+'</td></tr>'
		fileContent =  fileContent + '</body></html>'
		return fileContent
	
# Upload test case details to Database
def uploadTestCaseToDB(uploadedFileName):
	with open(uploadedFileName, "r") as ins:
		print(databasehost, databaseusername, databasepassword, databasename)
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		i=0
		for line in ins:
			splittedTestCaseLine = line.split(",")
			caseID =splittedTestCaseLine[0]
			caseStepID = splittedTestCaseLine[1]
			action=splittedTestCaseLine[2]
			inputValue = splittedTestCaseLine[3]
			expectedValue = splittedTestCaseLine[4]
			actualValue = splittedTestCaseLine[5]
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_value,expected_value,actual_value) values (%s,%s,%s,%s,%s,%s)"	
			args = (caseID,caseStepID,action,inputValue,expectedValue,actualValue)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem: 
		return " "
	return testCaseItem

#Get test case details from Database
def readTestCasesFromDB():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"> <col width="180"><col width="380"><col width="280"><tr><th>Action </th> <th>Input value </th> <th>Expected value</th><th>Outcome</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td></tr>'
		#print("r[1]|"+validateString(r[1])+"r[2]|"+validateString(r[2])+"r[3]|"+validateString(r[3])+"r[4]|"+validateString(r[4])+"r[5]|"+validateString(r[5])+"r[6]|"+validateString(r[6])+"r[7]|"+validateString(r[7])+"r[8]|"+validateString(r[8])+"r[9]|"+validateString(r[9]))
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data">	<input type="submit" value="Execute Test cases" name="submit"></form></body></html>'
	return fileContent

# Submit POST request 
@app.route('/ExecuteTestCase',methods = ['POST'])
def ExecuteTestCaseUpdateResult():
	i=0
	jsonStringForTestCase=getJSONStringForTestCases()
	session['TestCaseString']=jsonStringForTestCase
	print("jsonStringForTestCase==>"+jsonStringForTestCase)
	#request.args["TestCaseToBeExecuted"]=jsonStringForTestCase
	hostname = request.url_root
	print(hostname)
	return redirect(hostname + 'start', code=307)

# Read test case data from database
def getJSONStringForTestCases():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"r[2]==>"+r[2]+"r[3]==>"+r[3])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'","test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[1]+'","input":"'+splittedTestCaseItem[2]+'"},'
	jsonTestCaseString=jsonTestCaseString[:-1]
	jsonTestCaseString=jsonTestCaseString+']}'
	return jsonTestCaseString

# Show testcase execution result in HTML page
def ReturnTestCaseHTMLResult(testCaseIDToBePublished):	
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"> <col width="180"><col width="380"><col width="280"><tr> <th>Input value </th> <th>Expected value</th><th>Outcome</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+r[2]+'</td><td>'+r[3]+'</td><td>'+r[4]+'</td></tr>'
		print("R3==>"+r[3])
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data"> <input type="submit" value="Execute Test cases" name="submit"></form></body></html>'
	return fileContent

############################################################Twilio recording code######################################################################################

#Receive the POST request
@app.route('/start', methods=['GET','POST'])
def start():
	#Get testcase details as string
	session['testCaseObject'] = getJSONStringForTestCases()
	print ("session['TestCaseString']==>"+session['TestCaseString'])
	session['currentCount']=0
	currentCount=0
	testCaseObject = session['testCaseObject']
	testCaseJSON = json.loads(testCaseObject)
	action="place_call"
	first_action = "place_call"
	if "place_call" in first_action:
		print(dnis, cli)
		#dnis = testCaseJSON["steps"][currentCount][input]
		# Twilio/Signalwire Account Sid and Auth Token
		account_sid = os.environ["account_sid"]
		auth_token = os.environ["auth_token"]
		signalwire_space_url = os.environ["signalwire_space_url"]
		#client = Client(account_sid, auth_token)
		client = signalwire_client(account_sid, auth_token, signalwire_space_url=signalwire_space_url)
		session['currentCount']=1
		print("URL==>" + url_for('.recording', StepNumber=['0'], _external=True))
		call = client.calls.create(to=dnis, from_=cli, url=url_for('.recording', StepNumber=['0'], _external=True))
	else:
		print ("test case is not valid")
	return ""

# Twilio functions for record and TTS
@app.route("/recording", methods=['GET', 'POST'])
def recording():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	print("CurrentStepCount is " + currentStepCount)
	testCaseObject = getJSONStringForTestCases()
	print ("testCaseObject==>"+currentStepCount)
	testCaseJSON = json.loads(testCaseObject)
	print ("test_case_id==>"+testCaseJSON["test_case_id"])
	action = testCaseJSON["steps"][int(currentStepCount)]["action"]
	print("Action is =>" + action)
	inputMsg = testCaseJSON["steps"][int(currentStepCount)]["input"]
	print("currentStepCount==>"+str(currentStepCount)+"")
	if "place_call" in action:
		print("i am at first step")
		currentStepCount=int(currentStepCount)+1
		session['currentCount']=str(currentStepCount)
		response.pause(length=9)
		print("i have paused", inputMsg)
		response.play('', digits=inputMsg)
		response.pause(length=1)
		response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", recordingStatusCallback="/recording_stat?Step="+str(currentStepCount)+"&currentTestCaseID="+testCaseJSON["test_case_id"])
	if "DTMF" in action:
		print("i am at DTMF step")
		currentStepCount=int(currentStepCount)+1
		session['currentCount']=str(currentStepCount)
		#response.say(inputMsg)
		response.play('', digits=inputMsg)
		#response.pause(length=1)
		response.record(trim="trim-silence", action="/recording?StepNumber="+str(currentStepCount), timeout="3", recordingStatusCallback="/recording_stat?Step="+str(currentStepCount)+"&currentTestCaseID="+testCaseJSON["test_case_id"])
	if "Hangup" in action:
		response.hangup()
	return str(response)

# Receive recordng metadata
@app.route('/recording_stat', methods=['POST'])
def recording_stat():
	req = request.get_json(silent=True, force=True)
	AccountSid = request.values.get("AccountSid", None)
	CallSid =  request.values.get("CallSid", None)
	RecordingSid = request.values.get("RecordingSid", None)
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingStatus = request.values.get("RecordingStatus", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	RecordingChannels = request.values.get("RecordingChannels", None)
	RecordingStartTime = request.values.get("RecordingStartTime", None)
	RecordingSource	= request.values.get("RecordingSource", None)
	StepNumber = request.values.get("Step", None)
	testCaseID = request.values.get("currentTestCaseID", None)
	updateResultToDB(RecordingUrl, RecordingDuration, testCaseID, StepNumber)
	print("testCaseID==>"+str(testCaseID))
	print ("RecordingSid==>"+RecordingSid+"\nRecordingUrl==>"+RecordingUrl+"\nRecordingDuration==>"+RecordingDuration+"\nStep number==>"+str(StepNumber))
	return ""

# Update recording metadata to Database
def updateResultToDB(recordingURL,recordingDuration,testcaseID,testCaseStep):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	print(str(recordingURL)+"||"+str(recordingDuration)+"||"+testcaseID+"||"+testCaseStep)
	query = "UPDATE  ivr_test_case_master set recording_url = %s, recording_duration = %s where testcaseid=%s and testcasestepid = %s"
	args = (recordingURL,str(recordingDuration),str(testcaseID),testCaseStep)
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
