from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import os
import requests
import base64
import secrets
from dotenv import load_dotenv
from urllib.parse import urlencode
from typing import Dict, Optional, List
from collections import Counter

# Import our Pydantic models
from models import (
    WelcomeResponse, HealthResponse, AuthSuccessResponse,
    UserProfileResponse, TopTracksResponse, TopArtistsResponse,
    UserStatsResponse, UserToken, TimeRange, DiscoveryLevel,
    Track, Artist, UserProfile, StatsSummary, MusicTasteProfile
)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sephire - Spotify Analytics API",
    version="1.0.0",
    description="Clean FastAPI server for Spotify data - Analysis done in Jupyter"
)

# Spotify API credentials
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID") # type: ignore
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET") # type: ignore
SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")

# Spotify API endpoints
SPOTIFY_AUTH_URL: str = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL: str = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL: str = "https://api.spotify.com/v1"

# In-memory token storage (use database in production)
user_tokens: Dict[str, UserToken] = {}

@app.get("/", response_model=WelcomeResponse)
async def welcome() -> WelcomeResponse:
    """Welcome endpoint - clean and focused"""
    return WelcomeResponse(
        message="Sephire API - Spotify Data Server for ML Analysis",
        status="running",
        endpoints={
            "login": "/login",
            "profile": "/my-profile",
            "top_tracks": "/top-tracks",
            "top_artists": "/top-artists",
            "stats": "/my-stats",
            "audio_features": "/audio-features",
            "recently_played": "/recently-played"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(status="healthy", service="sephire-api")

@app.get("/login")
async def login() -> RedirectResponse:
    """Initiate Spotify OAuth flow"""
    state: str = secrets.token_urlsafe(16)

    scopes: List[str] = [
        "user-read-private",
        "user-read-email",
        "user-top-read",
        "user-read-recently-played"
    ]

    params: Dict[str, str] = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": state
    }

    auth_url: str = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)

@app.get("/callback", response_model=AuthSuccessResponse)
async def callback(
    code: Optional[str] = None,
    error: Optional[str] = None
) -> AuthSuccessResponse:
    """Handle Spotify OAuth callback"""
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    # Exchange code for token
    auth_header: str = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    headers: Dict[str, str] = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data: Dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }

    response: requests.Response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    token_data: Dict = response.json()

    # Store token
    user_id: str = "demo_user"  # In real app, use proper user sessions
    user_tokens[user_id] = UserToken(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_in=token_data["expires_in"]
    )

    return AuthSuccessResponse(
        message="Successfully authenticated with Spotify!",
        status="logged_in",
        next_steps="Use /top-tracks, /top-artists, or /my-stats endpoints"
    )

def get_spotify_headers(user_id: str = "demo_user") -> Dict[str, str]:
    """Get headers for Spotify API requests"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated. Please visit /login first")

    access_token: str = user_tokens[user_id].access_token
    return {"Authorization": f"Bearer {access_token}"}

@app.get("/my-profile", response_model=UserProfileResponse)
async def get_user_profile() -> UserProfileResponse:
    """Get user's Spotify profile"""
    headers: Dict[str, str] = get_spotify_headers()

    response: requests.Response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch profile")

    profile_data: Dict = response.json()

    user_profile = UserProfile(
        name=profile_data.get("display_name"),
        email=profile_data.get("email"),
        country=profile_data.get("country"),
        followers=profile_data.get("followers", {}).get("total", 0),
        subscription=profile_data.get("product")
    )

    return UserProfileResponse(
        user=user_profile,
        spotify_profile=profile_data.get("external_urls", {}).get("spotify")
    )

