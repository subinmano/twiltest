#!/usr/bin/python
# -*- coding: utf-8 -*-
import smtplib

# Declare global variables
sender_email_id = os.environ["fromemailid"]
sender_email_id_password = os.environ["frompassword"]
receiver_email_id = os.environ["toemailid"]

def sendEMAIL(testcaseID, testCaseStep, expected_value, actual_value):
 
  # creates SMTP session
  s = smtplib.SMTP('smtp.gmail.com', 587)
  
  # start TLS for security
  s.starttls()
  
  # Authentication
  s.login("sender_email_id", "sender_email_id_password") 
  
  # message to be sent
  message = 'Please note that Test case number ' +testcaseID+ ' has failed at step ' +testCaseStep+ '. The expected response was ' +expected_value+ ' and the actual response was ' +actual_value+ '.'
  
  # sending the mail
  s.sendmail("sender_email_id", "receiver_email_id", message)
  
  # terminating the session
  s.quit()
  
  return ""
