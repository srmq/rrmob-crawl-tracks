import datetime
import requests
from requests.auth import AuthBase
from dateutil import tz, parser
from email.utils import parseaddr
import json
import traceback

import spotipy

from . import conf
from .dbfuncs import (
    create_tables, init_db_engine, drop_tables,
    session_scope, get_PlayHistory_for_User,
    get_User_by_email, db_insert_User,
    get_Track_from_SpotifyId,
    get_Artist_from_SpotifyId,
    get_Playlist_from_SpotifyId,
    get_Album_from_SpotifyId
)
from .dbclasses import (
    Base, User, FullTrack, PlayHistory, 
    AudioFeatures, AudioAnalysis, 
    FullArtist, FullPlaylist, FullAlbum
)

root_pass = ""

def update_spotify_profile(user : User, token_info):
    sp = spotipy.Spotify(auth=token_info)
    userObj = sp.me()
    if userObj:
       user.user_obj = userObj
       user.spot_id = userObj['id']

def retrieve_Track_by_SpotifyId(track_spotify_id):
    token_info = get_app_accesstoken()
    sp = spotipy.Spotify(auth=token_info)
    trackObj = sp.track(track_spotify_id)
    return trackObj

def retrieve_Artist_by_SpotifyId(artist_spotify_id):
    token_info = get_app_accesstoken()    
    sp = spotipy.Spotify(auth=token_info)
    artistObj = sp.artist(artist_spotify_id)
    return artistObj

def retrieve_Playlist_by_SpotifyId(playlist_spotify_id, token_info):
    sp = spotipy.Spotify(auth=token_info)
    playlistObj = None
    try:
        playlistObj = sp.playlist(playlist_spotify_id)
    except Exception as e:
        msg = "An Error ocurred: " + str(e)
        print(msg)
        print("Traceback follows:")
        traceback.print_exc()
    finally:    
        return playlistObj

def retrieve_Album_by_SpotifyId(album_spotify_id):
    token_info = get_app_accesstoken()        
    sp = spotipy.Spotify(auth=token_info)
    albumObj = sp.album(album_spotify_id)
    return albumObj

def add_features(fullTrack : FullTrack):
    token_info = get_app_accesstoken()            
    sp = spotipy.Spotify(auth=token_info)
    afObject = sp.audio_features([fullTrack.spot_id])
    audioFeatures = AudioFeatures(feature_obj=afObject)
    fullTrack.audioFeatures = audioFeatures
    aaObject = sp.audio_analysis(fullTrack.spot_id)
    audioAnalysis = AudioAnalysis(analysis_obj=aaObject)
    fullTrack.audioAnalysis = audioAnalysis

