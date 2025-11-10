from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, date
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from tkinter import ttk,messagebox
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv


CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://127.0.0.1:8888/callback"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://musicchartsarchive.com/album-chart/"

def setup_spotify(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    scope = "playlist-modify-public playlist-modify-private user-library-read playlist-read-private playlist-read-collaborative"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=scope
    ))
    return sp

def _format_date_for_url(d):
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    raise ValueError("date must be a str or datetime/date object")

def fetch_page(date_input):
    date_str = _format_date_for_url(date_input)
    url = f"{BASE_URL}{date_str}/"
    res = requests.get(url, headers=HEADERS, timeout=15)
    return res.status_code, res.text

def extract_songs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find(id="content") or soup
    view = main.find(class_="view-chart-albums")
    container = view if view else main

    songs = []

    for tr in container.find_all("tr", class_=["odd", "even"]):
        a = tr.find("a")
        if a:
            txt = a.get_text(strip=True)
            if txt:
                songs.append(txt)

    if not songs:
        table = container.find("table")
        if table:
            for tr in table.find_all("tr"):
                a = tr.find("a")
                if a:
                    txt = a.get_text(strip=True)
                    if txt:
                        songs.append(txt)

    if not songs:
        for a in container.find_all("a"):
            txt = a.get_text(strip=True)
            if txt and len(txt) > 2 and not txt.lower().startswith(("read", "view", "more")):
                songs.append(txt)

    seen = set()
    filtered = []
    for s in songs:
        if s not in seen:
            seen.add(s)
            filtered.append(s)
    return filtered

def get_valid_chart_page(date_input):
    status, html = fetch_page(date_input)
    if status != 200:
        return None, None

    songs = extract_songs_from_html(html)
    if songs:
        return html, songs
    return None, None

def find_nearest(date_input, daily_window=7, weekly_weeks=52, pause=0.2):
    if isinstance(date_input, str):
        try:
            base = datetime.strptime(date_input, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date string must be in YYYY-MM-DD format")
    elif isinstance(date_input, datetime):
        base = date_input.date()
    elif isinstance(date_input, date):
        base = date_input
    else:
        raise ValueError("date_input must be a str or datetime/date")

    for d in range(daily_window):
        candidate = base - timedelta(days=d)
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate.isoformat(), songs
        time.sleep(pause)

    candidate = base - timedelta(days=daily_window)
    for w in range(weekly_weeks):
        candidate -= timedelta(days=7)
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate.isoformat(), songs
        time.sleep(pause)

    return None, None

def _search_track_uri(sp, query):
    try:
        results = sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]["uri"]
    except Exception:
        return None
    return None

def create_playlist(sp, user_id, date_str, songs_list, public=True, description=None):
    playlist_name = f"Top Charts from {date_str}"
    playlist_desc = description or f"Top songs from {date_str} scraped from MusicChartsArchive.com"

    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=public,
        description=playlist_desc
    )

    track_uris = []
    not_found = []
    for song in songs_list:
        uri = _search_track_uri(sp, song)
        if uri:
            track_uris.append(uri)
        else:
            not_found.append(song)

    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris[i:i+100])

    return {"playlist": playlist, "added": len(track_uris), "not_found": not_found}

def check_spotify_credentials(client_id, client_secret):
    if not client_id or not client_secret:
        messagebox.showwarning("Warning", "Please enter both client_id and client_secret.")
        return None

    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        token_info = auth_manager.get_access_token(as_dict=False)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        messagebox.showinfo("Success", "Successfully connected to Spotify API!")
        return sp 
    except Exception as e:
        messagebox.showerror("Error", f"Invalid credentials: {e}")
        return None
    
def loop_picked_playlists(sp, playlist_urls):
    if not sp:
        messagebox.showerror("Error", "Please connect to Spotify first")
        return
    try:
        user=sp.current_user()
        playlists = []
        for url in playlist_urls:
            if not url: 
                continue
            playlist_id = url.split("/")[-1].split("?")[0]
            playlists.append(playlist_id)
        with open("short_playlist_data.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["track_name", "artist_name", "album_name", "track_url","track_id"])
                for playlist_id in playlists:
                    try:
                        pl = sp.playlist(playlist_id)
                        results = sp.playlist_items(playlist_id)
                        tracks = results["items"]
                        while results["next"]:
                            results = sp.next(results)
                            tracks.extend(results["items"])
                        for item in tracks:
                            track = item.get("track")
                            if not track:
                                continue
                            track_name = track["name"]
                            artists = track.get("artists", [])
                            artist_name = ", ".join([a["name"] for a in artists])
                            album_name = track["album"]["name"]
                            track_url = track.get("external_urls", {}).get("spotify", "")
                            track_id=track["id"]
                            writer.writerow([track_name, artist_name, album_name, track_url,track_id])
                    except Exception as e:
                        print(f"Error processing playlist {playlist_id}: {e}")
                        
        messagebox.showinfo("Success", "Playlist data saved to playlist_data.csv")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process playlists: {e}")



def loop_songs(sp, csv_path="short_playlist_data.csv", output_csv="formatted_features.csv"):
    all_features = []
    base = "https://api.reccobeats.com/v1/audio-features"
    df = pd.read_csv(csv_path)
    track_ids = df["track_id"].tolist()
    r = requests.get(base, params={"ids": track_ids})
    r.raise_for_status()
    data = r.json()
    
    if isinstance(data, dict):
        if "audio_features" in data:
            features_list = data["audio_features"]
        elif "features" in data:
            features_list = data["features"]
        elif "data" in data:
            features_list = data["data"]
        elif "items" in data:
            features_list = data["items"]
        else:
            features_list = list(data.values())[0] if data else []
    elif isinstance(data, list):
        features_list = data
    else:
        features_list = []
    
    print("Type of features_list:", type(features_list))
    print("Length:", len(features_list) if isinstance(features_list, list) else "N/A")
    
    features_df = pd.DataFrame(features_list)
    
    column_order = ["id", "href", "danceability", "energy", "key", "loudness", 
                    "mode", "speechiness", "acousticness", "instrumentalness", 
                    "liveness", "valence", "tempo"]
    
    existing_columns = [col for col in column_order if col in features_df.columns]
    if existing_columns:
        remaining = [col for col in features_df.columns if col not in existing_columns]
        features_df = features_df[existing_columns + remaining]
    
    features_df.to_csv(output_csv, index=False)
    
    print(features_df.head())
    
    return features_df