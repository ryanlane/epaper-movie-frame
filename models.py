from sqlalchemy import Boolean, Column, Integer, String, DateTime
from database import Base

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    video_path = Column(String)
    time_per_frame = Column(Integer)
    skip_frames = Column(Integer)
    current_frame = Column(Integer)
    total_frames = Column(Integer)
    isRandom = Column(Boolean)
    isActive = Column(Boolean)
    started_at = Column(DateTime)
    last_updated = Column(DateTime)

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    VideoRootPath = Column(String)
    Resolution = Column(String)
    