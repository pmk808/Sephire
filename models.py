from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# Enums for better type safety
class TimeRange(str, Enum):
    SHORT_TERM = "short_term"  # Last 4 weeks
    MEDIUM_TERM = "medium_term"  # Last 6 months
    LONG_TERM = "long_term"  # All time


class DiscoveryLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    MAINSTREAM = "Mainstream"


# Core Data Models
class UserProfile(BaseModel):
    name: Optional[str]
    email: Optional[str]
    country: Optional[str]
    followers: int
    subscription: Optional[str]


class Track(BaseModel):
    name: str
    artist: str
    album: str
    popularity: int
    duration_ms: int
    preview_url: Optional[str]
    spotify_url: str


class Artist(BaseModel):
    name: str
    genres: List[str]
    popularity: int
    followers: int
    spotify_url: str


class MusicTasteProfile(BaseModel):
    diversity_score: int
    mainstream_factor: float
    discovery_level: DiscoveryLevel


class StatsSummary(BaseModel):
    total_top_tracks: int
    total_top_artists: int
    unique_genres: int
    avg_track_popularity: float
    avg_artist_popularity: float
    estimated_listening_hours: float


# API Response Models
class WelcomeResponse(BaseModel):
    message: str
    status: str
    endpoints: Dict[str, str]


class HealthResponse(BaseModel):
    status: str
    service: str


class AuthSuccessResponse(BaseModel):
    message: str
    status: str
    next_steps: str


class UserProfileResponse(BaseModel):
    user: UserProfile
    spotify_profile: Optional[str]


class TopTracksResponse(BaseModel):
    time_range: str
    total_tracks: int
    tracks: List[Track]


class TopArtistsResponse(BaseModel):
    time_range: str
    total_artists: int
    artists: List[Artist]


class UserStatsResponse(BaseModel):
    summary: StatsSummary
    top_genres: Dict[str, int]
    music_taste_profile: MusicTasteProfile


# Authentication Model
class UserToken(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
