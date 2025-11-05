# Spotify Top Charts Playlist Creator

This Python script allows you to create a Spotify playlist from historical album charts scraped from [MusicChartsArchive.com](https://musicchartsarchive.com). Simply provide a date, and the script will find the closest available chart and add the top songs to a new Spotify playlist.

## Features

- Scrapes album charts for a specific date.
- Finds the nearest available chart if the exact date is unavailable.
- Searches for songs on Spotify and creates a new playlist with available tracks.
- Handles both public and private playlists.

## Requirements

- Python 3.8+
- Libraries: `requests`, `beautifulsoup4`, `spotipy`
