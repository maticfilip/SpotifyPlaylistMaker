from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth


CLIENT_ID="e62d23f3e70e4d4281559724ebde8c2b"
CLIENT_SECRET="9d465f3d876c4e0dbc7e7ab181101fee"
REDIRECT_URI="http://127.0.0.1:8888/callback"

scope = "playlist-modify-public playlist-modify-private user-library-read"

sp=spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
))

user=sp.current_user()
print(f"{user['display_name']}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://musicchartsarchive.com/album-chart/"

user_input = input("What date would you like to listen to? (YYYY-MM-DD) ")

try:
    start_date = datetime.strptime(user_input, "%Y-%m-%d").date()
except ValueError:
    print("Invalid date format.")
    exit()

def fetch_page(date):
    url = f"{BASE_URL}{date}/"
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

def get_valid_chart_page(date):
    status, html = fetch_page(date)
    if status != 200:
        return None, None

    songs = extract_songs_from_html(html)
    if songs:
        print(f"✅ Page for {date} contains {len(songs)} song(s).")
        return html, songs

    return None, None

def find_nearest(date, daily_window=7, weekly_weeks=52, pause=0.2):
    for d in range(daily_window):
        candidate = date - timedelta(days=d)
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate, songs
        time.sleep(pause)

    candidate = date - timedelta(days=daily_window)
    for w in range(weekly_weeks):
        candidate -= timedelta(days=7)  
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate, songs
        time.sleep(pause)

    return None, None

matched_date, songs = find_nearest(start_date)
if not matched_date:
    print("No chart found within search limits.")
    exit()

songs_for_playlist=[]
print(f"Showing chart for {matched_date}")
for s in songs:
    print(s)
    songs_for_playlist.append(s)

#playlist

playlist_name=f"Top Charts from {matched_date}"
playlist_desc=f"Top songs from {matched_date} scraped from MusicChartsArchive.com"

playlist=sp.user_playlist_create(
    user=user["id"],
    name=playlist_name,
    public=True,
    description=playlist_desc
)

track_uris=[]

for song in songs_for_playlist:
    try:
        results=sp.search(q=song,type="track",limit=1)
        items=results["tracks"]["items"]

        if items:
            uri=items[0]["uri"]
            track_uris.append(uri)
        else:
            print(f"Not found {song}.")
    except Exception as e:
        print(f"Error:{e}")

if track_uris:
    for i in range(0,len(track_uris),100):
        sp.playlist_add_items(playlist_id=playlist["id"],items=track_uris[i:i+100])
else:
    print(f"No valid tracks found to add.")