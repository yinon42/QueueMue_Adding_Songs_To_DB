
# 🎧 QueueMue Firestore Music Manager

This project provides a suite of Python scripts for managing a music database using Firebase Firestore and Firebase Storage.  
It supports adding songs from Spotify, uploading MP3 files, filling in missing lyrics and BPM, and creating system playlists.

---

## 📦 Project Structure

```
quemueFirestoreAddSongs/
├── Add_Song_To_DB.py              # Upload song metadata from Spotify to Firestore
├── MP3_Upload.py                  # Upload local MP3 files to Firebase Storage
├── Lyrics_Fill_Batch.py           # Auto-fill missing lyrics using lyrics.ovh API
├── BPM_Update.py                  # Analyze songs and fill missing BPM values
├── Songs_With_No_MP3_List.py      # List songs missing audioUrl (no uploaded MP3)
├── System_Playlists_Update.py     # Auto-create playlists grouped by genre
```

---

## 🚀 How to Use

### 1. 🔑 Setup

- Python 3.8+
- Firebase project with Firestore & Storage enabled
- Spotify Developer API credentials
- Create a `.env` file with:

```env
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

- Download Firebase service account key as `queuemueue-firebase-admin.json`

---

### 2. 🎼 Upload Songs from Spotify

Use `Add_Song_To_DB.py` to extract song metadata and upload it to Firestore.

```bash
python Add_Song_To_DB.py
```

- Adds song title, artist, album cover, genre, and more.
- Automatically updates:
  - `songs` collection
  - `artists` and `genres`
  - Runs:
    - `System_Playlists_Update.py`
    - `Songs_With_No_MP3_List.py`
    - `Lyrics_Fill_Batch.py`

---

### 3. 📤 Upload MP3 Files

Upload matching `.mp3` files using `MP3_Upload.py`:

```bash
python MP3_Upload.py
```

- Matches file titles to existing Firestore songs
- Uploads to `songs/` in Firebase Storage
- Updates the `audioUrl` field in Firestore
- Generates logs for successful and failed uploads
- Runs `BPM_Update.py` automatically at the end

---

### 4. 📝 Fill Missing Lyrics

Use `Lyrics_Fill_Batch.py` to fill lyrics for specific songs:

```bash
python Lyrics_Fill_Batch.py SONG_ID1,SONG_ID2,...
```

- Fetches lyrics via the [lyrics.ovh API](https://lyrics.ovh/)
- Updates `lyrics` field in the relevant song documents

---

### 5. 🥁 Analyze BPM

Detect missing BPM and update them with:

```bash
python BPM_Update.py
```

- Downloads MP3 from `audioUrl`
- Uses `librosa` to calculate tempo (BPM)
- Updates Firestore with results

---

### 6. 🎵 Generate System Playlists

Automatically generate playlists by genre using:

```bash
python System_Playlists_Update.py
```

- Groups songs by `genreId`
- Creates documents in `system_playlists` collection
- Each playlist includes a list of song IDs by genre

---

### 7. 🔍 Identify Songs Missing Audio

List all songs without an MP3 using:

```bash
python Songs_With_No_MP3_List.py
```

- Prints out song titles and Spotify URLs
- Helps locate songs that are missing an uploaded file

---

## 📁 Firestore Collections Overview

| Collection        | Purpose                                  |
|------------------|-------------------------------------------|
| `songs`          | Stores all song metadata and audio info  |
| `artists`        | Stores artist names and IDs              |
| `genres`         | Stores genre tags used for playlists     |
| `system_playlists` | Stores auto-generated playlists by genre |

---

## 🛡️ Notes

- Do not commit your `.env` or service account JSON files.
- Add the following to `.gitignore`:

```gitignore
.env
*.json
venv/
logs/
```

---

## 📜 License

MIT © 2025 Yinon Meir
