import sys
from email.mime.text import MIMEText
from email.header import Header
import smtplib
import os
 
 #YandexMailbox smtp server
host_server = 'smtp.yandex.com'
 #YandexMailbox smtp server port
ssl_port = '465'
 #username 
user = 'no-reply@scratchblox.tk'
 #pwd is the password
pwd = os.environ.get("pwd")
 #Sender's mailbox
sender_mail = 'no-reply@scratchblox.tk'
 
def send_mail(receiver,mail_title,mail_content):
    msg = MIMEText(mail_content, "plain", 'utf-8')
    msg["Subject"] = Header(mail_title, 'utf-8')
    msg["From"] = sender_mail
    msg["To"] = receiver
    try:
                 # ssl login
        smtp = smtplib.SMTP_SSL(host_server, ssl_port)
                 # set_debuglevel() is used for debugging. The parameter value is 1 to turn on the debugging mode, and the parameter value is 0 to turn off the debugging mode
        # smtp.set_debuglevel(1)
        smtp.ehlo(host_server)
        smtp.login(user, pwd)
        smtp.sendmail(sender_mail, receiver, msg.as_string())
        smtp.quit()
        return True
    except Exception as e:
        print(str(e))
        return False