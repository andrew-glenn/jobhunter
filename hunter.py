#!/usr/bin/python
import urllib2
import hashlib
import os
import sqlite3
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from config import Config

config = Config()
## Sending email variables


datestamp=datetime.now().strftime("%Y-%m-%d")
dbcon = sqlite3.connect(config.dbpath)
dbcur = dbcon.cursor()
 
# Start URL List
# Connect to the database, create it if it doesn't exist. 
class turbopower:
    # define all the things!
    def __init__(self):
        self._error=''
        self._area=''
        self._desc=''
        self._url=''
        self._md5hash=''

    def parse_db_query(self, _query):
        return str(dbcon.execute(_query).fetchall()[0][0])

    def init_db(self):
        dbquery="create table if not exists districts (isd VARCHAR(255), area VARCHAR(255), url VARCHAR(255), md5 VARCHAR(32), last_updated VARCHAR(10), last_scanned VARCHAR(10), has_error VARCHAR(5), pubpri VARCHAR(255));"
        dbcur.execute(dbquery)

    def iterate_url(self):
        # Loop through the URLs.
        for v in config.d:
            self._error=False
            self._area=config.d[v]['Area']
            self._desc=config.d[v]['Desc']
            self._url=config.d[v]['URL']
            
            _request=urllib2.Request(self._url)
            try:
                if config.d[v]['Postdata']:
                    _postdata=config.d[v]['Postdata']
                    _results=urllib2.urlopen(self._url, _postdata).read()
                else:
                    _results=urllib2.urlopen(self._url).read()
                    self._md5hash=hashlib.md5(_results).hexdigest()
            except urllib2.HTTPError, e:
                self._error=True

            except urllib2.URLError, e:
                self._error=True

            if 'as of' in _results:
                print _results
        
            self.update_db()

    def update_db(self):
        _dbquery="select exists (select 1 from districts where isd='%s' limit 1);" %(self._desc)
        if '1' in self.parse_db_query(_dbquery):
            # Grab the MD5sum and compare.
            _dbquery="select md5 from districts where isd='%s';" %(self._desc)
            if self._md5hash in self.parse_db_query(_dbquery):
                _dbquery="update districts set last_scanned='%s', has_error='%s' where isd='%s';" %(datestamp, self._error, self._desc)
            else:
                _dbquery="update districts set last_updated='%s', last_scanned='%s', md5='%s', has_error='%s' where isd='%s';" %(datestamp, datestamp, self._md5hash, self._error, self._desc)
            # If the request error'd  out.
            if self._error == True:
                _dbquery="update districts set last_updated='%s', has_error='%s' where isd='%s';" %(datestamp, self._error, self._desc)
        # If it doesn't exist, insert it.
        else:
            _dbquery="insert into districts (isd, area, url, md5, last_updated, last_scanned, has_error) values ('%s', '%s', '%s', '%s','%s','%s', '%s')" %(self._desc, self._area, self._url, self._md5hash, datestamp, datestamp, self._error)
    
        # Execute the query
        dbcon.execute(_dbquery)
    
        # Save the results. 
        dbcon.commit()
    
    def send_email(self):
        # Construct the email body.
        msgbody="School District Report for '%s'" %(datestamp)
        msgbody+="\n\n"
        msgbody+="***Districts that have updated their postings in the last day:***"
        msgbody+="\n\n"

        # List each district, url that was updated since the last run.
        _query="select isd, url from districts where last_updated='%s';" %(datestamp)
        for i in dbcon.execute(_query).fetchall():
            msgbody+="%s\n\t\t%s\n" %(i[0], i[1])
    
        msgbody+="\n\n"
        msgbody+="***URLs that Errored at last run.***"
        msgbody+="\n\n"

        # List all URLs that encountered an error in the last day, so I can investigate them.
        for i in dbcon.execute("select isd, url from districts where has_error='True';").fetchall():
            msgbody+="%s\t\t%s\n\n" %(i[0]. i[1])
    
        # Send the emaimport smtplib
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
