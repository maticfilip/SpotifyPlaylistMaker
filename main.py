import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import core
import threading
import csv
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth

LARGEFONT = ("Verdana", 35)

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Spotify Playlist Creator")
        self.geometry("1280x720")
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (StartPage, Page1, Page2):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Startpage")
        label.grid(row=0, column=1, padx=10, pady=10)
        button1 = ttk.Button(self, text="Page 1", command=lambda: controller.show_frame(Page1))
        button1.grid(row=1, column=1, padx=10, pady=10)
        button2 = ttk.Button(self, text="Page 2", command=lambda: controller.show_frame(Page2))
        button2.grid(row=1, column=2, padx=10, pady=10)

class Page1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.sp = None
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frm, text="Datum (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        self.date_entry = ttk.Entry(frm, width=20)
        self.date_entry.grid(row=0, column=1, sticky="w")
        self.scrape_btn = ttk.Button(frm, text="Scrape Charts", command=self.on_scrape)
        self.scrape_btn.grid(row=0, column=2, padx=6)
        self.listbox = tk.Listbox(frm, width=60, height=15)
        self.listbox.grid(row=1, column=0, columnspan=3, pady=8)
        self.playlist_btn = ttk.Button(frm, text="Create Spotify Playlist", command=self.on_create_playlist, state="disabled")
        self.playlist_btn.grid(row=2, column=0, pady=6)
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(frm, textvariable=self.status_var)
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="w")
        self.current_songs = []
        self.matched_date = None
        self.sp = None
        self.user_id = None

    def set_status(self, txt):
        self.status_var.set(txt)
        self.controller.update_idletasks()

    def on_scrape(self):
        date_str = self.date_entry.get().strip()
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Greška", "Neispravan format datuma. Koristi YYYY-MM-DD.")
            return
        self.scrape_btn.config(state="disabled")
        self.set_status("Searching...")
        t = threading.Thread(target=self.scrape_thread, args=(date_obj,), daemon=True)
        t.start()

    def scrape_thread(self, date_obj):
        matched_date, songs = core.find_nearest(date_obj)
        if matched_date and songs:
            self.current_songs = songs
            self.matched_date = matched_date
            self.root.after(0, self.show_songs)
        else:
            self.root.after(0, lambda: messagebox.showinfo("Info", "Nema chart-a u zadanim granicama."))
            self.root.after(0, lambda: self.set_status("No results"))
            self.root.after(0, lambda: self.scrape_btn.config(state="normal"))

    def show_songs(self):
        self.listbox.delete(0, tk.END)
        for s in self.current_songs:
            self.listbox.insert(tk.END, s)
        self.set_status(f"Found {len(self.current_songs)} songs for {self.matched_date}")
        self.playlist_btn.config(state="normal")

    def on_create_playlist(self):
        if not self.current_songs:
            messagebox.showwarning("Warning", "Nema pjesama za dodati.")
            return
        self.playlist_btn.config(state="disabled")
        self.set_status("Creating playlist...")
        t = threading.Thread(target=self.create_playlist_thread, daemon=True)
        t.start()

    def create_playlist_thread(self):
        try:
            if not self.sp:
                self.sp = core.setup_spotify()
                user = self.sp.current_user()
                self.user_id = user["id"]
            result = core.create_playlist(self.sp, self.user_id, self.matched_date, self.current_songs, public=True, description=f"Top songs from {self.matched_date} scraped from MusicChartsArchive.com")
            if result and result.get("playlist"):
                playlist_obj = result["playlist"]
                name = playlist_obj.get("name", "Playlist")
                added = result.get("added", 0)
                not_found = result.get("not_found", [])
                msg = f"Playlist '{name}' created. Tracks added: {added}."
                if not_found:
                    msg += f"Not found: {len(not_found)}"
                self.root.after(0, lambda: messagebox.showinfo("Success", msg))
                self.root.after(0, lambda: self.set_status("Playlist created"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to create playlist."))
                self.root.after(0, lambda: self.set_status("Error"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Spotify error: {e}"))
            self.root.after(0, lambda: self.set_status("Error"))
        finally:
            self.root.after(0, lambda: self.playlist_btn.config(state="normal"))

class Page2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.frejm = ttk.LabelFrame(self, text="Connect with your API", padding=10)
        self.frejm.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.desc_label = ttk.Label(self.frejm, text="Here you can use AI to generate some new playlists for you.")
        self.desc_label.grid(row=1, column=1, padx=5, pady=5)

        self.input_label = ttk.Label(self.frejm, text="Insert your API client_id. This information does not get saved.")
        self.input_label.grid(row=2, column=1, padx=5, pady=5)

        self.entry_id = ttk.Entry(self.frejm)
        self.entry_id.grid(row=3, column=1, padx=5, pady=5)

        self.input_label = ttk.Label(self.frejm, text="Insert your API client_secret. This information does not get saved.")
        self.input_label.grid(row=4, column=1, padx=5, pady=5)

        self.entry_secret = ttk.Entry(self.frejm)
        self.entry_secret.grid(row=5, column=1, padx=5, pady=5)

        self.connect_btn = ttk.Button(self.frejm, text="Connect", command=self.connect_spotify)
        self.connect_btn.grid(row=6, column=1, padx=5, pady=5)

        self.drugi_frejm = ttk.LabelFrame(self, text="Insert your playlists.", padding=10)
        self.drugi_frejm.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.playlist_label = ttk.Label(self.drugi_frejm, text="Insert the link to your first playlist.")
        self.playlist_label.grid(row=0, column=1, padx=5, pady=5)

        self.entry_pl1 = ttk.Entry(self.drugi_frejm)
        self.entry_pl1.grid(row=1, column=1, padx=5, pady=5)

        self.playlist_label = ttk.Label(self.drugi_frejm, text="Insert the link to your second playlist.")
        self.playlist_label.grid(row=2, column=1, padx=5, pady=5)

        self.entry_pl2 = ttk.Entry(self.drugi_frejm)
        self.entry_pl2.grid(row=3, column=1, padx=5, pady=5)

        self.playlist_label = ttk.Label(self.drugi_frejm, text="Insert the link to your third playlist.")
        self.playlist_label.grid(row=4, column=1, padx=5, pady=5)

        self.entry_pl3 = ttk.Entry(self.drugi_frejm)
        self.entry_pl3.grid(row=5, column=1, padx=5, pady=5)

        self.combine_btn = ttk.Button(self.drugi_frejm, text="Go through your playlists.", padding=5, command=self.process_picked_playlists)
        self.combine_btn.grid(row=6, column=1, padx=10, pady=10)

        self.text_label = ttk.Label(self.drugi_frejm, text="Or go through all your handmade playlists with the API.")
        self.text_label.grid(row=0, column=2, padx=10, pady=10)
        self.go_btn = ttk.Button(self.drugi_frejm, text="Go through your playlists.", padding=10, command=self.loop_playlists)
        self.go_btn.grid(row=1, column=2, padx=10, pady=10)

    def connect_spotify(self):
        cid = self.entry_id.get().strip()
        secret = self.entry_secret.get().strip()
        if not cid or not secret:
            messagebox.showerror("Error", "Please enter both client ID and client secret.")
            return
        try:
            sp = core.setup_spotify(client_id=cid, client_secret=secret)
            self.sp = sp
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
            messagebox.showinfo("Success", "Playlist data saved to a new csv file.")

    def process_picked_playlists(self):
        if not self.sp:
            messagebox.showerror("Error", "Please connect to Spotify first")
            return
            
        playlist_urls = [
            self.entry_pl1.get().strip(),
            self.entry_pl2.get().strip(),
            self.entry_pl3.get().strip()
        ]
        
        if not any(playlist_urls):  # Check if all entries are empty
            messagebox.showwarning("Warning", "Please enter at least one playlist URL")
            return
            
        try:
            core.loop_picked_playlists(self.sp, playlist_urls)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process playlists: {e}")

        core.loop_songs(self,"short_playlist_data.csv")
app = App()
app.mainloop()