@app.get("/top-tracks", response_model=TopTracksResponse)
async def get_top_tracks(
    limit: int = Query(default=10, ge=1, le=50, description="Number of tracks to return"),
    time_range: TimeRange = Query(default=TimeRange.MEDIUM_TERM, description="Time period")
) -> TopTracksResponse:
    """Get user's top tracks - clean data for ML analysis"""
    headers: Dict[str, str] = get_spotify_headers()

    params: Dict[str, str] = {
        "limit": str(limit),
        "time_range": time_range.value
    }

    response: requests.Response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/top/tracks",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch top tracks")

    data: Dict = response.json()

    # Process data into clean format
    tracks: List[Track] = []
    for track_data in data.get("items", []):
        track = Track(
            name=track_data["name"],
            artist=", ".join([artist["name"] for artist in track_data["artists"]]),
            album=track_data["album"]["name"],
            popularity=track_data["popularity"],
            duration_ms=track_data["duration_ms"],
            preview_url=track_data.get("preview_url"),
            spotify_url=track_data["external_urls"]["spotify"]
        )
        tracks.append(track)

    return TopTracksResponse(
        time_range=time_range.value,
        total_tracks=len(tracks),
        tracks=tracks
    )

@app.get("/top-artists", response_model=TopArtistsResponse)
async def get_top_artists(
    limit: int = Query(default=10, ge=1, le=50, description="Number of artists to return"),
    time_range: TimeRange = Query(default=TimeRange.MEDIUM_TERM, description="Time period")
) -> TopArtistsResponse:
    """Get user's top artists - clean data for ML analysis"""
    headers: Dict[str, str] = get_spotify_headers()

    params: Dict[str, str] = {
        "limit": str(limit),
        "time_range": time_range.value
    }

    response: requests.Response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/top/artists",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch top artists")

    data: Dict = response.json()

    # Process data into clean format
    artists: List[Artist] = []
    for artist_data in data.get("items", []):
        artist = Artist(
            name=artist_data["name"],
            genres=artist_data["genres"],
            popularity=artist_data["popularity"],
            followers=artist_data["followers"]["total"],
            spotify_url=artist_data["external_urls"]["spotify"]
        )
        artists.append(artist)

    return TopArtistsResponse(
        time_range=time_range.value,
        total_artists=len(artists),
        artists=artists
    )

@app.get("/my-stats", response_model=UserStatsResponse)
async def get_user_stats() -> UserStatsResponse:
    """Get basic user statistics - detailed analysis done in Jupyter"""
    headers: Dict[str, str] = get_spotify_headers()

    # Get data for basic stats
    tracks_response: requests.Response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/top/tracks?limit=50&time_range=medium_term",
        headers=headers
    )
    artists_response: requests.Response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/top/artists?limit=50&time_range=medium_term",
        headers=headers
    )

    if tracks_response.status_code != 200 or artists_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch data for stats")

    tracks_data: Dict = tracks_response.json()
    artists_data: Dict = artists_response.json()

    # Basic genre analysis
    all_genres: List[str] = []
    for artist in artists_data.get("items", []):
        all_genres.extend(artist.get("genres", []))

    genre_counts: Counter = Counter(all_genres)
    top_genres: Dict[str, int] = dict(genre_counts.most_common(10))

    # Basic popularity stats
    track_popularities: List[int] = [track["popularity"] for track in tracks_data.get("items", [])]
    avg_track_popularity: float = sum(track_popularities) / len(track_popularities) if track_popularities else 0.0

    artist_popularities: List[int] = [artist["popularity"] for artist in artists_data.get("items", [])]
    avg_artist_popularity: float = sum(artist_popularities) / len(artist_popularities) if artist_popularities else 0.0

    # Basic listening time
    total_duration_ms: int = sum(track["duration_ms"] for track in tracks_data.get("items", []))
    total_hours: float = round(total_duration_ms / (1000 * 60 * 60), 2)

    # Discovery level
    if avg_track_popularity < 50:
        discovery_level = DiscoveryLevel.HIGH
    elif avg_track_popularity < 70:
        discovery_level = DiscoveryLevel.MEDIUM
    else:
        discovery_level = DiscoveryLevel.MAINSTREAM

    # Build response
    summary = StatsSummary(
        total_top_tracks=len(tracks_data.get("items", [])),
        total_top_artists=len(artists_data.get("items", [])),
        unique_genres=len(set(all_genres)),
        avg_track_popularity=round(avg_track_popularity, 1),
        avg_artist_popularity=round(avg_artist_popularity, 1),
        estimated_listening_hours=total_hours
    )

    music_taste_profile = MusicTasteProfile(
        diversity_score=len(set(all_genres)),
        mainstream_factor=round(avg_track_popularity, 1),
        discovery_level=discovery_level
    )

    return UserStatsResponse(
        summary=summary,
        top_genres=top_genres,
        music_taste_profile=music_taste_profile
    )

