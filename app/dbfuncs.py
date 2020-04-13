import os
from contextlib import contextmanager

from .dbclasses import (
    Base, User, FullTrack, PlayHistory, 
    AudioFeatures, AudioAnalysis, 
    FullArtist, FullPlaylist, FullAlbum
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _db_not_initialized():
    raise Exception("Database engine was not initialized. Call init_db_engine(dbUrl) first")


_engine = None
_Session = _db_not_initialized 

def _get_db_engine():
    if not _engine:
        _db_not_initialized()
    return _engine


def init_db_engine(dbUrl : str):
    global _engine
    _engine = create_engine(dbUrl, echo=True)
    global _Session 
    _Session = sessionmaker(bind=_engine)

def create_tables():
    Base.metadata.create_all(_get_db_engine())

def drop_tables():
    Base.metadata.drop_all(_get_db_engine())

def get_PlayHistory_for_User(session,
        user : User, after : datetime.datetime, 
        before : datetime.datetime
        ):
    return session.query(PlayHistory).filter(
                PlayHistory.user_id == user.id, 
                PlayHistory.played_at < before,
                PlayHistory.played_at >= after
            ).order_by(PlayHistory.retrieved_at.desc())

def get_User_by_email(session, email):
    return session.query(User).filter(User.email == email).first()

def db_insert_User(session, user : User):
    session.add(user)

def get_Track_from_SpotifyId(session, track_spotify_id):
    return session.query(FullTrack).filter(FullTrack.spot_id == track_spotify_id).first()

def get_Artist_from_SpotifyId(session, artist_spotify_id):
    return session.query(FullArtist).filter(FullArtist.spot_id == artist_spotify_id).first()

def get_Playlist_from_SpotifyId(session, playlist_spotify_id):
    return session.query(FullPlaylist).filter(FullPlaylist.spot_id == playlist_spotify_id).first()    

def get_Album_from_SpotifyId(session, album_spotify_id):
    return session.query(FullAlbum).filter(FullAlbum.spot_id == album_spotify_id).first()

@contextmanager
def session_scope():
    session = _Session() 
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
