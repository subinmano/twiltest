#!/usr/bin/python
# -*- coding: utf-8 -*-
#import python modules
import os
import io
import pymysql
import sys
import requests
import json
import urllib
from jiwer import wer
from difflib import SequenceMatcher
from datetime import datetime
import time
import re

# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client
from signalwire.voice_response import VoiceResponse

# Import Flask Modules
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template, Blueprint, flash
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask import g

# Import custom modules
import transcribe
import updateresult
import param
from models import User
from models import db

auth = Blueprint('auth', __name__)

# Declare Global variables
cli = os.environ["cli"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
signalwire_space_url = os.environ["signalwire_space_url"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]
database_uri = os.environ["database_uri"]

#Set key for session variables
#SECRET_KEY = os.environ["SECRET_KEY"]
#app.secret_key=SECRET_KEY

###############################################################User Management####################################################################
#Render the Login page
@auth.route('/login')
def login():
	return render_template('login.html')
  
#Process user details
@auth.route('/login', methods=['POST'])
def login_post():
	email = request.form.get('email')
	password = request.form.get('password')
	session['username'] = email
	remember = True if request.form.get('remember') else False
	# check if user actually exists , take the user supplied password, hash it, and compare it to the hashed password in database
	user = User.query.filter_by(email=email).first()
	if not user or not check_password_hash(user.password, password):
		flash('Please check your login details and try again.')
		#if user doesn't exist or password is wrong, reload the page
		return redirect(url_for('auth.login'))
	#if the above check passes, then we know the user has right credentials
	login_user(user, remember=remember)
	return redirect(url_for('main.profile'))
  
#Render the signup page
@auth.route('/signup')
def signup():
	return render_template('signup.html')

#Create user with details
@auth.route('/signup', methods=['POST'])
def signup_post():
	email = request.form.get('email')
	name = request.form.get('name')
	password = request.form.get('password')
	# Check if user exists-if this returns a user, then the email already exists in database
	user = User.query.filter_by(email=email).first() 
	# if a user is found, we want to redirect back to signup page so user can try again
	if user: 
		flash('Email address already exists')
		return redirect(url_for('auth.signup'))
	# create new user with the form data. Hash the password so plaintext version isn't saved.
	new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
	# add the new user to the database
	db.session.add(new_user)
	db.session.commit()
	return redirect(url_for('auth.login'))

#logout the user
@auth.route('/logout')
@login_required
def logout():
	logout_user()
	session.pop('username')
	return redirect(url_for('main.index'))

########################################################### Upload Test Case ###########################################################################
# Render Homepage to upload test cases
@auth.route('/TestCaseUpload')
@login_required
def load_TestCaseUploadPage():
	return render_template("FileUpload.html")

# Receive request to upload to db and display - Call functions to upload to DB display on screen
@auth.route('/UploadTestCaseToDB',methods = ['POST'])
@login_required
def submitFileToDB():
	currentUserName = current_user.email
	print("The logged in user is : "+currentUserName)
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		checktestcasetype(f.filename,currentUserName)
	return readTestCasesFromDB()

# Receive post request from HTML and perform actions based on dynamic parameters or static parameters	
def checktestcasetype(uploadedFileName,currentUserName):
	with open(uploadedFileName, "r") as ins:
		TestCaseLine = ins.readline().split(",")
		if TestCaseLine[9] == "Input Dynamic Param":
			param.uploadTestCaseTodynamicDB(uploadedFileName, currentUserName)
			testCases = param.getDistinctTestCaseIdFromDB(currentUserName)
			for eachTestCase in testCases:
				paramListString=param.formSingleParamString(eachTestCase)
				jsonParamObj=param.formJsonObjForAllParam(paramListString)
				print("maxParamLength::"+str(jsonParamObj['dynamicParamLength']))
				param.ExpandAndUpdateDynamicTestCase(jsonParamObj,jsonParamObj['dynamicParamLength'],eachTestCase,currentUserName)
				print('paramListString::'+paramListString)
		else:
			uploadTestCaseToDB(uploadedFileName,currentUserName)
	return ""

# Upload static test case information to Database
def uploadTestCaseToDB(uploadedFileName,currentUserName):
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
			print ("Current User name::"+currentUserName);
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence, uploaded_date,username) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			args = (caseID,caseStepID,actionType,inputType,inputValue,inputPause,expectedValue,promptDuration,expectedConfidence,uploadDatetime,currentUserName)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""

