import os
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import pymysql
import sys
import requests
import json
import urllib
from jiwer import wer
from difflib import SequenceMatcher

# Declare global variables
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

#@app.route('/Result',methods = ['POST'])
def updateResultToDB(recordingURL,recognizedText,testcaseID,testCaseStep):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT expected_value, expected_confidence FROM ivr_test_case_master where testcaseid = %s and testcasestepid = %s"
	args = (str(testcaseID),testCaseStep)
	cur.execute(query,args)
	for r in cur:
		expected_value = r[0]
		expected_confidence = r[1]
	print(str(recordingURL)+"||"+str(recognizedText)+"||"+testcaseID+"||"+testCaseStep+"||"+expected_value+"||"+expected_confidence+")
	#error = wer(ground_truth, hypothesis)
	confidence = 1-(SequenceMatcher(None, expected value, recognizedText).ratio())
	print(confidence)
	if confidence > expected_confidence:
		result = "pass"
	else:
		result = "fail"
	query = "UPDATE ivr_test_case_master set recording_url = %s, actual_value = %s, result = %s where testcaseid=%s and testcasestepid = %s"
	args = (recordingURL,str(recognizedText), str(result), str(testcaseID),testCaseStep)
	cur.execute(query,args)
	print("Rows Affected==>"+str(cur.rowcount))
	conn.commit()
	cur.close()
	conn.close()
	return ""
