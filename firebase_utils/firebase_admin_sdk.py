import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
#from .config import cred_dict

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize Firebase Admin SDK with error handling
try:
    #cred = credentials.Certificate(cred_dict)
    cred = credentials.Certificate("firebase_utils/firebase_admin_sdk.json")
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    raise  # Optionally, raise the error again to propagate it

# Initialize Firestore client with error handling
try:
    db = firestore.client()
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    raise







