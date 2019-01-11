import os
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
from jiwer import wer
from difflib import SequenceMatcher

#Initiate Flask app
app = Flask(__name__,template_folder='template')

@app.route('/Testjiwer',methods = ['POST'])
def Testjiwer():
	ground_truth = "Thanks for calling ABC Bank. Press 1 for Banking, for credit card press 2"
	hypothesis = "Thanks for calling ABC Bank Press 1 four banking four credit card press 2"
	error = wer(ground_truth, hypothesis)
	ratio = SequenceMatcher(None, ground_truth, hypothesis).ratio()
	print(error, ratio)
	return ""

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
