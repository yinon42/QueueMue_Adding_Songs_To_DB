from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, firestore

"""
This script generates system playlists based on genres stored in Firestore.
It scans all songs in the database, groups them by matching genre, and writes
a list of song IDs into the `system_playlists` collection, one document per genre.

How it works:
1. Fetches all genres from the `genres` collection.
2. Loads all songs from the `songs` collection.
3. For each song, checks its genre(s) and assigns it to the matching playlist.
4. Saves the resulting playlists into Firestore under the `system_playlists` collection.

Notes:
- Matching is case-insensitive and based on containment (e.g., "hiphop" in "hiphop/urban").
- Songs can belong to multiple playlists if they have multiple genres.
"""
# Initialize Firebase
cred = credentials.Certificate(r"C:\Users\yinon\PycharmProjects\quemueFirestoreAddSongs\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Fetch all genre names (lowercased)
def fetch_all_genres():
    genres_ref = db.collection("genres").stream()
    return [doc.to_dict().get("name", "").strip().lower() for doc in genres_ref if doc.to_dict().get("name")]

# Fetch all songs from Firestore
def get_all_songs():
    return list(db.collection("songs").stream())

# Extract genre names (as lowercase strings) from a song's 'genreId' field
def get_genre_names(genre_field):
    if not genre_field:
        return []
    if isinstance(genre_field, str):
        return [genre_field.lower()]
    elif isinstance(genre_field, list):
        return [g.lower() for g in genre_field if isinstance(g, str)]
    else:
        return []

# Build playlists and write them to Firestore
def build_system_playlists():
    genre_names = fetch_all_genres()
    all_songs = get_all_songs()

    playlists = defaultdict(list)

    for genre_name in genre_names:
        for song in all_songs:
            data = song.to_dict()
            song_id = song.id
            song_genres = get_genre_names(data.get("genreId"))

            for sg in song_genres:
                if genre_name in sg:
                    playlists[genre_name].append(song_id)
                    break  # Stop checking once a match is found

    # Write playlists to Firestore
    for genre, song_ids in playlists.items():
        # Create playlist document (metadata)
        playlist_ref = db.collection("system_playlists").document(genre)
        playlist_ref.set({
            "name": genre.capitalize(),
            "numSongs": len(song_ids)
        })

        # Write subcollection of songs with isLast field
        for i, song_id in enumerate(song_ids):
            playlist_ref.collection("songs").document(song_id).set({
                "songId": song_id,
                "isLast": (i == len(song_ids) - 1)
            })

        print(f"🎵 Playlist '{genre}' – {len(song_ids)} songs added.")

    print("\n✅ System playlists with isLast updated successfully!")

# Main Execution
if __name__ == "__main__":
    build_system_playlists()
