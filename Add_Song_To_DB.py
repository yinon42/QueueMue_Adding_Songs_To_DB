import os
import subprocess

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import firebase_admin
from firebase_admin import credentials, firestore
from spotipy.oauth2 import SpotifyClientCredentials

"""
This script allows you to upload metadata about a Spotify track to Firebase Firestore.

Workflow:
1. Prompt the user to input a Spotify track URL.
2. Use the Spotify Web API to extract metadata (title, artist, duration, album art).
3. Create or retrieve artist and genre documents in Firestore.
4. Add a new document to the "songs" collection, including:
   - Title, artist reference, genre references, duration, artwork, and more.
5. After all uploads, run auxiliary scripts:
   - `System_Playlists_Update.py`: updates system playlists.
   - `Songs_With_No_MP3_List.py`: generates a report of missing MP3s.
   - `Lyrics_Fill_Batch.py`: fills lyrics for the newly added songs.

Technologies used:
- Spotipy for Spotify Web API
- Firebase Admin SDK for Firestore
- `.env` file for managing sensitive credentials

Notes:
- `audioUrl` is currently left empty – to be filled manually or in a later step.
- Lyrics and genres are fetched where possible.
- Auxiliary scripts must be in the same project directory.
"""

# Load environment variables from .env file
load_dotenv()

# Init Spotify clients
auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-library-read"
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Use client credentials for genre and artist info
sp_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

# Initialize Firebase Admin SDK
cred = credentials.Certificate(r"C:\Users\yinon\PycharmProjects\quemueFirestoreAddSongs\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Genre ID cache to avoid duplicates
genre_cache = {}

# Generates a Firestore-safe ID from a name (uppercase, underscores instead of spaces)
def safe_id(name):
    return name.strip().replace(" ", "_").upper()

# Gets or creates a document in a collection using a normalized name-based ID
def get_or_create_named_document(collection_name, name_field, name_value):
    doc_id = safe_id(name_value)
    doc_ref = db.collection(collection_name).document(doc_id)
    if not doc_ref.get().exists:
        doc_ref.set({name_field: name_value})
    return doc_id

# Fetches Spotify genres for a track and returns a list of genre document IDs (creating them if needed)
def get_or_create_genre_ids(track_id):
    try:
        track = sp_client.track(track_id)
        artist_id = track["artists"][0]["id"]
        artist = sp_client.artist(artist_id)
        genres = artist.get("genres", [])
        genre_ids = []

        for g in genres:
            g_lower = g.lower()
            if g_lower in genre_cache:
                genre_ids.append(genre_cache[g_lower])
            else:
                genre_id = safe_id(g)
                ref = db.collection("genres").document(genre_id)
                if not ref.get().exists:
                    ref.set({"name": g})
                genre_cache[g_lower] = genre_id
                genre_ids.append(genre_id)

        return genre_ids
    except Exception as e:
        print(f"⚠️ Failed to get genres: {e}")
        return []

#  Extract track metadata from Spotify
def extract_basic_info(url):
    track_id = url.split("/")[-1].split("?")[0]
    print("🎯 Track ID:", track_id)

    track = sp.track(track_id, market="IL")
    artist_name = track["artists"][0]["name"]

    return {
        "track_id": track_id,
        "title": track["name"],
        "artist": artist_name,
        "duration": int(track["duration_ms"] / 1000),
        "url": url,
        "cover": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
        "audioUrl": ""
    }

# Upload a song document to Firestore
def upload_song(song_data):
    artist_name = song_data["artist"]
    artist_id = get_or_create_named_document("artists", "name", artist_name)
    genre_ids = get_or_create_genre_ids(song_data["track_id"])

    # Normalize titles
    original_title = song_data["title"]
    title_upper = original_title.strip().upper()
    title_lower = original_title.strip().lower()

    song_id = safe_id(original_title)
    doc_ref = db.collection("songs").document(song_id)

    doc = {
        "title": title_upper,
        "title_lower": title_lower,
        "artistId": artist_id,
        "artistName": artist_name,
        "artist_lower": artist_name.strip().lower(),
        "genreId": genre_ids,
        "lyrics": "",
        "url": song_data["url"],
        "duration": song_data["duration"],
        "cover": song_data["cover"],
        "audioUrl": song_data["audioUrl"]
    }

    doc_ref.set(doc)
    print(f'✅ "{title_upper}" uploaded successfully under ID: {song_id}\n')

# CLI loop to upload songs and run post-upload scripts
def main():
    print("🎧 Upload basic song info from Spotify to Firestore")
    print("Paste a Spotify track URL (or type 'exit' to quit):\n")

    uploaded_song_ids = []  # We will track uploaded songs

    while True:
        url = input("🔗 Spotify URL: ").strip()
        if url.lower() in ["exit", "quit"]:
            break

        try:
            info = extract_basic_info(url)
        except Exception as e:
            print(f"❌ Failed to extract info: {e}\n")
            continue

        print(f"\n🎵 Title: {info['title']}")
        print(f"🎤 Artist: {info['artist']}")
        print(f"⏱ Duration: {info['duration']} sec")
        print(f"🖼️ Cover: {info['cover']}")

        try:
            upload_song(info)
            song_id = safe_id(info["title"])
            uploaded_song_ids.append(song_id)  # We will save the ID.

        except Exception as e:
            print(f"❌ Failed to upload: {e}\n")

    if uploaded_song_ids:
        print("\n📦 Running post-upload tasks...")

        # Convert to string format to send as parameter
        song_ids_string = ",".join(uploaded_song_ids)

        venv_python = r"C:\Users\yinon\PycharmProjects\quemueFirestoreAddSongs\venv\Scripts\python.exe"
        subprocess.run([venv_python, "System_Playlists_Update.py"])
        subprocess.run([venv_python, "Songs_With_No_MP3_List.py"])
        subprocess.run([venv_python, "Lyrics_Fill_Batch.py", song_ids_string])

    print("✅ All post-upload tasks completed.")

# Main Execution
if __name__ == "__main__":
    main()