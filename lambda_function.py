import os
import sys
import json
import pytz
import logging
from datetime import datetime
from dotenv import load_dotenv
from firebase_utils.firebase_admin_sdk import db
from generate_devotional import generate_devotional_content
from google.api_core.exceptions import DeadlineExceeded  # To catch timeout errors

log_filename = "./tmp/daily_devotionals.log"  # /tmp is the only writable directory in Lambda
users_file_path = "./tmp/users.json"  # Users JSON file path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

# Load existing users.json data
def load_users_data():
    if os.path.exists(users_file_path):
        try:
            with open(users_file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logging.error("Error reading users.json, starting with an empty dictionary.")
            return {}
    return {}

# Save users data to users.json
def save_users_data(users_data):
    try:
        with open(users_file_path, "w") as f:
            json.dump(users_data, f, indent=4)
    except IOError:
        logging.error("Error writing to users.json.")

def create_daily_devotionals():
    results = []
    batch_size = 100
    query = db.collection('users').limit(batch_size)
    last_doc = None

    users_data = load_users_data()  # Load stored user IDs

    while True:
        try:
            # Fetch a batch of users
            users_batch = list(query.stream())
        except DeadlineExceeded as e:
            logging.error(f"DeadlineExceeded while streaming users batch: {e}")
            break

        if not users_batch:
            break

        for user in users_batch:
            user_id = user.id

            # Skip user if already in users.json
            if user_id in users_data:
                logging.info(f"Skipping user {user_id}, already processed.")
                continue

            try:
                user_doc = db.collection('users').document(user_id).get()
            except DeadlineExceeded as e:
                logging.error(f"DeadlineExceeded fetching document for user {user_id}: {e}")
                results.append({"user_id": user_id, "status": "failure", "error": "Deadline exceeded on get()"})
                continue

            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_email = user_data.get('email')
                first_name = user_data.get('firstName', 'Member')

                if user_email:
                    try:
                        why_statement_docs = db.collection('whyStatements').where('forUser', '==', user_id).get()
                    except DeadlineExceeded as e:
                        logging.error(f"DeadlineExceeded fetching whyStatements for user {user_id}: {e}")
                        results.append({"user_id": user_id, "status": "failure", "error": "Deadline exceeded on whyStatements"})
                        continue

                    if not why_statement_docs:
                        logging.error(f"Why Statement not found for user {user_id}")
                        results.append({"user_id": user_id, "status": "failure", "error": "Why Statement not found"})
                        continue

                    why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')
                    if isinstance(why_statement, str):
                        why_statement = {"whyStatement": why_statement}

                    devotional_content = generate_devotional_content(first_name, why_statement)

                    if isinstance(devotional_content, str):
                        try:
                            devotional_content = json.loads(devotional_content)
                        except json.JSONDecodeError as e:
                            logging.error(f"Error parsing JSON from generate_devotional_content for user {user_id}: {e}")
                            devotional_content = {}

                    devotional_record = {
                        "title": devotional_content.get("title", ""),
                        "introduction": devotional_content.get("introduction", ""),
                        "verse": devotional_content.get("verse", ""),
                        "insight": devotional_content.get("insight", ""),
                        "life_application": devotional_content.get("life_application", ""),
                        "declaration": devotional_content.get("declaration", ""),
                        "prayer": devotional_content.get("prayer", ""),
                        "dateTimeCreated": datetime.now(pytz.UTC).isoformat(),
                        "doc_id": None,
                        "forUser": user_id,
                        "isFavorite": False,
                    }

                    # Compare emails in a case-insensitive manner.
                    if user_email.lower() == "me@b3po.io":
                        try:
                            devotional_ref = db.collection('devotionals').add(devotional_record)
                        except DeadlineExceeded as e:
                            logging.error(f"DeadlineExceeded adding devotional for user {user_id}: {e}")
                            results.append({"user_id": user_id, "status": "failure", "error": "Deadline exceeded on add()"})
                            continue
                        devotional_doc_id = devotional_ref[1].id

                        devotional_record["doc_id"] = devotional_doc_id
                        try:
                            db.collection('devotionals').document(devotional_doc_id).set(devotional_record)
                        except DeadlineExceeded as e:
                            logging.error(f"DeadlineExceeded setting devotional for user {user_id}: {e}")
                            results.append({"user_id": user_id, "status": "failure", "error": "Deadline exceeded on set()"})
                            continue

                    logging.info(devotional_record)
                    logging.info(f"Devotional uploaded for user {user_id} ({user_email})")
                    results.append({"user_id": user_id, "status": "success"})

                    # Save user_id to users.json to prevent duplication
                    users_data[user_id] = {"processed_at": datetime.now(pytz.UTC).isoformat()}
                    save_users_data(users_data)

                else:
                    logging.info(f"Skipping user {user_id} with missing email.")
            else:
                logging.error(f"User {user_id} does not exist in the database")
                results.append({"user_id": user_id, "status": "not_found"})

        # Prepare for the next batch using pagination
        last_doc = users_batch[-1]
        query = db.collection('users').order_by('__name__').start_after(last_doc).limit(batch_size)

    return {"message": "Devotionals created successfully", "results": results}

def lambda_handler(event, context):
    response = create_daily_devotionals()
    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }

if __name__ == "__main__":
    response = create_daily_devotionals()
    logging.info(response)
