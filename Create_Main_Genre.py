
"""
This script updates the `mainGenre` field for each song in the Firestore `songs` collection
based on the first genre listed in the `genreId` array.

How it works:
1. Fetches all song documents from the `songs` collection.
2. For each song:
   a. Checks if the `genreId` field exists and is a list.
   b. Extracts the first genre from the list.
   c. Saves it to a new field called `mainGenre` in the same document.

Notes:
- Songs without any genre will be skipped.
- Useful for quick access to the primary genre of a song without processing the full list.
"""

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate(r"C:\Users\Yinon\PycharmProjects\QueueMue_Adding_Songs_To_DB\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def update_main_genre():
    songs_ref = db.collection('songs')
    songs = songs_ref.stream()

    for song in songs:
        data = song.to_dict()
        genre_ids = data.get('genreId', [])

        # Check if there is at least one genre
        if isinstance(genre_ids, list) and len(genre_ids) > 0:
            main_genre = genre_ids[0]
            song.reference.update({'mainGenre': main_genre})
            print(f"✅ Updated mainGenre for song: {song.id} -> {main_genre}")
        else:
            print(f"⚠️ No genres found for song: {song.id}, skipped.")

if __name__ == "__main__":
    update_main_genre()
