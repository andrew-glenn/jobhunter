#!/usr/bin/env python
import smtplib
import HTMLParser
from email.mime.text import MIMEText
from config import Config

config = Config()
## Sending email variables
datestamp=datetime.now().strftime("%Y-%m-%d")
dbcon = sqlite3.connect(config.dbpath)
dbcur = dbcon
   
def send_email():
        # Construct the email body.
        msgbody="School District Report for '%s'" %(datestamp)
        msgbody+="\n\n"
        msgbody+="***Districts that have updated their postings since the last run:***"
        msgbody+="\n\n"

#        List each district, url that was updated since the last run, that are relevant.
#        _query="select isd, url from districts where last_updated='%s' and relevant='True';" %(datestamp)
        _query="select isd, url from districts where last_updated='%s';" %(datestamp)
        for i in dbcon.execute(_query).fetchall():
            msgbody+="%s\n\t\t%s\n" %(i[0], i[1])
    
        msgbody+="\n\n"
        msgbody+="***URLs that Errored at last run.***"
        msgbody+="\n\n"

        # List all URLs that encountered an error in the last run, so I can investigate them.
        _query="select isd, url from districts where has_error='True';"
        for i in dbcon.execute(_query).fetchall():
            msgbody+="%s\t\t%s\n\n" %(i[0], i[1])

        msgbody+="\n\n"
        msgbody+="***Districts that updated their postings, but no relevant positions were found.***"
        msgbody+="\n\n"

#        # All districts that updated their postings, but no relevant positions were found. 
        _query="select isd, url from districts where last_updated='%s' and relevant='False';" %(datestamp)
        for i in dbcon.execute(_query).fetchall():
            msgbody+="%s\n\t\t%s\n" %(i[0], i[1])
     
        # Send the email. 
        msg = MIMEText(msgbody)
        msg['to'] = config.toaddy
        msg['from'] = config.fromaddy
        msg['Subject'] = config.subj

        mail = smtplib.SMTP(config.server)
        mail.login(config.user,config.password)
        mail.helo(config.helostring)
        mail.sendmail(config.fromaddy, config.toaddy, msg.as_string())
        mail.quit()


if __name__ == "__main__":
    turbopower = turbopower()
    turbopower.iterate_url()
    turbopower.init_db()
    turbopower.send_email()
