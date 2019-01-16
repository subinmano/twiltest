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

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY

# Declare global variables
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

# Render Homepage to upload test cases
@app.route('/TestCaseUpload')
def load_TestCaseUploadPage():
	return render_template("FileUpload.html")

# Receive post request from HTML and call helper functions
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
			action = TestCaseLine[2]
			inputType = TestCaseLine[3]
			inputValue = TestCaseLine[4]
			inputpause = TestCaseLine[5]
			expectedValue = TestCaseLine[6]
			promptDuration = TestCaseLine[7]
			expectedconfidence = TestCaseLine[8]
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"	
			args = (caseID,caseStepID,action,inputType,inputValue,inputpause,expectedValue,promptDuration,expectedconfidence)
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
	fileContent = """<html><title>IVR test case Execution</title><body><table border="1"><tr><th>Test Case ID</th><th>Test Case Step No</th><th>Action</th><th>Input Type</th><th>Input Value</th><th>Pause</th><th>Expected Prompt</th><th>Expected Prompt Duration</th><th>Min Confidence</th><th>Actual Prompt</th><th>Result</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	testcaseid=""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[9])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[11])+'</td><td>'+validateString(r[12])+'</td></tr>'
		testcaseid=r[0]
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase?TestCaseId='+testcaseid+'" method="post" enctype="multipart/form-data"><input type="submit" value="Execute Test Case" name="submit"></form></body></html>'
	return fileContent

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem:
		return ""
	return testCaseItem

#Create Json of Testcase details and insert to table
def createJSONStringForTestCases():
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT testcaseid, action, input_type, input_value, pause_break FROM ivr_test_case_master")
	testCaseid=""
	testCaseStepsCount=""
	testCaseStepsList=[]
	i=0
	for r in cur:
		print("R0==>"+r[0]+"R1==>"+r[1]+"r[2]==>"+r[2]+"r[3]==>"+r[3]+"r[4]==>"+r[4])
		testCaseid=r[0]
		i=i+1
		testCaseStepsList.append(r[1]+"|"+r[2]+"|"+r[3]+"|"+r[4])
	testCaseStepsCount=i
	print("testCaseid==>"+testCaseid)
	print("testCaseStepsCount==>"+str(testCaseStepsCount))
	print(testCaseStepsList)
	jsonTestCaseString='{'+'"test_case_id":"'+testCaseid+'","test_steps":"'+str(testCaseStepsCount)+'","steps":['
	for testCaseStepItem in testCaseStepsList:
		testCaseStepItem=testCaseStepItem.replace('"','')
		splittedTestCaseItem=testCaseStepItem.split("|")
		jsonTestCaseString=jsonTestCaseString+'{"action":"'+splittedTestCaseItem[0]+'","input_type":"'+splittedTestCaseItem[1]+'","input_value":"'+splittedTestCaseItem[2]+'","pause":"'+splittedTestCaseItem[3]+'"},'
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

# Submit POST request
@app.route('/ExecuteTestCase', methods=['GET','POST'])
def ExecuteTestCaseUpdateResult():
	testcaseid = request.values.get("TestCaseId", None)
	hostname = request.url_root
	print(hostname)
	return redirect(hostname + 'start?TestCaseId='+testcaseid+'', code=307)

# Show testcase execution result in HTML page
def ReturnTestCaseHTMLResult(testCaseIDToBePublished):	
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"><col width="180"><col width="380"><col width="280"><tr><th>Test Case ID</th><th>Test Case Step ID</th><th>Action </th><th>Input Type </th><th>Input Value</th><th>Pause </th><th>Expected value</th><th>Prompt Duration</th><th>Actual Prompt</th><th>Confidence</th><th>Status</th><th>Recording URL</th><th>Recording duration</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[0])+'</td><td>'+validateString(r[1])+'</td><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td><td>'+validateString(r[5])+'</td><td>'+validateString(r[6])+'</td><td>'+validateString(r[7])+'</td><td>'+validateString(r[8])+'</td><td>'+validateString(r[12])+'</td><td>'+validateString(r[10])+'</td><td>'+validateString(r[13])+'</td><td>'+validateString(r[14])+'</td></tr>'
		print("R3==>"+r[3])
	cur.close()
	conn.close()
	fileContent = fileContent + '</body></html>'
	return fileContent

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
