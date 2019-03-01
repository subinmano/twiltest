#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client


# Declare global variables
smscli = os.environ["smscli"]
smsdnis = os.environ["smsdnis"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
signalwire_space_url = os.environ["signalwire_space_url"]

def sendSMS(testcaseID, testCaseStep):
	#via Twilio
	client = Client(account_sid, auth_token)
	#via Signalwire
	client = signalwire_client(account_sid, auth_token, signalwire_space_url = signalwire_space_url)
	client.messages.create(from_=smscli,
	                       to=smsdnis,
						   body='Please note that  ' +testcaseID+ ' has failed at ' +testCaseStep+ '.'
						   )
	return ""
