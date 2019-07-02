#!/usr/bin/python
# -*- coding: utf-8 -*-
### This module updates test cases to database ###
import os
import io
import pymysql
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import sys
import requests
import json
import urllib

# Declare global variables
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

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

# Upload test case information to Database
def uploadTestCaseTodynamicDB(uploadedFileName):
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
			query = "INSERT INTO ivr_dynamic_test_case_master(testcaseid,testcasestepid,action,input_type,input_value,pause_break,expected_value,expected_prompt_duration, expected_confidence, uploaded_date,input_dynamic_param,output_dynamic_param) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			args = (caseID,caseStepID,actionType,inputType,inputValue,inputPause,expectedValue,promptDuration,expectedConfidence,uploadDatetime,inputDynamicParam,outputDynamicParam)
			if i!=0:
				cur.execute(query,args)
			else:
				i=i+1
		conn.commit()
		cur.close()
		conn.close()
		return ""