#Get test case details from Database and display in HTML page
@auth.route('/ReadTestCase')
@login_required
def readTestCasesFromDB():
	currentUserName = current_user.email
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master where username = '"+currentUserName+"'")
	fileContent = """<html><title>IVR test case Execution</title><body bgcolor="#42f5d7"><table border="1"><tr><th>Testcase ID</th><th>Step No</th><th>Action</th><th>Input Type</th><th>Input Value</th><th>Pause</th><th>Expected Prompt</th><th>Expected Prompt Duration</th><th>Min Confidence</th><th>Actual Prompt</th><th>Result</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[9])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[11])+'</td><td>'+validateString(r[12])+'</td></tr>'
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data"><input type="submit" value="Execute Test Case" name="submit"></form>''<form action="/ShowTestResult" method="post" enctype="multipart/form-data"><input type="submit" value="Show Test Result" name="submit"></form></body></html>'
	return fileContent

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem:
		return ""
	return testCaseItem

#Create json of the testcase and call make call
@auth.route('/ExecuteTestCase', methods = ['POST'])
@login_required
def ExecuteTestCase():
	currentUserName = current_user.email
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT distinct(testcaseid) FROM ivr_test_case_master where username = '"+currentUserName+"'")
	listOfTestCases=[]
	for r in cur:
		listOfTestCases.append(r[0])
	print(listOfTestCases)
	print("Length of the List1==>"+str(len(listOfTestCases)))
	i=0
	for i in range(0,len(listOfTestCases)):
		if i==len(listOfTestCases)-1:
			print("Current::"+listOfTestCases[i]+"Next::"+"End")
			createJSONStringForTestCases(listOfTestCases[i],'none',currentUserName)
		else:
			print("Current::"+listOfTestCases[i]+"Next::"+listOfTestCases[i+1])
			createJSONStringForTestCases(listOfTestCases[i],listOfTestCases[i+1],currentUserName)
	makecallfortestcase(listOfTestCases[0],currentUserName)
	return redirect(url_for('main.profile'))

#Create Json of Testcase details and insert to table
def createJSONStringForTestCases(currenttestcaseid,nexttestcaseid,currentUserName):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT testcaseid, action, input_type, input_value, pause_break, expected_value, expected_prompt_duration,username FROM ivr_test_case_master where testcaseid=%s and username=%s"
	args = (str(currenttestcaseid),currentUserName)
	cur.execute(query,args)
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"R2==>"+r[2]+"R3==>"+r[3]+"R4==>"+r[4]+"R5==>"+r[5]+"R6==>"+r[6]+"R7==>"+r[7])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3]+"|"+r[4]+"|"+r[5]+"|"+r[6]+"|"+r[7])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'", "next_test_case_id":"'+nexttestcaseid+'", "test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[0]+'","input_type":"'+splittedTestCaseItem[1]+'","input_value":"'+splittedTestCaseItem[2]+'","pause":"'+splittedTestCaseItem[3]+'","expected_value":"'+splittedTestCaseItem[4]+'","prompt_duration":"'+splittedTestCaseItem[5]+'","user_name":"'+splittedTestCaseItem[6]+'"},'
	jsonTestCaseString=jsonTestCaseString[:-1]
	jsonTestCaseString=jsonTestCaseString+']}'
	query = "INSERT INTO ivr_test_case_json(testcaseid,test_case_json,username) values (%s,%s,%s)"
	args = (testCaseid,jsonTestCaseString,currentUserName)
	cur.execute(query,args)
	conn.commit()
	cur.close()
	conn.close()
	filename = testCaseid + currentUserName + ".json"
	f = open(filename, "w")
	f.write(jsonTestCaseString)
	return()

# Show testcase execution result in HTML page
@auth.route('/ShowTestResult', methods=['GET','POST'])
@login_required
def ShowTestResult():
	currentUserName = current_user.email
	testcaseid = request.values.get("TestCaseId", None)
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT * FROM ivr_test_case_master where testcaseid=%s and username=%s"
	args = (str(testcaseid),currentUserName)
	cur.execute(query,args)
	fileContent = """<html><title>IVR test case Execution Result</title><body bgcolor="#42f5d7"><body><table border="1"><tr><th>Testcase ID</th><th>Step No</th><th>Action</th><th>Input Type</th><th>Input Value</th><th>Pause</th><th>Expected Prompt</th><th>Expected Prompt Duration</th><th>Min Confidence</th><th>Actual Prompt</th><th>Result</th><th>Recording URL</th><th>Recording duration</th><th>Uploaded date</th><th>Execution status</th><th>Execution date</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[9])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[11])+'</td><td>'+validateString(r[12])+'</td><td>'+validateString(r[13])+'</td><td>'+validateString(r[14])+'</td><td>'+validateString(r[15])+'</td></tr>'
		print("R3==>"+r[3])
	cur.close()
	conn.close()
	fileContent = fileContent + '</body></html>'
	return fileContent

