import app.trackcrawler as tc

import datetime

email = 'srmq@srmq.org'
date = datetime.datetime.now()
tc.getTracksPlayedAtDate(email, date)