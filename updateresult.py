import os
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
import pymysql
import sys
import requests
import json
import urllib
from jiwer import wer
from difflib import SequenceMatcher
from datetime import datetime
import sendsms
import sendemail

# Declare global variables
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

#@app.route('/Result',methods = ['POST'])
def updateResultToDB(recordingURL,recognizedText,recordingDuration,testcaseID,testCaseStep):
	conn = pymysql.connect(host=databasehost, user=databaseusername, passwd=databasepassword, port=3306, db=databasename)
	cur = conn.cursor()
	query = "SELECT expected_value, expected_confidence FROM ivr_test_case_master where testcaseid = %s and testcasestepid = %s"
	args = (str(testcaseID),testCaseStep)
	cur.execute(query,args)
	for r in cur:
		expected_value = r[0]
		expected_confidence = float(r[1])
	print(str(recordingURL)+"||"+str(recognizedText)+"||"+str(recordingDuration)+"||"+testcaseID+"||"+testCaseStep+"||"+expected_value+"||"+str(expected_confidence))
	#error = wer(ground_truth, hypothesis)
	actual_confidence = round((SequenceMatcher(None, expected_value, recognizedText).ratio()), 2)
	print(actual_confidence)
	if actual_confidence<expected_confidence:
		result = "Fail"
		#sendsms.sendSMS(testcaseID,testCaseStep)
		#sendemail.sendEMAIL(testcaseID, testCaseStep, expected_value, recognizedText)
	else:
		result = "Pass"
	execution_status = "completed"
	execution_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	query = "UPDATE ivr_test_case_master set recording_url = %s, actual_value = %s, recording_duration = %s, result = %s, execution_status = %s, execution_datetime = %s where testcaseid=%s and testcasestepid = %s"
	args = (recordingURL, str(recognizedText), str(recordingDuration), str(result), str(execution_status), str(execution_datetime), str(testcaseID), testCaseStep)
	cur.execute(query,args)
	print("Rows Affected==>"+str(cur.rowcount))
	conn.commit()
	cur.close()
	conn.close()
	return ""