@app.get("/audio-features")
async def get_audio_features(limit: int = Query(default=20, ge=1, le=30)) -> Dict:
    """Get audio features + popularity scores for ML analysis - FIXED for 403 errors"""

    headers: Dict[str, str] = get_spotify_headers()

    # Get top tracks
    tracks_response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/top/tracks?limit={limit}&time_range=medium_term",
        headers=headers
    )

    if tracks_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch tracks")

    tracks_data = tracks_response.json()
    tracks = tracks_data.get("items", [])

    if not tracks:
        raise HTTPException(status_code=400, detail="No tracks found")

    track_ids = [track["id"] for track in tracks if track.get("id")]

    if not track_ids:
        raise HTTPException(status_code=400, detail="No valid track IDs found")

    # FIX: Process in smaller batches to avoid 403 errors
    batch_size = 10  # Smaller batches are more reliable
    all_audio_features = []

    print(f"🔍 Processing {len(track_ids)} tracks in batches of {batch_size}")

    for i in range(0, len(track_ids), batch_size):
        batch_ids = track_ids[i:i + batch_size]
        batch_tracks = tracks[i:i + batch_size]

        print(f"🔍 Processing batch {i//batch_size + 1}: tracks {i+1}-{min(i+batch_size, len(track_ids))}")

        try:
            # Get audio features for this batch
            ids_string = ','.join(batch_ids)
            features_response = requests.get(
                f"{SPOTIFY_API_BASE_URL}/audio-features?ids={ids_string}",
                headers=headers,
                timeout=10  # Add timeout
            )

            print(f"🔍 Batch response status: {features_response.status_code}")

            if features_response.status_code == 403:
                print("⚠️ 403 error - trying individual track requests as fallback...")

                # Fallback: Request tracks individually
                for track_id, track in zip(batch_ids, batch_tracks):
                    try:
                        single_response = requests.get(
                            f"{SPOTIFY_API_BASE_URL}/audio-features/{track_id}",
                            headers=headers,
                            timeout=5
                        )

                        if single_response.status_code == 200:
                            audio_feature = single_response.json()
                            if audio_feature:
                                combined_record = {
                                    'track_id': track['id'],
                                    'name': track['name'],
                                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                                    'popularity': track['popularity'],
                                    'danceability': audio_feature.get('danceability'),
                                    'energy': audio_feature.get('energy'),
                                    'speechiness': audio_feature.get('speechiness'),
                                    'acousticness': audio_feature.get('acousticness'),
                                    'instrumentalness': audio_feature.get('instrumentalness'),
                                    'liveness': audio_feature.get('liveness'),
                                    'valence': audio_feature.get('valence'),
                                    'tempo': audio_feature.get('tempo'),
                                    'loudness': audio_feature.get('loudness')
                                }
                                all_audio_features.append(combined_record)
                        else:
                            print(f"⚠️ Could not get features for track {track['name']}")

                    except Exception as e:
                        print(f"⚠️ Error getting individual track {track_id}: {e}")
                        continue

            elif features_response.status_code == 200:
                # Normal batch processing
                features_data = features_response.json()
                raw_audio_features = features_data.get("audio_features", [])

                for track, audio_feature in zip(batch_tracks, raw_audio_features):
                    if audio_feature is not None:
                        combined_record = {
                            'track_id': track['id'],
                            'name': track['name'],
                            'artist': ', '.join([artist['name'] for artist in track['artists']]),
                            'popularity': track['popularity'],
                            'danceability': audio_feature.get('danceability'),
                            'energy': audio_feature.get('energy'),
                            'speechiness': audio_feature.get('speechiness'),
                            'acousticness': audio_feature.get('acousticness'),
                            'instrumentalness': audio_feature.get('instrumentalness'),
                            'liveness': audio_feature.get('liveness'),
                            'valence': audio_feature.get('valence'),
                            'tempo': audio_feature.get('tempo'),
                            'loudness': audio_feature.get('loudness')
                        }
                        all_audio_features.append(combined_record)
            else:
                print(f"⚠️ Batch failed with status {features_response.status_code}")

        except Exception as e:
            print(f"⚠️ Error processing batch: {e}")
            continue

        # Small delay between batches to avoid rate limiting
        import time
        time.sleep(0.1)

    print(f"✅ Successfully processed {len(all_audio_features)} tracks")

    if not all_audio_features:
        # Last resort: return tracks with dummy audio features for testing
        print("⚠️ No audio features available - returning tracks with basic data only")
        basic_features = []
        for track in tracks[:10]:  # Just first 10 tracks
            basic_record = {
                'track_id': track['id'],
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'popularity': track['popularity'],
                # Add dummy values for ML testing
                'danceability': 0.5,
                'energy': 0.5,
                'speechiness': 0.1,
                'acousticness': 0.5,
                'instrumentalness': 0.1,
                'liveness': 0.2,
                'valence': 0.5,
                'tempo': 120.0,
                'loudness': -10.0
            }
            basic_features.append(basic_record)

        return {
            "audio_features": basic_features,
            "total_tracks": len(basic_features),
            "message": "Using basic track data with dummy audio features - audio features API unavailable",
            "warning": "Audio features are dummy values - predictions will not be accurate"
        }

    return {
        "audio_features": all_audio_features,
        "total_tracks": len(all_audio_features),
        "message": "Audio features + popularity scores ready for ML analysis",
        "processing_info": f"Successfully processed {len(all_audio_features)} out of {len(tracks)} tracks"
    }

