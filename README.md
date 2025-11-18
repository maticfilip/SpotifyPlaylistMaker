# Spotify Playlist Creator

Smart music reccomender driven by a cosine similarity algorithm implemented on audio features from Spotify tracks. Currently using Spotify API to get user playlist info so the algorithm can create a vector with users audio features preference for later recommendations. ReccoBeats API is implemented to get audio features for each track in the playlist, and I will try to create a personal audio feature extractor so I can get rid of the API for better scalability. 
This is a simple desktop app implemented using Tkinter GUI for Python.
The data used is 1msongs.csv (lost the link, will add).

The audio features currently being used are: 'acousticness', 'danceabilitiy', 'duration_ms', 'energy', 'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'speechiness', 'tempo', 'time_signature', 'valence'.
Currently experimenting with other features like genre, popularity, release date and similar for optimal results.

Except the AI driven playlist, app has an option to generate playlist based on top charts from history. Simply provide the app with a date from the history, and in your Spotify library you will get a playlist with songs top charting from that week. The data is being scraped from https://musicchartsarchive.com/ 


## Features

- Using ReccoBeats API to understand users preference
- Using Spotify API to connect to the users playlists and library
- Combining multiple users playlists, or going through all of them to understand the users preferences ( it is recommended to only input 1-3 playlists with similar genres for better recommendations)
- Implementing advanced mathemathical methods to find tracks similar to already existing playlists
- Handles both public and private playlists
- Creating playlists directly into your Spotify library




## Requirements

The most important requirement is the Spotify API client ID and client secret that are easily obtained https://developer.spotify.com/documentation/web-api. The user data isn't being stored for safety reasons, so after every restart you need to provide the information to the app again. Later on hashing the data will be implemented so it is easier to use the app every time. 

- Python 3.8+
- Libraries: `requests`, `beautifulsoup4`, `spotipy`,`pandas`,`time`,`tkinter`,`csv`,`ast`,`sklearn`,`datetime`,`customtkinter`,`threading`
- Necessessary data will be uploaded after perfecting the algorithm


