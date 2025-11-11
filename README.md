# Spotify Top Charts Playlist Creator

This Python app was first only a way for you to create a Spotify playlist from historical album charts scraped from [MusicChartsArchive.com](https://musicchartsarchive.com). Simply provide a date, and the script will find the closest available chart and add the top songs to a new Spotify playlist. But, I had an idea that there was some potential here to create a smarter playlist creator. By using Spotify API and ReccoBeats API I am extracting users playlists, the playlist audio features and using that data to recommend new songs to the user and create a playlist. 


## Features

- Scrapes album charts for a specific date.
- Finds the nearest available chart if the exact date is unavailable.
- Searches for songs on Spotify and creates a new playlist with available tracks.
- Handles both public and private playlists.
- 

## Requirements

- Python 3.8+
- Libraries: `requests`, `beautifulsoup4`, `spotipy`
