import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict, List, Tuple, Any
from collections import Counter
import io
import base64
from datetime import datetime, timedelta

class SpotifyAnalytics:
    """
    Data analysis engine for Spotify listening habits
    Using Pandas for data manipulation and NumPy for calculations
    """

    def __init__(self):
        self.tracks_df = None
        self.artists_df = None

    def load_tracks_data(self, tracks_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert Spotify tracks data to Pandas DataFrame for analysis
        """
        # Extract relevant fields and create DataFrame
        processed_tracks = []

        for track in tracks_data:
            processed_tracks.append({
                'name': track['name'],
                'artist': track['artist'],
                'album': track['album'],
                'popularity': track['popularity'],
                'duration_ms': track['duration_ms'],
                'duration_minutes': track['duration_ms'] / (1000 * 60),  # Convert to minutes
                'has_preview': track['preview_url'] is not None
            })

        self.tracks_df = pd.DataFrame(processed_tracks)
        return self.tracks_df

    def load_artists_data(self, artists_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert Spotify artists data to Pandas DataFrame for analysis
        """
        # Flatten genres for easier analysis
        processed_artists = []

        for artist in artists_data:
            processed_artists.append({
                'name': artist['name'],
                'popularity': artist['popularity'],
                'followers': artist['followers'],
                'genre_count': len(artist['genres']),
                'genres': artist['genres']  # Keep as list for detailed analysis
            })

        self.artists_df = pd.DataFrame(processed_artists)
        return self.artists_df

    def get_listening_patterns(self) -> Dict[str, Any]:
        """
        Analyze listening patterns using Pandas aggregations
        """
        if self.tracks_df is None:
            raise ValueError("No tracks data loaded")

        # Use Pandas for statistical analysis
        stats = {
            'total_tracks': len(self.tracks_df),
            'avg_popularity': self.tracks_df['popularity'].mean(),
            'popularity_std': self.tracks_df['popularity'].std(),
            'avg_duration_minutes': self.tracks_df['duration_minutes'].mean(),
            'total_listening_hours': self.tracks_df['duration_minutes'].sum() / 60,
            'popularity_distribution': {
                'mainstream': len(self.tracks_df[self.tracks_df['popularity'] >= 70]),
                'moderate': len(self.tracks_df[(self.tracks_df['popularity'] >= 40) &
                                             (self.tracks_df['popularity'] < 70)]),
                'niche': len(self.tracks_df[self.tracks_df['popularity'] < 40])
            }
        }

        return stats

    def analyze_genre_diversity(self) -> Dict[str, Any]:
        """
        Advanced genre analysis using Pandas and NumPy
        """
        if self.artists_df is None:
            raise ValueError("No artists data loaded")

        # Flatten all genres from all artists
        all_genres = []
        for genres_list in self.artists_df['genres']:
            all_genres.extend(genres_list)

        # Use Counter for frequency analysis
        genre_counts = Counter(all_genres)

        # Calculate diversity metrics using NumPy
        genre_frequencies = np.array(list(genre_counts.values()))

        diversity_metrics = {
            'unique_genres': len(genre_counts),
            'total_genre_instances': len(all_genres),
            'avg_genres_per_artist': self.artists_df['genre_count'].mean(),
            'genre_concentration': self._calculate_herfindahl_index(genre_frequencies),
            'top_genres': dict(genre_counts.most_common(10)),
            'genre_distribution_stats': {
                'mean_frequency': float(np.mean(genre_frequencies)),
                'std_frequency': float(np.std(genre_frequencies)),
                'max_frequency': int(np.max(genre_frequencies)),
                'min_frequency': int(np.min(genre_frequencies))
            }
        }

        return diversity_metrics

    def _calculate_herfindahl_index(self, frequencies: np.ndarray) -> float:
        """
        Calculate Herfindahl-Hirschman Index for diversity measurement
        Lower values = more diverse, Higher values = more concentrated
        """
        if len(frequencies) == 0:
            return 0.0

        # Calculate market shares (percentages)
        total = np.sum(frequencies)
        shares = frequencies / total

        # HHI = sum of squared market shares
        hhi = np.sum(shares ** 2)

        return float(hhi)

    def get_popularity_insights(self) -> Dict[str, Any]:
        """
        Analyze popularity patterns using statistical methods
        """
        if self.tracks_df is None or self.artists_df is None:
            raise ValueError("Missing data for analysis")

        # Track popularity analysis
        track_pop_quartiles = self.tracks_df['popularity'].quantile([0.25, 0.5, 0.75])

        # Artist popularity analysis
        artist_pop_quartiles = self.artists_df['popularity'].quantile([0.25, 0.5, 0.75])

        # Correlation between track and artist popularity would need more complex data

        insights = {
            'track_popularity': {
                'quartiles': {
                    'q1': float(track_pop_quartiles[0.25]),
                    'median': float(track_pop_quartiles[0.5]),
                    'q3': float(track_pop_quartiles[0.75])
                },
                'discovery_score': self._calculate_discovery_score(self.tracks_df['popularity'])
            },
            'artist_popularity': {
                'quartiles': {
                    'q1': float(artist_pop_quartiles[0.25]),
                    'median': float(artist_pop_quartiles[0.5]),
                    'q3': float(artist_pop_quartiles[0.75])
                },
                'avg_followers': int(self.artists_df['followers'].mean())
            }
        }

        return insights

    def _calculate_discovery_score(self, popularity_series: pd.Series) -> float:
        """
        Calculate how much user discovers new/underground music
        Score: 0-100 (higher = more mainstream taste)
        """
        avg_popularity = popularity_series.mean()
        return float(avg_popularity)

    def create_popularity_chart(self) -> str:
        """
        Create popularity distribution chart using Matplotlib
        Returns base64 encoded PNG
        """
        if self.tracks_df is None:
            raise ValueError("No tracks data for visualization")

        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Chart 1: Popularity histogram
        ax1.hist(self.tracks_df['popularity'], bins=20, alpha=0.7, color='#1db954', edgecolor='black')
        ax1.set_xlabel('Popularity Score')
        ax1.set_ylabel('Number of Tracks')
        ax1.set_title('Track Popularity Distribution')
        ax1.grid(True, alpha=0.3)

        # Chart 2: Duration vs Popularity scatter
        ax2.scatter(self.tracks_df['duration_minutes'], self.tracks_df['popularity'],
                   alpha=0.6, color='#1db954')
        ax2.set_xlabel('Duration (minutes)')
        ax2.set_ylabel('Popularity Score')
        ax2.set_title('Duration vs Popularity')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')

    def create_genre_chart(self) -> str:
        """
        Create genre distribution pie chart using Matplotlib
        Returns base64 encoded PNG
        """
        if self.artists_df is None:
            raise ValueError("No artists data for visualization")

        # Get genre data
        all_genres = []
        for genres_list in self.artists_df['genres']:
            all_genres.extend(genres_list)

        genre_counts = Counter(all_genres)
        top_genres = dict(genre_counts.most_common(8))

        if not top_genres:
            raise ValueError("No genre data available")

        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))

        # Fix: Get colormap properly and convert to list of colors
        cmap = plt.cm.get_cmap('Set3')
        colors = [cmap(i) for i in np.linspace(0, 1, len(top_genres))]

        # Fix: Handle optional autopct return value
        pie_result = ax.pie(
            list(top_genres.values()),  # Fix: Convert dict_values to list
            labels=list(top_genres.keys()),  # Fix: Convert dict_keys to list
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )

        # Fix: Handle variable unpacking based on what's returned
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            # Improve text readability
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        else:
            wedges, texts = pie_result

        ax.set_title('Top Music Genres Distribution', fontsize=16, fontweight='bold')

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')
