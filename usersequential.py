#!/usr/bin/python
# -*- coding: utf-8 -*-
#import python modules
import os
import io
import pymysql
import sys
import requests
import json
import urllib
from jiwer import wer
from difflib import SequenceMatcher
from datetime import datetime
import time
import re

# Twilio Helper Library
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather, Say, Dial, Play
# Signalwire Helper lirary
from signalwire.rest import Client as signalwire_client
from signalwire.voice_response import VoiceResponse

# Import Flash Modules
from flask import Flask, request, Response, make_response, jsonify, url_for, redirect, session, render_template, Blueprint, flash
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import g

# Import custom modules
import transcribe
import updateresult
import param
from models import User
from models import db

auth = Blueprint('auth', __name__)

# Declare Global variables
cli = os.environ["cli"]
account_sid = os.environ["account_sid"]
auth_token = os.environ["auth_token"]
signalwire_space_url = os.environ["signalwire_space_url"]
databasename = os.environ["databasename"]
databasehost = os.environ["databasehost"]
databaseusername = os.environ["databaseusername"]
databasepassword = os.environ["databasepassword"]

###############################################################User Management####################################################################
#Render the Login page
@auth.route('/login')
def login():
    return render_template('login.html')
  
#Process user details
@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    session['username'] = email
    remember = True if request.form.get('remember') else False
    # check if user actually exists , take the user supplied password, hash it, and compare it to the hashed password in database
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page
    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))
  
#Render the signup page
@auth.route('/signup')
def signup():
    return render_template('signup.html')

#Create user with details
@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    # Check if user exists-if this returns a user, then the email already exists in database
    user = User.query.filter_by(email=email).first() 
    # if a user is found, we want to redirect back to signup page so user can try again
    if user: 
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))
    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))

#logout the user
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username')
    return redirect(url_for('main.index'))
  
########################################################### Upload Test Case ###########################################################################


