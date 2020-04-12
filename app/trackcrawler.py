import datetime
import requests
from requests.auth import AuthBase
from dateutil import tz, parser
from email.utils import parseaddr
import json

import spotipy

from . import conf
from .dbfuncs import (
    create_tables, init_db_engine, drop_tables,
    session_scope, get_PlayHistory_for_User,
    get_User_by_email, db_insert_User
)
from .dbclasses import (
    Base, User, FullTrack, PlayHistory, 
    AudioFeatures, AudioAnalysis, 
    FullArtist, FullPlaylist, FullAlbum
)

def update_spotify_profile(user : User, token_info):
    sp = spotipy.Spotify(auth=token_info)
    userObj = sp.me()
    if userObj:
       user.user_obj = userObj
       user.spot_id = userObj['id']

def getTracksPlayedAtDate(root_pass=None, date=None, default_tz=tz.tzoffset('America/Recife (-03)', -10800)):
    """The tracks played by that user at a particular date.

    Parameters
    ----------
    root_pass : str
        The root password we will use to retrieve the access tokens
    date
        The date in which the tracks were played.    
    default_tz
        The default time zone to use if the given date does not 
        already contains one (default value is UTC-3)

    """
    if not root_pass:
        raise Exception('root password parameter is mandatory')

    if not date:
        raise Exception('date parameter is mandatory')

    myDateTime = datetime.datetime(date.year, date.month, date.day, hour=0, minute=0, second=0)
    myDateTime = myDateTime.replace(tzinfo=(default_tz if not date.tzinfo else date.tzinfo))    

    tomorrowDate = myDateTime + datetime.timedelta(hours=24)

    req = requests.post(conf.baseUrl + '/getuserswithtoken', json={'rootpass': root_pass})
    req.raise_for_status()

    users = req.json()

    if not 'users' in users:
        raise Exception('No users with token info found')
    else:
        users = users['users']
    
    for user in users:
        print('Processing user: ' + user['fullname'] + ' <' + user['email'] + '>' )
        req = requests.post(conf.baseUrl + '/getspotifyauth', json={'rootpass': root_pass, 'email': user['email']})
        req.raise_for_status()
        auth_info = req.json()
        token_info = auth_info['access_token']
        if not token_info:
            raise Exception('Did not receive access token')

        with session_scope() as session:
            dbUser = get_User_by_email(session, user['email'])
            if not dbUser:
                print("User not found, adding her")
                dbUser = User(email=user['email'])
                db_insert_User(session, dbUser)
                update_spotify_profile(dbUser, token_info)
            lastPlayHistoryOnDate = get_PlayHistory_for_User(session, dbUser, myDateTime, tomorrowDate).first()
            if lastPlayHistoryOnDate:
                myDateTime = lastPlayHistoryOnDate.played_at + datetime.timedelta(seconds=1)
            initDateEpoch = int(myDateTime.timestamp()*1000)
            sp = spotipy.Spotify(auth=token_info)
            played = sp.current_user_recently_played(limit=50, after=initDateEpoch)
            itemArray = played['items']
            for obj in itemArray:
                #json_formatted_str = json.dumps(played, indent=2)
                #print(json_formatted_str)
                track_obj = obj['track']
                played_at = parser.isoparse(obj['played_at'])
                context_obj = obj['context']
                newPlayHistory = PlayHistory(
                    track_obj=track_obj, played_at=played_at, 
                    context_obj=context_obj, user_id=dbUser.id
                    )
                #FIXME update fulltrack_id e from_*

            
            print("Number of itens: " + str(len(played['items'])))   

def action_create(args):
    dbUrl = args.database_url[0]
    init_db_engine(dbUrl)
    create_tables()

def action_dropall(args):
    dbUrl = args.database_url[0]
    init_db_engine(dbUrl)
    drop_tables()

def action_crawl(args):
    if not args.crawl_args:
        raise Exception('--crawl-args is mandatory for crawl action')    
    if not args.crawl_args[0]:
        raise Exception('Root password is required for crawl action')
    if not args.crawl_args[1]:
        raise Exception('Date to crawl is required for crawl action')
    
    dbUrl = args.database_url[0]
    init_db_engine(dbUrl)

    dateToCrawl = datetime.datetime.strptime(args.crawl_args[1], '%Y-%m-%d')
    getTracksPlayedAtDate(root_pass=args.crawl_args[0], date=dateToCrawl)    
