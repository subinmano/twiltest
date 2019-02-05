import os
import io
import sys
import requests
import json
import urllib
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template
# Google Cloud SDK
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

#Initiate Flask app
app = Flask(__name__,template_folder='template')

# Declare global variables
credentials_dgf = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

# This function calls Google STT and then returns recognition as text
@app.route('/goog_speech2text', methods=['GET', 'POST'])
#def goog_speech2text(RecordingUrl):
def goog_speech2text():
	RecordingUrl = request.values.get("RecordingUrl", None)
	#Generate Google STT Credentials
	service_account_info = json.loads(credentials_dgf)
	credentials = service_account.Credentials.from_service_account_info(service_account_info)
	# Create Google STT client
	client = speech.SpeechClient(credentials=credentials)
	#Create temporary file
	audiofileNameSplit = RecordingUrl.split("/")
	audiofile = audiofileNameSplit[len(audiofileNameSplit)-1]
	urllib.request.urlretrieve(RecordingUrl, audiofile)
	#Pass the audio to be recognized by Google Speech-To-Text
	with io.open(audiofile, 'rb') as audio_file:
		content = audio_file.read()
	audio = speech.types.RecognitionAudio(content=content)
	#Set the configuration parameters of the audio file for Google STT
	config = speech.types.RecognitionConfig(
		encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
		sample_rate_hertz=8000,
		language_code='en-US',
		# Enhanced models are only available to projects that opt in for audio data collection
		use_enhanced=True,
		# Specify the model for the enhanced model usage.
		model='phone_call')
	#Get the response from Google STT	
	response = client.recognize(config, audio)
	recognized_text = ""
	for i in range(len(response.results)):
		recognized_text += response.results[i].alternatives[0].transcript
	print("Transcript: " + recognized_text)
	return ""
	
	#for result in response.results:
		#print('Transcript: {}'.format(result.alternatives[0].transcript))
		#recognized_text = result.alternatives[0].transcript
	#return recognized_text

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print ('Starting app on port %d' % port)
	app.run(debug=False, port=port, host='0.0.0.0')
