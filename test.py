#!/usr/bin/env python
from sqlalchemy import *

db = create_engine('sqlite:///jobs.db')
metadata = MetaData(db)
dist = Table('districts', metadata, autoload=True)

s = select(["*"]).where(dist.c.isd=="MOODY")
results = s.execute().fetchone()

try:
    len(results)
    print results
    print "Update goes here"
except TypeError:
    print "No results found"
