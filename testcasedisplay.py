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

# Declare global variables
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

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
	#fileContent = fileContent +'<form action="/ExecuteTestCase?TestCaseId='+testcaseid+'" method="post" enctype="multipart/form-data"><input type="submit" value="Execute Test Case" name="submit"></form></body></html>'
	fileContent = fileContent +'<form action="/ExecuteTestCase?TestCaseId='+testcaseid+'" method="post" enctype="multipart/form-data"><input type="submit" value="Execute Test Case" name="submit"></form>''<form action="/ShowTestResult?TestCaseId='+testcaseid+'" method="post" enctype="multipart/form-data"><input type="submit" value="Show Test Result" name="submit"></form></body></html>'
	return fileContent

#Validation of testcase upload
def validateString(testCaseItem):
	if not testCaseItem:
		return ""
	return testCaseItem
