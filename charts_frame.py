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

class cFrame(ctk.CTkFrame):
    # accept start_page_class so we don't import main here (breaks circular import)
    def __init__(self, parent, controller, start_page_class):
        super().__init__(parent, fg_color="#0d0d0d")
        self.controller = controller
        self.sp = None
        self.start_page_class = start_page_class

        topbar = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        topbar.pack(pady=20, padx=20, fill="x")

        # use the passed StartPage class reference instead of importing it
        back_btn = ctk.CTkButton(topbar, text="← Back", width=100, command=lambda: controller.show_frame(self.start_page_class))
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

