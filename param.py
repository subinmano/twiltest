#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os
import io
import pymysql
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import sys
import requests
import json
import urllib

# Declare global variables
maxParamLength=0
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

# Upload test case information to Database
def uploadTestCaseTodynamicDB(uploadedFileName,currentUserName):
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
			inputDynamicParam = TestCaseLine[9]
			outputDynamicParam = TestCaseLine[10]
			query = "INSERT INTO ivr_dynamic_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence, uploaded_date,input_dynamic_param,output_dynamic_param,username) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			args = (caseID,caseStepID,actionType,inputType,inputValue,inputPause,expectedValue,promptDuration,expectedConfidence,uploadDatetime,inputDynamicParam,outputDynamicParam,currentUserName)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""

#Get Distinct TestcaseID from the table	
def getDistinctTestCaseIdFromDB(currentUserName):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT distinct(testcaseid), username FROM ivr_dynamic_test_case_master where username = '"+currentUserName+"'")
	testcaseidstring=[]
	for r in cur:
		testcaseidstring.append(r[0])
	cur.close()
	conn.close()
	return testcaseidstring

# Create dynamic parameter strings for input and output parameters
def formSingleParamString(testCaseID):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	cur.execute("SELECT input_dynamic_param from ivr_dynamic_test_case_master where testcaseid = '"+testCaseID+"'")
	paramList = ''
	for r in cur:
		if len(r[0])>2:
			paramList = paramList + r[0] + '^'
	cur.execute("SELECT output_dynamic_param from ivr_dynamic_test_case_master where testcaseid = '"+testCaseID+"'")
	for s in cur:
		#print("Param::"+r[0]+"Leng::"+str(len(r[0])))
		if len(s[0])>2:
			#print("Param::"+r[0]+"Leng::"+str(len(r[0])))
			paramList = paramList + s[0] + '^'
	#print("paramList::"+paramList)
	conn.close()
	cur.close()
	return paramList[:-1]

# Create Json for input and output dynamic parameter string
def formJsonObjForAllParam(paramList):
	paramListArray = paramList.split("^")
	jsonString = '{'
	for paramSample in paramListArray:
		rawParamSplitted=paramSample.split(";")
		#print(rawParamSplitted)
		for eachParamString in rawParamSplitted:
			#print("rawParamSplitted::"+eachParamString)
			tempParamValuesArray=eachParamString.split("=")
			paramValuesArray=tempParamValuesArray[1].split("|");
			maxParamLength=len(paramValuesArray)
			jsonString = jsonString + '"dynamicParamLength":'+ str(len(paramValuesArray)) +","
			#print("maxParamLength::"+str(maxParamLength))
			jsonString = jsonString+ '"' +tempParamValuesArray[0]+'":[ '
			for eachParam in paramValuesArray:
				jsonString = jsonString + '"'+ eachParam + '",'
				#print("Parama::"+eachParam)
			#print("jsonString::"+jsonString[:-1])
			jsonString = jsonString.replace("\n","")
			jsonString = jsonString[:-1] + '],'
	jsonString = jsonString[:-1] + '}'
	#print("jsonString::"+jsonString)
	jsonData = json.loads(jsonString)
	#print (jsonData['source'][0])
	#print (jsonData['number1'][0])
	#print (jsonData['destination'][0])
	return jsonData

# Create individual test case for every dynamic parameter and insert to Database
def ExpandAndUpdateDynamicTestCase(paramJsonObj,dynamicParamLen,testCaseID,currentUserName):
	i=0
	for i in range(dynamicParamLen):
		conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		connIns = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
		cur = conn.cursor()
		insCur = connIns.cursor()
		cur.execute("SELECT testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration,expected_confidence,actual_value,result,input_dynamic_param,output_dynamic_param,username from ivr_dynamic_test_case_master where testcaseid = '"+testCaseID+"' and username = '"+currentUserName+"'")
		paramList = ''
		#print("maxParamLength::"+str(dynamicParamLen))
		for r in cur:
			inputValue=r[4]
			outputValue=r[6]
			#print("String::"+r[4])
			if len(r[11])>2:
				replacedValue=r[4]
				rawDynamicParam=r[11]
				processedDynamicParam = rawDynamicParam.split(";")
				#print("replacedValue::"+replacedValue+"rawDynamicParam::"+rawDynamicParam)
				for eachDynamicParam in processedDynamicParam:
					#print("eachDynamicParam::"+eachDynamicParam)
					onlyParamName=eachDynamicParam.split("=")
					#print("paramJsonObj::"+paramJsonObj['number1'][i])
					replacedValue=replacedValue.replace(onlyParamName[0],paramJsonObj[onlyParamName[0]][i])
					inputValue=replacedValue
				#print("replacedValue::"+replacedValue)
			if len(r[12])>2:
				replacedValue=r[6]
				rawDynamicParam=r[12]
				processedDynamicParam = rawDynamicParam.split(";")
				#print("replacedValue::"+replacedValue+"rawDynamicParam::"+rawDynamicParam)
				for eachDynamicParam in processedDynamicParam:
					#print("eachDynamicParam::"+eachDynamicParam)
					onlyParamName=eachDynamicParam.split("=")
					#print("paramJsonObj::"+paramJsonObj['number1'][i])
					replacedValue=replacedValue.replace(onlyParamName[0],paramJsonObj[onlyParamName[0]][i])
					outputValue=replacedValue
			inputValue = inputValue.replace('{','',2)
			inputValue = inputValue.replace('}','',2)
			outputValue = outputValue.replace('}','',2)
			outputValue = outputValue.replace('{','',2)
			print("inputValue::"+inputValue+"::Output::replacedValue::"+outputValue)
			#print("Output::replacedValue::"+replacedValue)
			uploadDatetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			query = "INSERT INTO ivr_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence,uploaded_date,username) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			print(r[0]+"|"+r[1]+"|"+r[2]+"|"+r[3]+"|"+inputValue+"|"+r[5]+"|"+outputValue+"|"+r[7]+"|"+r[8]+"|"+uploadDatetime+"|"+currentUserName)
			args = (r[0]+"_"+str(i+1),r[1],r[2],r[3],inputValue,r[5],outputValue,r[7],r[8],uploadDatetime,currentUserName)
			insCur.execute(query,args)
			connIns.commit()
	insCur.close()
	conn.close()
	connIns.close()
	cur.close()
	return ""
