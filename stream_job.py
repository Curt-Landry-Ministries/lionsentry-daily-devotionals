import os
import sys
import json
import pytz
import logging
from datetime import datetime
from dotenv import load_dotenv
from firebase_utils.firebase_admin_sdk import db
from generate_stream_devotional import generate_devotional_content
from google.api_core.exceptions import DeadlineExceeded

load_dotenv()

today = datetime.now()
log_filename = f"./tmp/devotionals/{str(today.year)[-2:]}/{today.month}/daily_batch_devotionals_{str(today.year)[-2:]}-{today.month}-{today.day}.log"
users_file_path = "./tmp/batch_users.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_users_data():
    if os.path.exists(users_file_path):
        try:
            with open(users_file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logging.error("Error reading users.json, starting with an empty dictionary.")
            return {}
    return {}

def save_users_data(users_data):
    try:
        with open(users_file_path, "w") as f:
            json.dump(users_data, f, indent=4)
    except IOError:
        logging.error("Error writing to users.json.")

def is_valid_devotional(devotional):
    required_fields = [
        "title", "introduction", "verse", "insight",
        "life_application", "declaration", "prayer"
    ]
    return all(devotional.get(field) and devotional[field].strip() for field in required_fields)

def create_daily_devotionals():
    results = []
    batch_size = 100
    query = db.collection('users').limit(batch_size)
    last_doc = None

    users_data = load_users_data()

    while True:
        try:
            users_batch = list(query.stream())
        except DeadlineExceeded as e:
            logging.error(f"DeadlineExceeded while streaming users batch: {e}")
            break

        if not users_batch:
            break

        for user in users_batch:
            user_id = user.id

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

                    if not is_valid_devotional(devotional_content):
                        logging.error(f"Failed to generate valid devotional content for user {user_id}.")
                        results.append({"user_id": user_id, "status": "failure", "error": "Invalid devotional content"})
                        continue

                    devotional_record = {
                        "title": devotional_content.get("title", ""),
                        "introduction": devotional_content.get("introduction", ""),
                        "verse": devotional_content.get("verse", ""),
                        "insight": devotional_content.get("insight", ""),
                        "life_application": devotional_content.get("life_application", ""),
                        "declaration": devotional_content.get("declaration", ""),
                        "prayer": devotional_content.get("prayer", ""),
                        "dateTimeCreated": datetime.now(pytz.UTC).isoformat(),
                        "forDate": datetime.now(pytz.UTC).strftime("%Y-%m-%d"),
                        "doc_id": None,
                        "forUser": user_id,
                        "isFavorite": False,
                    }

                    try:
                        devotional_ref = db.collection('devotionals').document()
                        devotional_record["doc_id"] = devotional_ref.id
                        devotional_ref.set(devotional_record)
                    except DeadlineExceeded as e:
                        logging.error(f"DeadlineExceeded saving devotional for user {user_id}: {e}")
                        results.append({"user_id": user_id, "status": "failure", "error": "Deadline exceeded on set()"})
                        continue

                    logging.info(devotional_record)
                    logging.info(f"Devotional uploaded for user {user_id} ({user_email})")
                    results.append({"user_id": user_id, "status": "success"})

                    users_data[user_id] = {"processed_at": datetime.now(pytz.UTC).isoformat()}
                    save_users_data(users_data)

                else:
                    logging.info(f"Skipping user {user_id} with missing email.")
            else:
                logging.error(f"User {user_id} does not exist in the database")
                results.append({"user_id": user_id, "status": "not_found"})

        last_doc = users_batch[-1]
        query = db.collection('users').order_by('__name__').start_after(last_doc).limit(batch_size)

    return {"message": "Devotionals created successfully", "results": results}


if __name__ == "__main__":
    response = create_daily_devotionals()
    logging.info(response)
