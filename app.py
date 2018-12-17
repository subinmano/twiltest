#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import pymysql
from flask import Flask, render_template,request,session,redirect

app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ.get("SECRET_KEY", default=None)
print("SECRET_KEY==>"+SECRET_KEY)
app.secret_key=SECRET_KEY

@app.route('/TestCaseUpload')
def load_TestCaseUploadPage():
	return render_template("FileUpload.html")

@app.route('/RedirectTest',methods = ['POST','GET'])
def RedirectedPage():
	print("This is a redirect test")
	return "This is redirect Test"

@app.route('/UploadTestCaseToDB',methods = ['POST'])
def submitFileToDB():
	if request.method == 'POST':
		f = request.files['fileToUpload']
		f.save(f.filename)
		uploadTestCaseToDB(f.filename)
		#return readUploadedTestCaseFile(f.filename)
	return readTestCasesFromDB()

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

def uploadTestCaseToDB(uploadedFileName):
	with open(uploadedFileName, "r") as ins:
		conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
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
			query = "INSERT INTO  ivr_test_case_master(testcaseid,testcasestepid,action,input_value,expected_value,actual_value) values (%s,%s,%s,%s,%s,%s)"	
			args = (caseID,caseStepID,action,inputValue,expectedValue,actualValue)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		
def validateString(testCaseItem):
	if not testCaseItem: 
		return " "
	return testCaseItem

def readTestCasesFromDB():
	conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"> <col width="180"><col width="380"><col width="280"><tr><th>Action </th> <th>Input value </th> <th>Expected value</th><th>Outcome</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+validateString(r[2])+'</td><td>'+validateString(r[3])+'</td><td>'+validateString(r[4])+'</td></tr>'
		#print("r[1]|"+validateString(r[1])+"r[2]|"+validateString(r[2])+"r[3]|"+validateString(r[3])+"r[4]|"+validateString(r[4])+"r[5]|"+validateString(r[5])+"r[6]|"+validateString(r[6])+"r[7]|"+validateString(r[7])+"r[8]|"+validateString(r[8])+"r[9]|"+validateString(r[9]))
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data">	<input type="submit" value="Execute Test cases" name="submit"></form></body></html>'
	#fileContent =  fileContent + '</body></html>'
	return fileContent

@app.route('/ExecuteTestCase',methods = ['POST'])
def ExecuteTestCaseUpdateResult():
	resultArray=["Result1","Result2","Result3","Result4","Result5"]
	testCaseStepID=["1","2","3","4","5"]
	testCaseID="TC103"
	i=0
	jsonStringForTestCase=getJSONStringForTestCases()
	session['TestCaseString']=jsonStringForTestCase
	print("jsonStringForTestCase==>"+jsonStringForTestCase)
	#request.args["TestCaseToBeExecuted"]=jsonStringForTestCase
	conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
	cur = conn.cursor()
	for resultItem in resultArray:
		query = "UPDATE  ivr_test_case_master set actual_value = %s where testcaseid=%s and testcasestepid = %s"	
		args = (resultItem,"TC103",testCaseStepID[i])
		i=i+1
		cur.execute(query,args)
	conn.commit()
	cur.close()
	conn.close()
	return redirect("http://localhost:5001/start", code=307)
	#return ReturnTestCaseHTMLResult(testCaseID)
	
def ReturnTestCaseHTMLResult(testCaseIDToBePublished):	
	conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
	cur = conn.cursor()
	cur.execute("SELECT * FROM ivr_test_case_master")
	fileContent = """<html><title>IVR test case Execution Result</title><body><table border="1"> <col width="180"><col width="380"><col width="280"><tr> <th>Input value </th> <th>Expected value</th><th>Outcome</th></tr>"""
	for r in cur:
		fileContent =  fileContent + '<tr><td>'+r[2]+'</td><td>'+r[3]+'</td><td>'+r[4]+'</td></tr>'
		print("R3==>"+r[3])
	cur.close()
	conn.close()
	fileContent = fileContent +'<form action="/ExecuteTestCase" method="post" enctype="multipart/form-data">	<input type="submit" value="Execute Test cases" name="submit"></form></body></html>'
	#fileContent =  fileContent + '</body></html>'
	return fileContent

def getJSONStringForTestCases():
	conn = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='infypoc')
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
		
if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
