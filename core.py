from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, date
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from tkinter import ttk,messagebox


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