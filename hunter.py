#!/usr/bin/python
# Job Hunter
# A script to assist in parsing job postings. 
#
#   A note from the author.:
#
#   This script was to assist my girlfriend in finding a job.
#   In the middle of an effort to make the results more granular, she got a job.
#   To that end, I consider this script to be a GREAT SUCCESS!
#   
#   A few statistics: 
#       Employers parsed during each run: 96
#        Average run time: 45 seconds.
#
#   Parts of this script, like the TalentED and AppleJax classes are part of that granularity effort, 
#    but are not yet called referenced during script execution.

#   I'm leaving this script as-is. To see a non-cluttered version, take a look at the last git commit or two. 
#   Should I need it later, it'll be here. 
#
### Begin Software License.
#
# This program is free software: you can redistribute it and/or modify
# it under the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# http://www.gnu.org/licenses/gpl-3.0.html
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# No Warranty or guarantee or suitability exists for the software.
# Use at your own risk. The author is not responsible if your system breaks.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
### End Software License.
#
#
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
from sqlalchemy import *
config = Config()
## Sending email variables

datestamp=datetime.now().strftime("%Y-%m-%d")

# Create the pointer to the database engine, create the DB if it doesn't exist. 
db = create_engine({0][1].format("sqlite://",config.dbpath))
#conn = db.connect()
#conn.execute("create table if not exists districts (isd VARCHAR(255), area VARCHAR(255), url VARCHAR(255), \
#                    md5 VARCHAR(32), last_updated VARCHAR(10), last_scanned VARCHAR(10), has_error VARCHAR(5), \ 
#                    pubpri VARCHAR(255), relevant INTEGER);")
#conn.close()
metadata = BoundMetadata(db)

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
        self._regex=['.*<!--.*-->.*', '.*var beaconURL.*', '.*socs.fes.org.*',
                    '.*counter.edlio.com.*', '.*id="hLoadTime" value="...."',
                    '.*<input type=.hidden.*', '.*<p id="date".*',
                    '.*sessionid.*', '.*loadstamp.*', '.*timeStamp.*',
                    '.*beacon-1.newrelic.com.*']

        self._relevant = False
        self._pmatch='teacher|elementary|sped|special ed(ucation+)|[1-5](st|nd|rd|th)\ grade|EC-6'
        self._talented = False

        _archive="{0}/{1}.{2}".format(config.archivedir, "jobs.db", datestamp)
        shutil.copy(config.dbpath, _archive)

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

                self._md5hash=hashlib.md5(_results).hexdigest()
            self.update_db()

    def update_db(self):
        dist = Table('districts', metadata, autoload=True)
        s = select('*'].where(dist.c.isd=="%s") %(self._desc)
        results = s.execute().fetchone()

        try:
            len(results)
            # Unpacking the variables
            district = str(results[0])
            area = str(results[1])
            url = str(results[2])
            md5 = str(results[3])
            last_updated = str(results[4])
            last_scanned = str(results[5])
            has_error = str(results[6])
            pubpri = str(results[7])
            relevant = str(results[8])
            
            # Let's set a the last_scanned variable to today
            last_scanned = datestamp

            # All the comparison logic
            # - If the retreived MD5 matches the MD5 of the content we pulled.
            if self._md5hash is not md5:
                # Set the last_updated to today
                # Store the retreived MD5
                last_updated = datestamp
                md5 = self._md5hash

            # If something error'd out. 
            if self._error:
                has_error = True
            upd = dist.update().where(dist.c.isd=self._desc).values(isd=self._desc, area=self._area, \
                            url=self._url, md5=self._md5hash, \
                            last_updated=datestamp, last_scanned=datestamp, \
                            has_error=self._error, relevant=self._relevant)
            results = db.execute(upd)

        # Results returned nothing            
        except NameError:
            # Insert the data into the database.
            ins = dist.insert().values(isd=self._desc, area=self._area, \
                                        url=self._url, md5=self._md5hash, \
                                        last_updated=datestamp, last_scanned=datestamp, \
                                        has_error=self._error, relevant=self._relevant)
            result = db.execute(ins)

   


if __name__ == "__main__":
    turbopower = turbopower()
    turbopower.iterate_url()
    turbopower.init_db()
    turbopower.send_email()
