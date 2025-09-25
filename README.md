# Sephire - Spotify Analytics with ML

A personal Spotify analytics platform combining **FastAPI** for data serving and **Jupyter notebooks** for machine learning experiments.

## What it Does

**Data Pipeline:**
- **FastAPI Server**: Authenticates with Spotify, serves your music data via REST API
- **Jupyter Notebooks**: Analyzes patterns, trains ML models, creates predictions
- **Real-time Integration**: Notebooks fetch live data from your own API

**Analytics Features:**
- Music taste analysis (genres, popularity, discovery level)
- Top tracks and artists breakdown
- ML-powered music recommendations (coming soon)
- Listening pattern predictions (coming soon)

## Architecture

```
Spotify API → FastAPI (Data Server) → Jupyter (ML Lab) → Trained Models
     ↓              ↓                        ↓              ↓
Your Music → REST Endpoints → pandas/numpy → Predictions
```

## Setup

### 1. Clone and Install
```bash
git clone <your-repo-url>
cd sephire
conda create -n sephire python=3.11
conda activate sephire
pip install -r requirements.txt
```

### 2. Spotify API Setup
1. Go to [developer.spotify.com](https://developer.spotify.com/)
2. Create a new app
3. Get your Client ID and Client Secret
4. Set redirect URI: `http://127.0.0.1:8000/callback`

### 3. Environment Configuration
Create `.env` file:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

### 4. Create Data Directories
```bash
mkdir notebooks data ml_models
mkdir data/raw data/processed
```

## Usage

### Start the Data Server
```bash
# Terminal 1: FastAPI server
conda activate sephire
python main.py
# Server runs on http://127.0.0.1:8000
```

### Authenticate with Spotify
1. Visit `http://127.0.0.1:8000/login`
2. Login with your Spotify account
3. Authorize the application

### Start Jupyter Lab
```bash
# Terminal 2: Jupyter for analysis
conda activate sephire
jupyter lab
# Opens at http://localhost:8888
```

### Run Analysis
1. Open `notebooks/01_data_exploration.ipynb`
2. Run cells to fetch and analyze your Spotify data
3. Create new notebooks for ML experiments

## Project Structure

```
sephire/
├── main.py                 # FastAPI server (data endpoints)
├── models.py               # Pydantic data models
├── notebooks/              # Jupyter ML experiments
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_ml_models.ipynb
├── data/                   # Data storage
│   ├── raw/               # Raw API responses
│   └── processed/         # Cleaned datasets
├── ml_models/             # Trained model artifacts
├── requirements.txt       # Python dependencies
├── .env                   # Spotify credentials (gitignored)
└── README.md             # This file
```

## API Endpoints

### Core Endpoints
- `GET /` - Welcome message and status
- `GET /health` - Service health check
- `GET /login` - Initiate Spotify OAuth

### Data Endpoints
- `GET /my-profile` - User profile information
- `GET /top-tracks?limit=50` - Your top tracks
- `GET /top-artists?limit=50` - Your top artists
- `GET /my-stats` - Comprehensive music statistics

### Example Usage in Jupyter
```python
import requests
import pandas as pd

# Fetch your data
response = requests.get("http://127.0.0.1:8000/top-tracks?limit=50")
data = response.json()

# Convert to DataFrame for analysis
df = pd.DataFrame(data['tracks'])
print(f"Found {len(df)} tracks to analyze!")

# Your analysis here...
```

## ML Workflow

### 1. Data Collection (FastAPI)
- Spotify OAuth authentication
- Real-time data fetching
- Structured JSON responses

### 2. Data Analysis (Jupyter)
- pandas for data manipulation
- numpy for numerical computations
- matplotlib/seaborn for visualization

### 3. Model Training (Jupyter)
- scikit-learn for ML algorithms
- Feature engineering experiments
- Model evaluation and selection

### 4. Model Integration (FastAPI + Jupyter)
- Save trained models with joblib
- Load models in FastAPI for predictions
- Real-time ML-powered endpoints

## Tech Stack

**Backend:** FastAPI, Uvicorn
**Data Science:** pandas, numpy, scikit-learn
**Visualization:** matplotlib, seaborn, plotly
**ML Environment:** Jupyter Lab, conda
**External API:** Spotify Web API

Your Spotify data never leaves your computer!

---
