#!/usr/bin/python
# -*- coding: utf-8 -*-
import smtplib

# Declare global variables
sender_email_id = os.environ["fromemailid"]
sender_email_id_password = os.environ["frompassword"]
receiver_email_id = os.environ["toemailid"]

def sendEMAIL(testcaseID, testCaseStep):
  # creates SMTP session
  s = smtplib.SMTP('smtp.gmail.com', 587) 
  
# start TLS for security 
s.starttls() 
  
# Authentication 
s.login("sender_email_id", "sender_email_id_password") 
  
# message to be sent 
message = "Message_you_need_to_send"
  
# sending the mail 
s.sendmail("sender_email_id", "receiver_email_id", message) 
  
# terminating the session 
s.quit() 
