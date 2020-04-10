from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column('id', Integer, primary_key=True) 
    email = Column(String(320), nullable=False, unique=True, index=True)

    user_obj = Column(JSONB)
    spot_id = Column(String(1024), unique=True, index=True)    
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)
    #relationship
    playHistory = relationship("PlayHistory", back_populates="parentUser")    

class FullTrack(Base):
    __tablename__ = 'tracks'
    id = Column('id', Integer, primary_key=True)
    fulltrack_obj = Column(JSONB, nullable=False)
    spot_id = Column(String(1024), unique=True, index=True, nullable=False)        
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)
    #relationships
    played = relationship("PlayHistory", back_populates="fullTrack")
    audioFeatures = relationship("AudioFeatures", back_populates="parentTrack", uselist=False)
    audioAnalysis = relationship("AudioAnalysis", back_populates="parentTrack", uselist=False)

class PlayHistory(Base):
    __tablename__ = 'play_history'

    id = Column('id', Integer, primary_key=True) 
    track_obj = Column(JSONB, nullable=False)
    played_at = Column(DateTime, nullable=False)
    context_obj = Column(JSONB, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    fulltrack_id = Column(Integer, ForeignKey('tracks.id'))
    from_artist = Column(Integer, ForeignKey('artists.id'))
    from_playlist = Column(Integer, ForeignKey('playlists.id'))
    from_album = Column(Integer, ForeignKey('albuns.id'))
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)
    #relationships
    parentUser = relationship("User", back_populates="playHistory")
    fullTrack = relationship("FullTrack", back_populates="played")
    fromAlbum = relationship("FullAlbum", back_populates="played")
    fromPlaylist = relationship("FullPlaylist", back_populates="played")
    fromArtist = relationship("FullArtist", back_populates="played")    

class AudioFeatures(Base):
    __tablename__ = 'audio_features'    

    id = Column('id', Integer, primary_key=True)
    feature_obj = Column(JSONB, nullable=False)
    fulltrack_id = Column(Integer, ForeignKey('tracks.id'), nullable=False, unique=True)
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)

    parentTrack = relationship("FullTrack", back_populates="audioFeatures")        

class AudioAnalysis(Base):
    __tablename__ = 'audio_analysis'    

    id = Column('id', Integer, primary_key=True)
    analysis_obj = Column(JSONB, nullable=False)
    fulltrack_id = Column(Integer, ForeignKey('tracks.id'), nullable=False, unique=True)
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)  

    parentTrack = relationship("FullTrack", back_populates="audioAnalysis")      

class FullArtist(Base):
    __tablename__ = 'artists'
    id = Column('id', Integer, primary_key=True)
    fullartist_obj = Column(JSONB, nullable=False)
    spot_id = Column(String(1024), unique=True, index=True, nullable=False)
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)    

    played = relationship("PlayHistory", back_populates="fromArtist")    

class FullPlaylist(Base):
    __tablename__ = 'playlists'
    id = Column('id', Integer, primary_key=True)
    fullplaylist_obj = Column(JSONB, nullable=False)
    spot_id = Column(String(1024), unique=True, index=True, nullable=False)
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)    

    played = relationship("PlayHistory", back_populates="fromPlaylist")    

class FullAlbum(Base):
    __tablename__ = 'albuns'
    id = Column('id', Integer, primary_key=True)
    fullalbum_obj = Column(JSONB, nullable=False)
    spot_id = Column(String(1024), unique=True, index=True, nullable=False)
    retrieved_at = Column(DateTime, server_default=func.now(), nullable=False)    

    played = relationship("PlayHistory", back_populates="fromAlbum")