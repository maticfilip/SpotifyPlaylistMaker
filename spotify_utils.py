from imports import *

CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://127.0.0.1:8888/callback"



def setup_spotify(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    scope = "playlist-modify-public playlist-modify-private user-library-read playlist-read-private playlist-read-collaborative"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=scope
    ))
    return sp



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
        with open("data/short_playlist_data.csv", "w", newline="", encoding="utf-8") as file:
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

def recommended_playlist(sp, tracks_info, name, user_id, public=True):
    
    if isinstance(tracks_info, pd.DataFrame):
        df = tracks_info.copy()
    else:
        df = pd.read_csv(tracks_info)

    queries = (df["trackTitle"].astype(str) + " " + df["artists"].astype(str)).tolist()


    playlist_desc=f"A playlist created by @app."

    playlist=sp.user_playlist_create(
        user=user_id,
        name=name,
        description=playlist_desc,
        public=public
    )

    track_uris=[]
    not_found=[]
    for q in queries:
        uri=_search_track_uri(sp, q)
        if uri:
            track_uris.append(uri)
        else:
            not_found.append(q)

    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris[i:i+100])

    return {"playlist": playlist, "added": len(track_uris), "not_found": not_found}
