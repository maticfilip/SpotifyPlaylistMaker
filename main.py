import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import core
import csv
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth
import charts_frame, ai_frame

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
        for F in (StartPage, charts_frame.cFrame, ai_frame.aiFrame):
            # pass StartPage class to cFrame and aiFrame to avoid importing main inside those frames
            if F is charts_frame.cFrame or F is ai_frame.aiFrame:
                frame = F(parent=self.container, controller=self, start_page_class=StartPage)
            else:
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
                             command=lambda: controller.show_frame(charts_frame.cFrame))
        btn1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        btn2 = ctk.CTkButton(self, text="AI Playlists", 
                             font=("Segoe UI", 18, "bold"), width=220,
                             command=lambda: controller.show_frame(ai_frame.aiFrame))
        btn2.place(relx=0.5, rely=0.6, anchor=tk.CENTER)


app = App()
app.mainloop()
