import datetime
import requests
from requests.auth import AuthBase
import os
from dateutil import tz
from email.utils import parseaddr
import json

import spotipy

from . import conf

_root_pass = os.getenv('ROOT_PASS')
if not _root_pass:
    raise Exception("Configuration Error. No ROOT_PASS found")

def getTracksPlayedAtDate(email=None, date=None, default_tz=tz.tzoffset('America/Recife (-03)', -10800)):
    """The tracks played by that user at a particular date.

    Parameters
    ----------
    email : str
        The user email address.
    date
        The date in which the tracks were played.    

    """
    if not email:
        raise Exception('email parameter is mandatory')
    if not '@' in parseaddr(email)[1]:
        raise Exception('Email address is invalid')

    if not date:
        raise Exception('date parameter is mandatory')

    myDateTime = datetime.datetime(date.year, date.month, date.day, hour=0, minute=0, second=0)
    myDateTime = myDateTime.replace(tzinfo=(default_tz if not date.tzinfo else date.tzinfo))    

    initDateEpoch = int(myDateTime.timestamp()*1000)

    req = requests.post(conf.baseUrl + '/getspotifyauth', json={'rootpass': _root_pass, 'email': email})

    req.raise_for_status()

    auth_info = req.json()

    token_info = auth_info['access_token']

    if not token_info:
        raise Exception('Did not receive access token')

    sp = spotipy.Spotify(auth=token_info)

    played = sp.current_user_recently_played(limit=50, after=initDateEpoch)

    json_formatted_str = json.dumps(played, indent=2)

    print(json_formatted_str)    



    