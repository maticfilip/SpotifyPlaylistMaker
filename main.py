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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Playlist Creator")
        self.geometry("1280x720")
        self.configure(fg_color="#0d0d0d")

        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="#0d0d0d")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, Page1, Page2):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0d0d0d")
        self.controller = controller

        title = ctk.CTkLabel(self, text="Spotify Playlist Creator", 
                             font=("Segoe UI", 40, "bold"), text_color="#1DB954")
        title.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        btn1 = ctk.CTkButton(self, text="Chart Playlist", 
                             font=("Segoe UI", 18, "bold"), width=220,
                             command=lambda: controller.show_frame(Page1))
        btn1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        btn2 = ctk.CTkButton(self, text="AI Playlists", 
                             font=("Segoe UI", 18, "bold"), width=220,
                             command=lambda: controller.show_frame(Page2))
        btn2.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

class Page1(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0d0d0d")
        self.controller = controller
        self.sp = None

        topbar = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        topbar.pack(pady=20, padx=20, fill="x")

        back_btn = ctk.CTkButton(topbar, text="← Back", width=100, command=lambda: controller.show_frame(StartPage))
        back_btn.pack(side="right", padx=10, pady=10)

        title = ctk.CTkLabel(topbar, text="Billboard Chart Scraper", font=("Segoe UI", 26, "bold"), text_color="#1DB954")
        title.pack(side="left", padx=20, pady=10)

        frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12)
        frame.pack(pady=30, padx=40, fill="both", expand=True)

        date_label = ctk.CTkLabel(frame, text="Date (YYYY-MM-DD):", font=("Segoe UI", 14))
        date_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.date_entry = ctk.CTkEntry(frame, width=200, font=("Segoe UI", 13))
        self.date_entry.grid(row=0, column=1, padx=10, pady=10)

        self.scrape_btn = ctk.CTkButton(frame, text="Scrape Charts", command=self.on_scrape)
        self.scrape_btn.grid(row=0, column=2, padx=10, pady=10)

        self.listbox = tk.Listbox(frame, width=70, height=15, bg="#121212", fg="#1DB954", 
                                  selectbackground="#1DB954", selectforeground="black",
                                  font=("Consolas", 11))
        self.listbox.grid(row=1, column=0, columnspan=3, pady=20)

        self.playlist_btn = ctk.CTkButton(frame, text="Create Spotify Playlist", 
                                          command=self.on_create_playlist, state="disabled", width=240)
        self.playlist_btn.grid(row=2, column=0, pady=15)

        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ctk.CTkLabel(frame, textvariable=self.status_var, font=("Segoe UI", 12), text_color="#a0a0a0")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10, sticky="w")

        self.current_songs = []
        self.matched_date = None
        self.user_id = None

    def set_status(self, txt):
        self.status_var.set(txt)
        self.controller.update_idletasks()

    def on_scrape(self):
        date_str = self.date_entry.get().strip()
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return
        self.scrape_btn.configure(state="disabled")
        self.set_status("Searching...")
        t = threading.Thread(target=self.scrape_thread, args=(date_obj,), daemon=True)
        t.start()

    def scrape_thread(self, date_obj):
        matched_date, songs = core.find_nearest(date_obj)
        if matched_date and songs:
            self.current_songs = songs
            self.matched_date = matched_date
            self.controller.after(0, self.show_songs)
        else:
            self.controller.after(0, lambda: messagebox.showinfo("Info", "No chart found."))
            self.controller.after(0, lambda: self.set_status("No results"))
            self.controller.after(0, lambda: self.scrape_btn.configure(state="normal"))

    def show_songs(self):
        self.listbox.delete(0, tk.END)
        for s in self.current_songs:
            self.listbox.insert(tk.END, s)
        self.set_status(f"Found {len(self.current_songs)} songs for {self.matched_date}")
        self.playlist_btn.configure(state="normal")

    def on_create_playlist(self):
        if not self.current_songs:
            messagebox.showwarning("Warning", "No songs to add.")
            return
        self.playlist_btn.configure(state="disabled")
        self.set_status("Creating playlist...")
        t = threading.Thread(target=self.create_playlist_thread, daemon=True)
        t.start()

    def create_playlist_thread(self):
        try:
            if not self.sp:
                self.sp = core.setup_spotify()
                user = self.sp.current_user()
                self.user_id = user["id"]
            result = core.create_playlist(self.sp, self.user_id, self.matched_date, self.current_songs, public=True, description=f"Top songs from {self.matched_date}")
            if result and result.get("playlist"):
                playlist_obj = result["playlist"]
                name = playlist_obj.get("name", "Playlist")
                added = result.get("added", 0)
                not_found = result.get("not_found", [])
                msg = f"Playlist '{name}' created. Tracks added: {added}."
                if not_found:
                    msg += f" Not found: {len(not_found)}"
                self.controller.after(0, lambda: messagebox.showinfo("Success", msg))
                self.controller.after(0, lambda: self.set_status("Playlist created"))
            else:
                self.controller.after(0, lambda: messagebox.showerror("Error", "Failed to create playlist."))
                self.controller.after(0, lambda: self.set_status("Error"))
        except Exception as e:
            self.controller.after(0, lambda: messagebox.showerror("Error", f"Spotify error: {e}"))
            self.controller.after(0, lambda: self.set_status("Error"))
        finally:
            self.controller.after(0, lambda: self.playlist_btn.configure(state="normal"))

class Page2(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0d0d0d")
        self.controller = controller

        topbar = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        topbar.pack(pady=20, padx=20, fill="x")

        back_btn = ctk.CTkButton(topbar, text="← Back", width=100, command=lambda: controller.show_frame(StartPage))
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
        with open("playlist_data.csv", "w", newline="", encoding="utf-8") as file:
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
        core.loop_songs(self.sp,"short_playlist_data.csv")
        all_tracks=pd.read_csv("1msongs.csv")
        playlist_tracks=pd.read_csv("formatted_features.csv")
        recommendations = core.recommend(all_tracks, playlist_tracks, top_n=25)
        recommendations.to_csv("recommended_tracks.csv", index=False, encoding="utf-8-sig")
        recommended_songs=pd.read_csv("recommended_tracks.csv")
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
        tracks_info = pd.read_csv("tracks_info.csv")
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

app = App()
app.mainloop()
