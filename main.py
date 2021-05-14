import tkinter as tk
from tkinter import ttk
import urllib
import time
import os
import re
import sys
import spotipy
import pytube
import validators
import threading
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch

# Spotify Credentials
SPOTIPY_CLIENT_ID = "706faa895a0f45718209aec6c61a0a70"
SPOTIPY_CLIENT_SECRET = "a915de3be77c44989562f2b41df62ef8"
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback/"


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 265

# Downloads Spotify tracks from YouTube
def download_yt_vids(track_urls, download_path):
    global track_names
    global restart

    progress_bar_increase = 100 / len(track_names)
    text_entry.delete(0, len(text_entry.get()))
    text_entry["state"] = "disabled"

    for i, track in enumerate(track_urls):
        current_track_name = re.sub(r"[\\/*?:'<>|]", "", track_names[i])

        if os.path.isfile(download_path + "\\" + current_track_name + ".mp3"):
            progress_bar["value"] += progress_bar_increase
            continue
        try:
            out_file = pytube.YouTube(track).streams.first().download(download_path)
        except (pytube.exceptions.RegexMatchError, urllib.error.HTTPError, ConnectionResetError) as e:
            print(track)
            print(e)
            continue

        os.rename(out_file, download_path + "\\" + current_track_name + ".mp3")
        progress_bar["value"] += progress_bar_increase

    status_text["text"] = "Done, go to " + download_path
    progress_bar["value"] = 0
    submit_button["state"] = "normal"
    submit_button["text"] = "Restart"
    restart = True


# Asks user for a download path and checks if it is valid
def is_valid_dir(download_path):
    global track_urls
    global is_loading

    if not os.path.isdir(download_path):
        status_text["text"] = "Error: Invalid Path"
        return
    else:
        status_text["text"] = "Valid Path, downloading your music..."
        submit_button["state"] = "disabled"
        is_loading = True
        download_yt_vids(track_urls, download_path)
        return


# Converts track_names into YouTube URLs by searching the Spotify track name on YouTube and getting the top result
def get_yt_urls(track_names):
    global track_urls
    global delete_entry_text
    global is_loading
    progress_bar_increase = 100/len(track_names)

    track_urls = []
    for names in track_names:
        videos_search = VideosSearch(names, limit=2)
        try:
            track_urls.append(videos_search.result()["result"][0]["link"])
        except IndexError:
            continue
        progress_bar["value"] += progress_bar_increase

    status_text["text"] = "Where do you want to download your music?"
    text_entry["state"] = "normal"
    text_entry["background"] = "white"
    window.focus_set()
    text_entry["foreground"] = "grey"
    text_entry.insert(0, "Enter Path Here")
    delete_entry_text = True
    is_loading = False
    progress_bar["value"] = 0
    progress_bar.grid_remove()
    submit_button["state"] = "normal"
    return


# Gets all the names of the tracks in the Users requested Spotify playlist and puts them in a list(track_names)
def get_playlist_track_names(playlist_url):
    global track_names

    track_offset = 0
    track_names = []
    for i in range(100):
        tracks = sp.playlist_tracks(playlist_id=playlist_url, offset=track_offset)
        for names in tracks["items"]:
            track_names.append(names["track"]["album"]["artists"][0]["name"] + " - " + names["track"]["name"])
        if not tracks["next"]:
            get_yt_urls(track_names)
            return
        track_offset += 100


# Checks if spotify URL is valid
def is_valid_spotify_url(playlist_url):
    global is_asking_dir
    global is_loading

    if not validators.url(str(playlist_url)):
        status_text["text"] = 'Error: Invalid URL, maybe you forgot to put "http://"'
        return
    else:
        try:
            sp.playlist_tracks(playlist_id=playlist_url)
            status_text["text"] = "Valid URL, getting Spotify data..."
            is_asking_dir = True
            is_loading = True
            text_entry.delete(0, len(text_entry.get()))
            text_entry["background"] = "black"
            text_entry["state"] = "disabled"
            submit_button["state"] = "disabled"
            progress_bar.pack()
            progress_bar.lift()
            progress_bar.lift()
            get_playlist_track_names(playlist_url)
            return
        except SpotifyException:
            status_text["text"] = "Error: Invalid URL, make sure your URL is a Spotify playlist link"
            return


# Starts a thread separated from the window.mainloop()
def button():
    global is_asking_dir
    global restart
    global delete_entry_text
    global is_loading

    if not is_asking_dir and not restart:
        playlist_url_entry = text_entry.get()
        program_thread = threading.Thread(target=is_valid_spotify_url, args=(playlist_url_entry,))
        program_thread.daemon = True
        program_thread.start()
    elif is_asking_dir and not restart:
        dir_thread = threading.Thread(target=is_valid_dir, args=(text_entry.get(),))
        dir_thread.daemon = True
        dir_thread.start()
    elif restart:
        text_entry["state"] = "normal"
        window.focus_set()
        text_entry.insert(0, "Enter URL here")
        text_entry.config(foreground="grey")
        status_text["text"] = "Enter Your Spotify Playlist URL"
        submit_button["text"] = "Submit"
        is_loading = False
        is_asking_dir = False
        delete_entry_text = True
        restart = False


def handle_focus_in(_):
    global delete_entry_text
    if delete_entry_text:
        text_entry.delete(0, len(text_entry.get()))
        text_entry.config(foreground="white")
        delete_entry_text = False


def handle_focus_out(_):
    if _ != "Pass":
        global is_asking_dir


def handle_enter(txt):
    global is_loading
    handle_focus_out("Pass")
    if not is_loading:
        button()


is_asking_dir = False
restart = False
delete_entry_text = True
is_loading = False

track_names = []
track_urls = []

window = tk.Tk()

window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
window.resizable(False, False)

style = ttk.Style()

window.tk.call("source", os.path.dirname(__file__) + "\\Azure\\azure-dark.tcl")

style.theme_use("azure-dark")

if getattr(sys, "frozen", False):
    icon = os.path.dirname(sys.executable) + "\\Images\\Spotify Playlist To MP3 Icon.ico"
elif __file__:
    icon = os.path.dirname(__file__) + "\\Images\\Spotify Playlist To MP3 Icon.ico"

window.iconbitmap(icon)
window.title("Spotify Playlist Downloader")

instructions_text = ttk.Label(window, text="Spotify Playlist Downloader", font=("TkDefaultFont", 50))
instructions_text.pack()

text_entry = ttk.Entry(window, width=50, font=("TkDefaultFont", 20), foreground="grey")
text_entry.insert(0, "Enter URL here")
text_entry.pack(pady=7)

text_entry.bind("<FocusIn>", handle_focus_in)
text_entry.bind("<FocusOut>", handle_focus_out)
text_entry.bind("<Return>", handle_enter)

status_text = ttk.Label(window, text="Enter Your Spotify Playlist URL", font=("TkDefaultFont", 20))
status_text.pack()

progress_bar = ttk.Progressbar(length=350)
progress_bar.pack()

submit_button = ttk.Button(window, text="Submit", width=15, command=lambda: button())
submit_button.pack(pady=5, ipady=10)

token = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                     client_secret=SPOTIPY_CLIENT_SECRET,
                     redirect_uri=SPOTIPY_REDIRECT_URI)
sp = spotipy.Spotify(auth_manager=token)


def main():
    window.mainloop()


if __name__ == "__main__":
    main()