#!/usr/bin/python

class Config:
    dbpath='/path/to/jobs.db'
    archivedir='/path/to/archive'

    fromaddy 'From Address <from@foo.bar>'
    toaddy = 'to@foo.bar'
    subj = 'Subject'
    user = 'bar.foo'
    password = 'foobar.password'
    server = 'herp.derp.foobar'
    helostring = 'me.herpa.derpa.foobar'

    d={'1':{'URL':'https://google.com/','Desc':'Google','Area':'CA', 'Postdata':''},
        '2':{'URL':'http://yahoo.com','Desc':'Yahoo','Area':'NYC', 'Postdata':'var1=foobar&var2=jobs&var3=yes'}
}
