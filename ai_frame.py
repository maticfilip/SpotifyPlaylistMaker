import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import core
import threading
import csv
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth


class aiFrame(ctk.CTkFrame):
    def __init__(self, parent, controller, start_page_class):
        super().__init__(parent, fg_color="#0d0d0d")
        self.controller = controller
        self.sp=None
        self.start_page_class=start_page_class

        topbar = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        topbar.pack(pady=20, padx=20, fill="x")

        back_btn = ctk.CTkButton(topbar, text="← Back", width=100, command=lambda: controller.show_frame(self.start_page_class))
        back_btn.pack(side="right", padx=10, pady=10)

        title = ctk.CTkLabel(topbar, text="AI Playlist Generator", font=("Segoe UI", 26, "bold"), text_color="#1DB954")
        title.pack(side="left", padx=20, pady=10)

        frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12)
        frame.pack(pady=30, padx=40, fill="both", expand=True)

        label_api = ctk.CTkLabel(frame, text="Connect with your Spotify API", font=("Segoe UI", 16, "bold"), text_color="#1DB954")
        label_api.grid(row=0, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(frame, text="Client ID:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_id = ctk.CTkEntry(frame, width=220)
        self.entry_id.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Client Secret:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_secret = ctk.CTkEntry(frame, width=220, show="*")
        self.entry_secret.grid(row=2, column=1, padx=5, pady=5)

        connect_btn = ctk.CTkButton(frame, text="Connect", command=self.connect_spotify, width=150)
        connect_btn.grid(row=3, column=0, columnspan=2, pady=10)

        divider = ctk.CTkLabel(frame, text="────────────── Playlists ──────────────", text_color="#1DB954", font=("Consolas", 13))
        divider.grid(row=4, column=0, columnspan=2, pady=10)

        self.entry_pl1 = ctk.CTkEntry(frame, placeholder_text="Playlist 1 URL", width=380)
        self.entry_pl1.grid(row=5, column=0, columnspan=2, pady=5)
        self.entry_pl2 = ctk.CTkEntry(frame, placeholder_text="Playlist 2 URL", width=380)
        self.entry_pl2.grid(row=6, column=0, columnspan=2, pady=5)
        self.entry_pl3 = ctk.CTkEntry(frame, placeholder_text="Playlist 3 URL", width=380)
        self.entry_pl3.grid(row=7, column=0, columnspan=2, pady=5)

        combine_btn = ctk.CTkButton(frame, text="Process Selected Playlists", command=self.process_picked_playlists)
        combine_btn.grid(row=8, column=0, columnspan=2, pady=15)

        go_btn = ctk.CTkButton(frame, text="Go Through All Playlists", command=self.loop_playlists, fg_color="#1ED760")
        go_btn.grid(row=9, column=0, columnspan=2, pady=10)

        create_btn=ctk.CTkButton(frame, text="Create a new playlist.", command=self.on_create, fg_color="#1ED760")
        create_btn.grid(row=10, column=0, columnspan=2, pady=10)

    def connect_spotify(self):
        cid = self.entry_id.get().strip()
        secret = self.entry_secret.get().strip()
        if not cid or not secret:
            messagebox.showerror("Error", "Please enter both client ID and client secret.")
            return
        try:
            sp = core.setup_spotify(client_id=cid, client_secret=secret)
            self.sp = sp
            user=sp.current_user()
            self.user_id=user["id"]
            messagebox.showinfo("Success", "Connected to Spotify!")
        except Exception as e:
            messagebox.showerror("Error", f"Spotify authentication failed: {e}")

    def loop_playlists(self):
        if not self.sp:
            messagebox.showerror("Error", "Please connect to Spotify first")
            return
        try:
            user = self.sp.current_user()
            playlists = []
            results = self.sp.current_user_playlists()
            while results:
                playlists.extend(results["items"])
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break
            for pl in playlists:
                print(f"- {pl['name']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
        with open("data/playlist_data.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["playlist_name","track_name","artist_name","album_name","track_url"])
            for pl in playlists:
                playlist_name = pl["name"]
                playlist_id = pl["id"]
                results = self.sp.playlist_items(playlist_id)
                tracks = results["items"]
                while results["next"]:
                    results = self.sp.next(results)
                    tracks.extend(results["items"])
                for item in tracks:
                    track = item.get("track")
                    if not track:
                        continue
                    track_name = track["name"]
                    artists=track.get("artists", [])
                    if artists:
                        artist_name=", ".join([a["name"] for a in artists])
                    else:
                        artist_name=""
                    album_name = track["album"]["name"]
                    track_url = track.get("external_urls", {}).get("spotify", "")
                    writer.writerow([playlist_name, track_name,artist_name, album_name, track_url])
            messagebox.showinfo("Success", "Playlist data saved to CSV.")

    def process_picked_playlists(self):
        if not self.sp:
            messagebox.showerror("Error", "Please connect to Spotify first")
            return
        playlist_urls = [
            self.entry_pl1.get().strip(),
            self.entry_pl2.get().strip(),
            self.entry_pl3.get().strip()
        ]
        if not any(playlist_urls):
            messagebox.showwarning("Warning", "Please enter at least one playlist URL")
            return
        try:
            core.loop_picked_playlists(self.sp, playlist_urls)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process playlists: {e}")
        core.loop_songs(self.sp,"data/short_playlist_data.csv")
        all_tracks=pd.read_csv("data/1msongs.csv")
        playlist_tracks=pd.read_csv("data/formatted_features.csv")
        recommendations = core.recommend(all_tracks, playlist_tracks, top_n=25)
        recommendations.to_csv("data/recommended_tracks.csv", index=False, encoding="utf-8-sig")
        recommended_songs=pd.read_csv("data/recommended_tracks.csv")
        core.get_song_names(recommended_songs)

    def on_create(self):
        name_dialog=ctk.CTkInputDialog(text="Enter the name for your playlist:",title="Playlist Name")
        playlist_name=name_dialog.get_input()

        if not playlist_name:
            messagebox.showwarning("Warning", "You must enter a playlist name.")
            return

        t=threading.Thread(target=self.create_new,args=(playlist_name,), daemon=True)
        t.start()

    
    def create_new(self, playlist_name):
        tracks_info = pd.read_csv("data/tracks_info.csv")
        if not self.sp:
                self.sp = core.setup_spotify()
                user = self.sp.current_user()
                self.user_id = user["id"]
        result=core.recommended_playlist(self.sp, tracks_info, playlist_name, self.user_id, public=True)
        if result and result.get("playlist"):
                playlist_obj = result["playlist"]
                name = playlist_obj.get("name", "Playlist")
                added = result.get("added", 0)
                not_found = result.get("not_found", [])
                msg = f"Playlist '{name}' created. Tracks added: {added}."
                if not_found:
                    msg += f"Not found: {len(not_found)}"
                    self.after(0, lambda: messagebox.showinfo("Success", msg))
                else:
                    self.after(0, lambda: messagebox.showinfo("Success", "Playlist has been added to your Spotify account."))
