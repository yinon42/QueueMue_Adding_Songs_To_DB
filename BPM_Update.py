import os
import tempfile
import requests
import librosa
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI

"""
This script scans all songs in the Firestore database and automatically calculates the BPM (beats per minute)
for songs that are missing it. It downloads the MP3 file using the `audioUrl`, analyzes the audio using `librosa`,
and updates the `bpm` field in Firestore.

Features:
- Downloads audio files from public URLs stored in Firestore.
- Uses `librosa` to analyze each file and extract tempo (BPM).
- Updates the Firestore `songs` collection with the calculated BPM.
- Skips songs that already have a BPM or are missing `audioUrl`.

Technologies:
- `firebase-admin` to connect and update Firestore
- `requests` for HTTP audio download
- `librosa` for BPM detection and signal processing
- `tempfile` and `os` for managing temporary files
- `dotenv` to load environment variables
- Optional `FastAPI` setup for future expansion (e.g., turning into an API endpoint)

Use Case:
Run this script after uploading songs to Firebase Storage, to fill in missing BPM values for use in playlists,
sorting, and music analytics.

Prerequisites:
- The `songs` collection in Firestore must have an `audioUrl` field pointing to a valid MP3 file.
- Firebase Admin SDK service key must be correctly configured.
- `librosa` and its dependencies (`numpy`, `soundfile`) must be installed.
"""

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase using service account JSON file
cred = credentials.Certificate(r"C:\Users\Yinon\PycharmProjects\QueueMue_Adding_Songs_To_DB\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Create FastAPI app instance
app = FastAPI()

# Download audio file from a given URL and save it temporarily
def download_audio(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                for chunk in response.iter_content(chunk_size=1024):
                    tmp.write(chunk)
                return tmp.name
        else:
            print(f"[ERROR] Failed to download file: {url}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] Error downloading file: {e}")
        return None

# Analyze audio file and calculate its BPM (beats per minute) using librosa
def calculate_bpm(file_path):
    try:
        y, sr = librosa.load(file_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return round(float(tempo), 2)
    except Exception as e:
        print(f"[EXCEPTION] Error in BPM calculation: {e}")
        return None

# Scan all songs in Firestore and update BPM for those missing it
def process_missing_bpm():
    print("🔍 Scanning all songs without BPM...")
    songs = db.collection('songs').stream()

    total = 0
    success = 0
    failed = 0

    for doc in songs:
        data = doc.to_dict()
        audio_url = data.get('audioUrl')
        bpm = data.get('bpm')
        title = data.get('title', 'Unknown')

        if not audio_url:
            print(f"[WARNING] Skipping '{title}' - no audioUrl.")
            continue
        if bpm is not None:
           # print(f"[INFO] Skipping '{title}' - BPM already exists.")
            continue

        total += 1
        print(f"\n🎵 Processing song: {title}")
        file_path = download_audio(audio_url)
        if not file_path:
            print(f"[ERROR] Failed to download '{title}'.")
            failed += 1
            continue

        bpm_result = calculate_bpm(file_path)
        os.remove(file_path)

        if bpm_result:
            print(f"✅ Calculated BPM = {bpm_result} for '{title}'")
            db.collection('songs').document(doc.id).update({'bpm': bpm_result})
            success += 1
        else:
            print(f"❌ Failed to calculate BPM for '{title}'")
            failed += 1

    print("\n📊 Done.")
    print(f"Total processed: {total}")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")

# Main Execution
if __name__ == "__main__":
    process_missing_bpm()
