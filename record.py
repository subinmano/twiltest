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
# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
#import custom modules
import transcribe

#Initiate Flask app
app = Flask(__name__,template_folder='template')

#Set key for session variables
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key=SECRET_KEY
