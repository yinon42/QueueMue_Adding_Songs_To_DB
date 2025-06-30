import firebase_admin
from firebase_admin import credentials, firestore

# אתחל את Firebase Admin SDK
cred = credentials.Certificate(r"C:\Users\Yinon\PycharmProjects\QueueMue_Adding_Songs_To_DB\queuemueue-firebase-admin.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def update_main_genre():
    songs_ref = db.collection('songs')
    songs = songs_ref.stream()

    for song in songs:
        data = song.to_dict()
        genre_ids = data.get('genreId', [])

        # בדיקה אם יש לפחות ז'אנר אחד
        if isinstance(genre_ids, list) and len(genre_ids) > 0:
            main_genre = genre_ids[0]
            song.reference.update({'mainGenre': main_genre})
            print(f"עודכן mainGenre לשיר: {song.id} -> {main_genre}")
        else:
            print(f"לא נמצא ז'אנר עבור השיר: {song.id}, דילגנו.")

if __name__ == "__main__":
    update_main_genre()