#############################################################Telephony activities################################################################
#Receive the POST request from Execute Test Case
#@auth.route('/start', methods=['GET','POST'])
def makecallfortestcase(testcaseid,username):
	#Initialize currentStepCount for keeping track of the test steps
	currentStepCount=0
	# If reading from file - Get filename
	filename = testcaseid + username + ".json"
	with open(filename) as json_file:
		testCaseJSON = json.load(json_file)
		test_case_id = testCaseJSON["test_case_id"]
		dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
		max_rec_length = testCaseJSON["steps"][currentStepCount]["prompt_duration"]
	'''
	# If reading from db
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT test_case_json FROM ivr_test_case_json where testcaseid=%s and username=%s"
	args = (str(testcaseid),username)
	cur.execute(query,args)
	for r in cur:
		testCaseJSON = json.load(r[0])
		test_case_id = testCaseJSON["test_case_id"]
		dnis = testCaseJSON["steps"][currentStepCount]["input_value"]
		max_rec_length = testCaseJSON["steps"][currentStepCount]["prompt_duration"]
	'''
	if max_rec_length!="":
		max_rec_length = int(max_rec_length) + 5
	else:
		max_rec_length = 600	
	
	# Print the values we need to make the call
	print("Values for the call are::")
	print(dnis, cli, test_case_id, max_rec_length)
		
	#Initiate Twilio client
	#client = Client(account_sid, auth_token)
	
	#Initiate Signalwire client
	client = signalwire_client(account_sid, auth_token, signalwire_space_url=signalwire_space_url)
	
	#Initiate the call
	call = client.calls.create(to=dnis, from_=cli,Record=true,url=url_for('.record_welcome', test_case_id=[test_case_id], prompt_duration=[max_length],user_name=[username]),_external=True)
	return()

