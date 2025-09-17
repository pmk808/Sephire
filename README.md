# Sephire

A simple app to analyze your Spotify listening habits.

## What it does

Connects to your Spotify account and shows you stats about your music taste like your top songs, favorite genres, and when you listen to music most.

## Setup

1. Clone this repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate`
4. Install stuff: `pip install -r requirements.txt`
5. Get Spotify API credentials from developer.spotify.com
6. Create a `.env` file with your credentials:
   ```
   SPOTIFY_CLIENT_ID=your_id_here
   SPOTIFY_CLIENT_SECRET=your_secret_here
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
   ```
7. Run it: `python main.py`

## Tech used

- FastAPI for the web stuff
- Pandas for handling data
- NumPy for calculations
- Matplotlib for charts

## Note

This is a learning project to practice Python libraries. Your Spotify data stays on your computer.