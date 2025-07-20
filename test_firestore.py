import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.collection("test").document("demo")
doc_ref.set({"hello": "world"})

print("✅ Test write complete.")
