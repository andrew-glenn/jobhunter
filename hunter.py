:
#!/usr/bin/python
import urllib2
import hashlib
import os
import sqlite3
import smtplib
import re
import shutil
import HTMLParser
from datetime import datetime
from email.mime.text import MIMEText
from config import Config

config = Config()
## Sending email variables

datestamp=datetime.now().strftime("%Y-%m-%d")
dbcon = sqlite3.connect(config.dbpath)
dbcur = dbcon

class TalentEDParse(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.in_tr = False
        self.table_data = False
        self.iteration = 0
        self.ptitle = None
        self.pdate = None
        self.ptype = None
        self.plocation = None
        self.array = []
        self.regex_pattern = '\xc2\xa0|^[0-9]$|Job Title|Posting Date|Type|Location'

    # What do we do at the start tag? <br><hr><title>, etc? 
    def handle_starttag(self, tag, attrs):
         if tag == 'tr':
             self.in_tr = True
         if tag == 'td' and self.in_tr == True:
            self.table_data = True

    # How do we handle the data within the tag? 
    def handle_data(self, data):
        if data is not None and self.table_data:
            if self.iteration is 0:
                self.ptitle = self.remove_ettera(data)
            elif self.iteration is 1:
                self.pdate = self.remove_ettera(data)
            elif self.iteration is 2:
                self.ptype = self.remove_ettera(data)
            elif self.iteration is 3:
                self.plocation = self.remove_ettera(data)

    # So, we have some crap we don't like. Let's get rid of it.
    #   See self.regex_pattern above.
    def remove_ettera(self, data):
        data = re.sub(self.regex_pattern, '', data)
        return data

    # What about the end tag>
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_tr:
            self.iteration = 0
            self.in_tr = False
        elif tag == 'td' and self.in_tr:
            self.iteration += 1
        if self.ptitle and self.pdate and self.ptype and self.plocation:
            dictionary = {  'title': self.ptitle, 
                            'date': self.pdate, 
                            'type': self.ptype, 
                            'location': self.plocation }
            self.array.append(dictionary)
 
    # Removing duplicates within the dictionary (self.array). 
    def candycrush(self, data):
        puppybrother = [dict(tupleized) for tupleized in set(tuple(item.items()) 
                            for item in data)]
        return puppybrother

class turbopower:
    # define all the things!
    def __init__(self):
        self._error = None
        self._area = None
        self._desc = None
        self._url = None
        self._md5hash = None
        self._regex=['.*<!--.*-->.*',
                    '.*var beaconURL.*',
                    '.*socs.fes.org.*',
                    '.*counter.edlio.com.*',
                    '.*id="hLoadTime" value="...."',
                    '.*<input type=.hidden.*',
                    '.*<p id="date".*',
                    '.*sessionid.*',
                    '.*loadstamp.*',
                    '.*timeStamp.*',
                    '.*beacon-1.newrelic.com.*']

        self._relevant = False
        self._pmatch='teacher|elementary|sped|special ed(ucation+)|[1-5](st|nd|rd|th)\ grade|EC-6'
        self._talented = False

        _archive="{0}/{1}.{2}".format(config.archivedir, "jobs.db", datestamp)
        shutil.copy(config.dbpath, _archive)

    def parse_db_query(self, _query):
        return str(dbcon.execute(_query).fetchall()[0][0])

    def init_db(self):
        dbquery="create table if not exists districts (isd VARCHAR(255), area VARCHAR(255), url VARCHAR(255), md5 VARCHAR(32), last_updated VARCHAR(10), last_scanned VARCHAR(10), has_error VARCHAR(5), pubpri VARCHAR(255), relevant INTEGER);"
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
            except urllib2.HTTPError, e:
                self._error=True

            except urllib2.URLError, e:
                self._error=True

            if _results:
                # Remove the stuff we don't care about. "Server Generation Time: X seconds", etc. 
                # Once done, hash the remaining text. 
                # Thinking there's a better way to do this, But for now...
                for pattern in self._regex:
                    _results = re.sub(pattern, '', _results)

                if 'talented' in self._url:
                    self._talented = True
                    for line in _results.split('\n'):
                        if "<table" in line:
                            p.feed(line)

#                _rpattern = re.compile(self._pmatch, re.IGNORECASE)
#                if _rpattern.search(_results):
#                    self._relevant = True

                self._md5hash=hashlib.md5(_results).hexdigest()
            self.update_db()

    def update_db(self):
        if p.array():
            p.array = p.candycrush(p.array())

        _dbquery="select exists (select 1 from districts where isd='%s' limit 1);" %(self._desc)
        if '1' in self.parse_db_query(_dbquery):
            # Grab the MD5sum and compare.
            _dbquery="select md5 from districts where isd='%s';" %(self._desc)
            if self._md5hash in self.parse_db_query(_dbquery):
                _dbquery="update districts set last_scanned='%s', has_error='%s' where isd='%s';" %(datestamp, self._error, self._desc)
            else:
                _dbquery="update districts set last_updated='%s', last_scanned='%s', md5='%s', has_error='%s', relevant='%s' where isd='%s';" %(datestamp, datestamp, self._md5hash, self._error, self._relevant, self._desc)
            # If the request error'd  out.
            if self._error == True:
                _dbquery="update districts set last_updated='%s', has_error='%s' where isd='%s';" %(datestamp, self._error, self._desc)
        # If it doesn't exist, insert it.
        else:
            _dbquery="insert into districts (isd, area, url, md5, last_updated, last_scanned, has_error, relevant) values ('%s', '%s', '%s', '%s','%s','%s', '%s','%s')" %(self._desc, self._area, self._url, self._md5hash, datestamp, datestamp, self._error, self._relevant)
    
        # Execute the query
        dbcon.execute(_dbquery)
    
        # Save the results. 
        dbcon.commit()
    
    def send_email(self):
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
