#!/usr/bin/python
# -*- coding: utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Declare global variables
sender_email_id = os.environ["fromemailid"]
sender_email_id_password = os.environ["frompassword"]
receiver_email_id = os.environ["toemailid"]

def sendEMAIL(testcaseID, testCaseStep, expected_value, actual_value):
 
  # creates SMTP session
  s = smtplib.SMTP('smtp.gmail.com', 587)
  
  # start TLS for security
  s.starttls()
  
  # mail account credentials
  s.login("sender_email_id", "sender_email_id_password")
  
  # create the message
  msg = MIMEMultipart()
  
  # setup the parameters of the message
  msg['From']=MY_ADDRESS
  msg['To']=email
  msg['Subject']="Test Case failure"
  
  # message to be sent
  message = 'Please note that Test case number ' +testcaseID+ ' has failed at step ' +testCaseStep+ '. The expected response was ' +expected_value+ ' and the actual response was ' +actual_value+ '.'
  
  # load the message
  msg.attach(MIMEText(message, 'plain'))
  
  # send the mail
  s.send_message(msg)
  del msg
  
  # terminating the session
  s.quit()
  
  return ""