@app.get("/recently-played")
async def get_recently_played(limit: int = Query(default=50, ge=1, le=50)) -> Dict:
    """Get recently played tracks for time-series analysis"""
    headers: Dict[str, str] = get_spotify_headers()

    response: requests.Response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/player/recently-played?limit={limit}",
        headers=headers
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch recent tracks")

    recent_data = response.json()

    # Clean format for analysis
    recent_tracks = []
    for item in recent_data.get("items", []):
        track = item["track"]
        recent_tracks.append({
            'name': track["name"],
            'artist': ", ".join([artist["name"] for artist in track["artists"]]),
            'album': track["album"]["name"],
            'duration_ms': track["duration_ms"],
            'played_at': item["played_at"],
            'popularity': track["popularity"],
            'spotify_url': track["external_urls"]["spotify"]
        })

    return {
        "recent_tracks": recent_tracks,
        "total_tracks": len(recent_tracks),
        "message": "Use this data in Jupyter for listening pattern analysis"
    }

@app.get("/track/{track_id}")
async def get_track_by_id(track_id: str) -> Dict:
    """Get specific track info by Spotify ID"""
    headers = get_spotify_headers()

    # Get track basic info
    track_response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/tracks/{track_id}",
        headers=headers
    )

    # Get audio features
    features_response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/audio-features/{track_id}",
        headers=headers
    )

    if track_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Track not found")

    track_data = track_response.json()
    features_data = features_response.json() if features_response.status_code == 200 else {}

    return {
        "track_info": {
            "name": track_data["name"],
            "artist": ", ".join([artist["name"] for artist in track_data["artists"]]),
            "album": track_data["album"]["name"],
            "popularity": track_data["popularity"],
            "duration_ms": track_data["duration_ms"],
            "spotify_url": track_data["external_urls"]["spotify"]
        },
        "audio_features": features_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
