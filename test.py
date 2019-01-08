import os
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
from jiwer import wer

#Initiate Flask app
app = Flask(__name__,template_folder='template')

@app.route('/Testjiwer',methods = ['POST'])
def Testjiwer():
	ground_truth = "hello world"
	hypothesis = "hello duck"
	error = wer(ground_truth, hypothesis)
	print(error)
	return ""

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