def processFromEpoch(session, email, initDateEpoch, dbUser, limit=50):
    sp = spotipy.Spotify(auth=get_accesstoken_for_user(email))
    played = sp.current_user_recently_played(limit=limit, after=initDateEpoch)
    #json_formatted_str = json.dumps(played, indent=2)
    #print(json_formatted_str)
    itemArray = played['items']
    lastDateSeen = datetime.datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.timezone.utc)
    for obj in itemArray:
        track_obj = obj['track']
        played_at = parser.isoparse(obj['played_at'])
        if played_at > lastDateSeen:
            lastDateSeen = played_at
        context_obj = obj['context']
        newPlayHistory = PlayHistory(
            track_obj=track_obj, played_at=played_at, 
            context_obj=context_obj, parentUser=dbUser
            )
        fullTrack = get_Track_from_SpotifyId(session, track_obj['id'])
        if not fullTrack:
            trackJsonObj = retrieve_Track_by_SpotifyId(track_obj['id'])
            if trackJsonObj:
                fullTrack = FullTrack(fulltrack_obj=trackJsonObj, spot_id=trackJsonObj['id'])
                add_features(fullTrack)
                newPlayHistory.fullTrack = fullTrack
        else:
            newPlayHistory.fullTrack = fullTrack
        fromType = context_obj['type']
        contextURI = context_obj['uri']
        contextID = contextURI[contextURI.rindex(':')+1:]
        if fromType == 'artist':
            fullArtist = get_Artist_from_SpotifyId(session, contextID)
            if not fullArtist:
                fullArtistObj = retrieve_Artist_by_SpotifyId(contextID)
                if fullArtistObj:
                    fullArtist = FullArtist(fullartist_obj=fullArtistObj, spot_id=fullArtistObj['id'])
                    newPlayHistory.fromArtist = fullArtist
            else:
                newPlayHistory.fromArtist = fullArtist
        elif fromType == 'playlist':
            fullPlaylist = get_Playlist_from_SpotifyId(session, contextID)
            if not fullPlaylist:
                fullPlaylistObj = retrieve_Playlist_by_SpotifyId(contextID, get_accesstoken_for_user(email))
                if fullPlaylistObj:
                    fullPlaylist = FullPlaylist(fullplaylist_obj=fullPlaylistObj, spot_id=fullPlaylistObj['id'])
                    newPlayHistory.fromPlaylist = fullPlaylist
            else:
                newPlayHistory.fromPlaylist = fullPlaylist
        elif fromType == 'album':
            fullAlbum = get_Album_from_SpotifyId(session, contextID)
            if not fullAlbum:
                fullAlbumObj = retrieve_Album_by_SpotifyId(contextID)
                if fullAlbumObj:
                    fullAlbum = FullAlbum(fullalbum_obj=fullAlbumObj, spot_id=fullAlbumObj['id'])
                    newPlayHistory.fromAlbum = fullAlbum
            else:
                newPlayHistory.fromAlbum = fullAlbum
        session.add(newPlayHistory)
    return len(itemArray), lastDateSeen, played['cursors']

def get_app_accesstoken():
    req = requests.post(conf.baseUrl + '/getappaccesstoken', json={'rootpass': root_pass})
    req.raise_for_status()
    auth_info = req.json()
    token_info = auth_info['access_token']
    return token_info

def get_accesstoken_for_user(email):
    req = requests.post(conf.baseUrl + '/getspotifyauth', json={'rootpass': root_pass, 'email': email})
    req.raise_for_status()
    auth_info = req.json()
    token_info = auth_info['access_token']
    return token_info


def getTracksPlayedAtDate(date=None, default_tz=tz.tzoffset('America/Recife (-03)', -10800)):
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
        try:
            print('Processing user: ' + user['fullname'] + ' <' + user['email'] + '>' )

            with session_scope() as session:
                dbUser = get_User_by_email(session, user['email'])
                if not dbUser:
                    print("User not found, adding her")
                    dbUser = User(email=user['email'])
                    db_insert_User(session, dbUser)
                    update_spotify_profile(dbUser, get_accesstoken_for_user(user['email']))
                lastPlayHistoryOnDate = get_PlayHistory_for_User(session, dbUser, myDateTime, tomorrowDate).first()
                if lastPlayHistoryOnDate:
                    myDateTime = lastPlayHistoryOnDate.played_at + datetime.timedelta(seconds=1)
                initDateEpoch = int(myDateTime.timestamp()*1000)

                limit = 50
                while True:
                    nproc, lastSeen, cursors = processFromEpoch(
                        session, user['email'], initDateEpoch, dbUser, limit)
                    initDate = datetime.datetime.fromtimestamp(int(initDateEpoch/1000), datetime.timezone.utc)
                    if not (nproc == limit and initDate.date() == lastSeen.date()):
                        break
                    else:
                        initDateEpoch = int(cursors['after'])
        except Exception as e:
            msg = "An Error ocurred while processing user " + user['fullname'] + ' <' + user['email'] + '>' + ": " + str(e)
            print(msg)
            print("Traceback follows:")
            traceback.print_exc()
            print("Skipping to next user...")

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

    global root_pass
    root_pass = args.crawl_args[0]

    dateToCrawl = datetime.datetime.strptime(args.crawl_args[1], '%Y-%m-%d')
    getTracksPlayedAtDate(date=dateToCrawl)    
