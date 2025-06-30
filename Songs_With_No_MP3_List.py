import firebase_admin
from firebase_admin import credentials, firestore

"""
This script connects to Firebase Firestore and lists all songs in the "songs" collection
that are missing an `audioUrl` field (either empty or null).

Useful for identifying which songs have no uploaded MP3 file linked to them.

Output:
- Prints song titles and Spotify URLs for all songs missing `audioUrl`.

Technologies:
- Firebase Admin SDK
"""

# Initialize Firebase
cred = credentials.Certificate(r"C:\Users\Yinon\PycharmProjects\QueueMue_Adding_Songs_To_DB\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Retrieve all songs from the 'songs' collection
songs_ref = db.collection("songs")
all_songs = songs_ref.stream()

print("🎧 Songs with missing audioUrl (null or empty):\n")

# Loop through songs and check for missing audioUrl
for doc in all_songs:
    song = doc.to_dict()
    audio_url = song.get("audioUrl")

    if not audio_url:  # Handles None, empty string, or other false values
        title = song.get("title", "Unknown")
        spotify_url = song.get("url", "No URL")
        print(f"🎵 {title}\n🔗 {spotify_url}\n")
