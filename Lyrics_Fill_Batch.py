import firebase_admin
from firebase_admin import credentials, firestore
import requests
import sys

"""
This script receives a comma-separated list of song IDs via command line,
and fills in missing lyrics for each one by calling the lyrics.ovh API.

Usage example:
python Lyrics_Fill_Batch.py SONG_ID1,SONG_ID2,SONG_ID3
"""

# Initialize Firebase connection
cred = credentials.Certificate(r"C:\Users\yinon\PycharmProjects\quemueFirestoreAddSongs\queuemueue-firebase-admin.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Fetch artist name by artist document ID
def get_artist_name_by_id(artist_id):
    try:
        doc = db.collection("artists").document(artist_id).get()
        if doc.exists:
            return doc.to_dict().get("name", "")
    except Exception as e:
        print(f"❌ Error fetching artist name: {e}")
    return None

# Fetch lyrics from external API (lyrics.ovh)
def fetch_lyrics(artist, title):
    try:
        print(f"🌐 Fetching lyrics for: {artist} – {title}")
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("lyrics", "")
        else:
            print(f"⚠️ Not found: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching lyrics: {e}")
    return None

# Fill missing lyrics for a list of song IDs
def fill_lyrics_for_songs(song_ids):
    updated = 0
    skipped = 0
    failed = 0

    for song_id in song_ids:
        print(f"\n🎯 Processing: {song_id}")
        try:
            doc_ref = db.collection("songs").document(song_id)
            doc = doc_ref.get()
            if not doc.exists:
                print(f"❌ Song '{song_id}' not found.")
                failed += 1
                continue

            data = doc.to_dict()
            title = data.get("title", "").strip()
            artist_id = data.get("artistId")
            lyrics = data.get("lyrics", "")

            if lyrics:
                print("⏭️ Already has lyrics.")
                skipped += 1
                continue

            artist_name = get_artist_name_by_id(artist_id)
            if not artist_name:
                print(f"❌ Artist not found for ID: {artist_id}")
                failed += 1
                continue

            found_lyrics = fetch_lyrics(artist_name, title)
            if found_lyrics:
                doc_ref.update({"lyrics": found_lyrics})
                print(f"✅ Updated lyrics for '{title}' by {artist_name}")
                updated += 1
            else:
                failed += 1

        except Exception as e:
            print(f"❌ Error processing '{song_id}': {e}")
            failed += 1

    print("\n📊 Lyrics Update Summary:")
    print(f"✅ Updated: {updated}")
    print(f"⏭ Skipped: {skipped}")
    print(f"❌ Failed: {failed}")


# Read song IDs from command-line arguments and run the update
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide a comma-separated list of song IDs.")
        sys.exit(1)

    song_ids_str = sys.argv[1]
    song_ids = [sid.strip() for sid in song_ids_str.split(",") if sid.strip()]
    fill_lyrics_for_songs(song_ids)