# Record Welcome prompt
@auth.route("/record_welcome", methods=['GET', 'POST'])
def record_welcome():
	response = VoiceResponse()
	currentTestCaseid=request.values.get("test_case_id", None)
	prompt_duration=request.values.get("prompt_duration", '')
	username=request.values.get("user_name", '')
	response.record(trim="trim-silence", action=url_for('.recording', StepNumber=1, TestCaseId=[currentTestCaseid], user_name=[username],_external=True), timeout="3", playBeep="false", maxLength=prompt_duration, recordingStatusCallback=url_for('.recording_stat', step=[1], currentTestCaseID=[currentTestCaseid], _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	return str(response)

# Twilio/Signalwire functions for record and TTS
@auth.route("/recording", methods=['GET', 'POST'])
def recording():
	response = VoiceResponse()
	currentStepCount= request.values.get("StepNumber", None)
	testcaseid = request.values.get("TestCaseId", None)
	print("testcaseid is " +testcaseid)
	username=request.values.get("user_name", '')
	print("Username is " +username)
	
	#Only for Signalwire... Not for Twilio
	RecordingUrl = request.values.get("RecordingUrl", None)
	RecordingDuration = request.values.get("RecordingDuration", None)
	print("Recording URL is => " + RecordingUrl)
	Recognized_text = transcribe.goog_speech2text(RecordingUrl)
	if Recognized_text:
		updateresult.updateResultToDB(RecordingUrl, Recognized_text, RecordingDuration, testcaseid, currentStepCount, username)
		
	#Get values from json file
	
	#If reading from file
	filename = testcaseid + username + ".json"
	print("CurrentStepCount is " + currentStepCount)
	with open(filename) as json_file:
		testCaseJSON = json.load(json_file)
		currentTestCaseid = testCaseJSON["test_case_id"]
		print ("Test Case ID ==>"+currentTestCaseid)
		nextTestCaseid = testCaseJSON["next_test_case_id"]
		print ("Next Test Case ID ==>"+nextTestCaseid)
		action = testCaseJSON["steps"][int(currentStepCount)]["action"]
		print("Action is =>" + action)
		input_type = testCaseJSON["steps"][int(currentStepCount)]["input_type"]
		print("Input Type is =>" + input_type)
		input_value = testCaseJSON["steps"][int(currentStepCount)]["input_value"]
		print("Input Value is =>" + input_value)
		pause = testCaseJSON["steps"][int(currentStepCount)]["pause"]
		print("Input Value is =>" + pause)
		max_rec_length = testCaseJSON["steps"][int(currentStepCount)]["prompt_duration"]
		print("Recording Length =>" + max_rec_length)
	'''
	#If reading from db
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT test_case_json FROM ivr_test_case_json where testcaseid=%s and username=%s"
	args = (str(testcaseid),username)
	cur.execute(query,args)
	for r in cur:
		testCaseJSON = json.load(r[0])
		currentTestCaseid = testCaseJSON["test_case_id"]
		print ("Test Case ID ==>"+currentTestCaseid)
		nextTestCaseid = testCaseJSON["next_test_case_id"]
		print ("Next Test Case ID ==>"+nextTestCaseid)
		action = testCaseJSON["steps"][int(currentStepCount)]["action"]
		print("Action is =>" + action)
		input_type = testCaseJSON["steps"][int(currentStepCount)]["input_type"]
		print("Input Type is =>" + input_type)
		input_value = testCaseJSON["steps"][int(currentStepCount)]["input_value"]
		print("Input Value is =>" + input_value)
		pause = testCaseJSON["steps"][int(currentStepCount)]["pause"]
		print("Input Value is =>" + pause)
		max_rec_length = testCaseJSON["steps"][int(currentStepCount)]["prompt_duration"]
		print("Recording Length =>" + max_rec_length)
	'''	
	#Check for pause or break needed
	if pause!="":
		response.pause(length=int(pause))
		print("I have paused")
	
	#Set maximum length of recording if prompt duration is mentioned or else set maximum length as 600 seconds
	if max_rec_length!="":
		max_rec_length = int(max_rec_length) + 5
	else:
		max_rec_length = 600
			
	if "Reply" in action:
		if "DTMF" in input_type:
			currentStepCount=int(currentStepCount)+1
			print("I am at DTMF input step:: " +currentStepCount)
			response.play(digits=input_value)
			response.record(trim="trim-silence", action=url_for('.recording', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid],user_name=username,_external=True), timeout="3", playBeep="false", maxLength=max_length, recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], user_name=username, _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
			
		if "Say" in input_type:
			currentStepCount=int(currentStepCount)+1
			print("I am at Say input step:: " +currentStepCount)
			response.say(input_value, voice="alice", language="en-US")
			response.record(trim="trim-silence", action=url_for('.recording', StepNumber=[str(currentStepCount)], TestCaseId=[currentTestCaseid],user_name=username,_external=True), timeout="3", playBeep="false", maxLength=max_length, recordingStatusCallback=url_for('.recording_stat', step=[str(currentStepCount)], currentTestCaseID=[currentTestCaseid], user_name=username, _scheme='https', _external=True),recordingStatusCallbackMethod="POST")
	
	if "Hangup" in action:
		print ("I am at hangup")
		print ("Testcaseid is " + currentTestCaseid)
		print("Username is " +username)
		response.hangup()
		print ("I am after hangup")
		execution_status = "completed"
		execution_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		query = "UPDATE ivr_test_case_master set execution_status = %s, execution_datetime = %s where testcaseid = %s and username =%s and action = %s"
		args = (str(execution_status), str(execution_datetime), currentTestCaseid, username,'Hangup')
		cur.execute(query,args)
		if nextTestCaseid!="none":
			makecallfortestcase(nextTestCaseid,username)
	return str(response)

# Receive recording metadata-- Only applicable for Twilio
@auth.route("/recording_stat", methods=['GET', 'POST'])
def recording_stat():
	print("I am at recording callback event")
	req = request.get_json(silent=True, force=True)
	StepNumber = request.values.get("step", None)
	print("StepNumber==>"+str(StepNumber))
	testCaseID = request.values.get("currentTestCaseID", None)
	print("testCaseID==>"+str(testCaseID))
	username = request.values.get("user_name", None)
	print("Username==>"+username)
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
		updateresult.updateResultToDB(RecordingUrl, Recognized_text, testCaseID, StepNumber,username)
	print("testCaseID==>"+str(testCaseID))
	
	print ("RecordingUrl==>"+RecordingUrl+"\nRecognizedText==>"+Recognized_text+"\nStep number==>"+str(StepNumber)+"\nUser name==>"+username)
	return()

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	
	#Initialize app
	app = Flask(__name__)

	app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
	app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

	db.init_app(app)

	login_manager = LoginManager()
	login_manager.login_view = 'auth.login'
	login_manager.init_app(app)

	@login_manager.user_loader
	def load_user(user_id):
		#since the user_id is just the primary key of our user table, use it in the query for the user
		return User.query.get(int(user_id))

	# blueprint for auth routes in the app
	from auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint)

	# blueprint for non-auth parts of the app
	from main import main as main_blueprint
	app.register_blueprint(main_blueprint)
	
	app.run(debug=False, port=port, host='0.0.0.0')
