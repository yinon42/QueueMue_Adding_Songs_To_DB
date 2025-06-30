import os
import subprocess
import firebase_admin
from firebase_admin import credentials, firestore, storage
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

"""
This script scans a local folder for MP3 files, extracts the title metadata from each file,
and uploads the corresponding file to Firebase Storage if a matching song document (by title) exists in Firestore.
Once uploaded, it updates the `audioUrl` field in the Firestore song document with the public URL of the uploaded file.

Features:
- Reads `.mp3` files from a specified local directory.
- Extracts `title` from ID3 metadata using `mutagen`.
- Matches the extracted title with song documents in Firestore (`songs` collection).
- Uploads matched files to Firebase Storage under the `songs/` directory.
- Sets the uploaded file to be public and updates the song document with the `audioUrl`.
- Generates log files for successful and failed uploads.

Technologies used:
- `firebase-admin` for Firestore and Firebase Storage operations.
- `mutagen` to read ID3 metadata from MP3 files.
- `os` and file I/O for filesystem operations and logging.

Logs:
- `uploaded_log.txt` — Lists all successfully uploaded songs and their download URLs.
- `failed_log.txt` — Lists all files that failed to upload, including reasons (missing title, not found in DB, etc.).

Configuration:
- `FOLDER_PATH`: Path to the folder containing `.mp3` files.
- `CREDENTIALS_PATH`: Path to your Firebase Admin SDK JSON credentials.
- `BUCKET_NAME`: Firebase Storage bucket (e.g., `your-project-id.appspot.com`).

Notes:
- File matching is based **only** on the lowercase `title` field in metadata and Firestore.
- Songs in Firestore **must already exist** with a matching `title` before running this script.
"""

# Configuration
FOLDER_PATH = r"C:\Users\yinon\Desktop\SongsToUpload"
BUCKET_NAME = 'queuemueue.firebasestorage.app'
LOGS_FOLDER = os.path.join(FOLDER_PATH, 'logs')
CREDENTIALS_PATH = r"C:\Users\Yinon\PycharmProjects\QueueMue_Adding_Songs_To_DB\queuemueue-firebase-admin.json"

# Create logs folder if it doesn't exist
os.makedirs(LOGS_FOLDER, exist_ok=True)
uploaded_log_path = os.path.join(LOGS_FOLDER, "uploaded_log.txt")
failed_log_path = os.path.join(LOGS_FOLDER, "failed_log.txt")

# Initialize Firebase connection
cred = credentials.Certificate(CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {
    'storageBucket': BUCKET_NAME
})

db = firestore.client()
bucket = storage.bucket()

# Test Firestore connection and load existing songs
try:
    songs_ref = db.collection('songs').stream()
    songs_by_title = {}
    count = 0
    for song in songs_ref:
        data = song.to_dict()
        title = data.get('title', '').strip()
        if title:
            songs_by_title[title.lower()] = song.id
            count += 1
    print(f"🔍 Connected to Firestore! Found {count} songs.")
except Exception as e:
    print(f"❌ Error connecting to Firestore: {str(e)}")
    exit()

# Extract the title from MP3 file metadata using mutagen
def get_title_from_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get('title', [None])[0]
        return title.strip() if title else None
    except Exception as e:
        print(f"⚠️ Error reading metadata from '{file_path}': {e}")
        return None

# Process and upload each MP3 file
files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(".mp3")]
uploaded_log, failed_log = [], []

print(f"\n📁 Found {len(files)} MP3 files to process.\n")

for file_name in files:
    local_path = os.path.join(FOLDER_PATH, file_name)

    title = get_title_from_metadata(local_path)
    if not title:
        print(f"❌ No title found in metadata: {file_name}")
        failed_log.append(f"{file_name} -> MISSING TITLE")
        continue

    key = title.lower()
    if key not in songs_by_title:
        print(f"❌ Song not found in Firestore: '{title}' (from file: {file_name})")
        failed_log.append(f"{file_name} -> TITLE NOT FOUND IN DB: {title}")
        continue

    song_id = songs_by_title[key]
    firebase_path = f"songs/{file_name}"

    try:
        blob = bucket.blob(firebase_path)
        blob.upload_from_filename(local_path)
        blob.make_public()
        download_url = blob.public_url

        db.collection('songs').document(song_id).update({
            'audioUrl': download_url
        })

        print(f"✅ Uploaded: {file_name} -> title: '{title}'")
        uploaded_log.append(f"{file_name} -> {download_url}")
    except Exception as e:
        print(f"❌ Upload error for {file_name}: {str(e)}")
        failed_log.append(f"{file_name} -> ERROR: {str(e)}")

# Write logs to file
with open(uploaded_log_path, 'w', encoding='utf-8') as f:
    f.write("✅ Successfully uploaded:\n" + "\n".join(uploaded_log))

with open(failed_log_path, 'w', encoding='utf-8') as f:
    f.write("❌ Failed uploads:\n" + "\n".join(failed_log))

print("\n📄 Logs written to:")
print(f"  📁 Success: {uploaded_log_path}")
print(f"  📁 Failures: {failed_log_path}")

# Run BPM update script after uploads
print("\n🚀 Running BPM_Update.py to calculate BPM...")

venv_python = r"C:\Users\yinon\PycharmProjects\quemueFirestoreAddSongs\venv\Scripts\python.exe"
bpm_script = os.path.join(os.getcwd(), "BPM_Update.py")
result = subprocess.run([venv_python, bpm_script])

if result.returncode == 0:
    print("✅ BPM_Update.py completed successfully.")
else:
    print("❌ Error running BPM_Update.py.")
