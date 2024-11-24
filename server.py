import os
import sys
import json
import pytz
import logging
from datetime import datetime
from dotenv import load_dotenv
from firebase.firebase_admin_sdk import db
from generate_devotional import generate_full_devotional

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
load_dotenv()

def create_daily_devotionals():
    results = []
    users = db.collection('users').stream()
    
    for user in users:
        user_id = user.id
        user_doc = db.collection('users').document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_email = user_data.get('email')
            
            if user_email:
                try:
                    # Generate the devotional content for the user
                    devotional_content = generate_full_devotional(user_id)

                    # Prepare the devotional data
                    devotional_data = {
                        "biblePassage": devotional_content.get("biblePassage", ""),
                        "dateTimeCreated": datetime.now(pytz.UTC).isoformat(),
                        "doc_id": None,  # Will be set after adding to Firestore
                        "forUser": user_id,
                        "isFavorite": False,
                        "journalingPrompt": devotional_content.get("journalingPrompt", ""),
                        "personalization": devotional_content.get("personalization", ""),
                        "title": devotional_content.get("title", "")
                    }

                    # Add the devotional to the user's devotionals collection
                    devotional_ref = db.collection('devotionals').add(devotional_data)
                    devotional_doc_id = devotional_ref[1].id

                    # Update the doc_id field
                    devotional_data["doc_id"] = devotional_doc_id
                    db.collection('devotionals').document(devotional_doc_id).set(devotional_data)

                    logging.info(f"Devotional uploaded for user {user_id} ({user_email})")
                    results.append({"user_id": user_id, "status": "success"})
                
                except Exception as e:
                    logging.error(f"Error generating devotional for {user_id} ({user_email}): {str(e)}")
                    results.append({"user_id": user_id, "status": "failure", "error": str(e)})
            else:
                logging.info(f"Skipping test email for user {user_id} ({user_email})")
        else:
            logging.error(f"User {user_id} does not exist in the database")
            results.append({"user_id": user_id, "status": "not_found"})
    
    # Return results as a JSON-formatted string
    return json.dumps({"message": "Devotionals created successfully", "results": results})

if __name__ == "__main__":
    response = create_daily_devotionals()
    print(response)
