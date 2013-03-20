#!/usr/bin/python
import urllib2
import hashlib
import os
import sqlite3
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

## Sending email variables
fromaddy='Automation <foo@bar.com>'
toaddy='Me <bar@foo.com>'
subj='Jobs Report'

user='foobar'
_pass='barfoo'

server='mail.foobarfoo.net'
helostring='remote.foobarfoo.net'

## End mail variables.

datestamp=datetime.now().strftime("%Y-%m-%d")
dbpath='/home/ag/schoolstalker9000/jobs.db'

# Start URL List
d={'1':{'URL':'','Desc':'','Area':'', 'Postdata':''}
}
# End URL List

# Connect to the database, create it if it doesn't exist. 
dbcon = sqlite3.connect(dbpath)
dbcur=dbcon.cursor()
dbquery="create table if not exists districts (isd VARCHAR(255), area VARCHAR(255), url VARCHAR(255), md5 VARCHAR(32), last_updated VARCHAR(10), last_scanned VARCHAR(10), has_error VARCHAR(5), pubpri VARCHAR(255));"

# DB Connection Parsing Function
def parse_db_query(_query):
    return str(dbcon.execute(_query).fetchall()[0][0])

dbcur.execute(dbquery)

# Loop through the URLs.
for v in d:
    _error=False
    _area= d[v]['Area']
    _desc=d[v]['Desc']
    _url=d[v]['URL']
    
    _request=urllib2.Request(_url)
    try:
        if d[v]['Postdata']:
            _postdata=d[v]['Postdata']
            _results=urllib2.urlopen(_url, _postdata).read()
        else:
            _results=urllib2.urlopen(_url).read()
        _md5hash=hashlib.md5(_results).hexdigest()
    except urllib2.HTTPError, e:
        print _url
        _error=True
    except urllib2.URLError, e:
        print _url
        _error=True

    _dbquery="select exists (select 1 from districts where isd='%s' limit 1);" %(_desc)
    # If the ISD already exists in the table
    if '1' in parse_db_query(_dbquery):
        # Grab the MD5sum and compare.
        _dbquery="select md5 from districts where isd='%s';" %(_desc)
        if _md5hash in parse_db_query(_dbquery):
            _dbquery="update districts set last_scanned='%s', has_error='%s' where isd='%s';" %(datestamp, _error, _desc)
        else:
            _dbquery="update districts set last_updated='%s', last_scanned='%s', md5='%s', has_error='%s' where isd='%s';" %(datestamp, datestamp, _md5hash, _error, _desc)
        # If the request error'd  out.
        if _error == True:
            _dbquery="update districts set last_updated='%s', has_error='%s' where isd='%s';" %(datestamp, _error, _desc)
    # If it doesn't exist, insert it.
    else:
        _dbquery="insert into districts (isd, area, url, md5, last_updated, last_scanned, has_error) values ('%s', '%s', '%s', '%s','%s','%s', '%s')" %(_desc, _area, _url, _md5hash, datestamp, datestamp, _error)

    # Execute the query
    dbcon.execute(_dbquery)

# Save the results. 
dbcon.commit()


# Construct the email body.
msgbody="School District Report for '%s'" %(datestamp)
msgbody+="\n\n"
msgbody+="***Districts that have updated their postings in the last day:***"
msgbody+="\n\n"

# List each district, url that was updated since the last run.
__query="select isd, url from districts where last_updated='%s';" %(datestamp)
for i in dbcon.execute(__query).fetchall():
    msgbody+="%s\n\t\t%s\n" %(i[0], i[1])

msgbody+="\n\n"
msgbody+="***URLs that Errored at last run.***"
msgbody+="\n\n"

# List all URLs that encountered an error in the last day, so I can investigate them.
for i in dbcon.execute("select isd, url from districts where has_error='True';").fetchall():
    msgbody+="%s\t\t%s" %(i[0]. i[1])

# Send the emaimport smtplib
msg = MIMEText(msgbody)
msg['to'] = toaddy
msg['from'] = fromaddy
msg['Subject'] = subj

mail = smtplib.SMTP(server)
mail.login(user,_pass)
mail.helo(helostring)
mail.sendmail(fromaddy, toaddy, msg.as_string())
mail.quit()
