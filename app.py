import os
import sys
import json
import pytz
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from firebase_utils.firebase_admin_sdk import db
from generate_devotional import generate_devotional_content
from google.api_core.exceptions import DeadlineExceeded  # To catch timeout errors

load_dotenv()

today = datetime.now()
log_filename = f"./tmp/devotionals/{str(today.year)[-2:]}/{today.month}/daily_devotionals_{str(today.year)[-2:]}-{today.month}-{today.day}.log"
users_file_path = "./tmp/users.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

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

def is_valid_devotional(devotional):
    required_fields = [ "title", "introduction", "verse", "insight", "life_application", "declaration", "prayer"]
    return all(devotional.get(field) and devotional[field].strip() for field in required_fields)

def create_daily_devotionals():
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
                        continue

                    if not why_statement_docs:
                        logging.error(f"Why Statement not found for user {user_id}")
                        continue

                    why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')
                    if isinstance(why_statement, str):
                        why_statement = {"whyStatement": why_statement}

                    # Attempt to generate valid devotional content
                    attempts = 0
                    max_attempts = 2
                    devotional_content = {}

                    while attempts < max_attempts:
                        raw_content = generate_devotional_content(first_name, why_statement)

                        if isinstance(raw_content, str):
                            try:
                                devotional_content = json.loads(raw_content)
                            except json.JSONDecodeError as e:
                                logging.error(f"Error parsing JSON from generate_devotional_content for user {user_id}: {e}")
                                devotional_content = {}
                        else:
                            devotional_content = raw_content

                        if is_valid_devotional(devotional_content):
                            break

                        logging.warning(f"Generated devotional content for user {user_id} is incomplete or invalid. Retrying...")
                        devotional_content = {}
                        attempts += 1

                    if not is_valid_devotional(devotional_content):
                        logging.error(f"Failed to generate valid devotional content for user {user_id} after {max_attempts} attempts.")
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
                        "doc_id": None,
                        "forUser": user_id,
                        "isFavorite": False,
                    }

                    try:
                        devotional_ref = db.collection('devotionals').add(devotional_record)
                    except DeadlineExceeded as e:
                        logging.error(f"DeadlineExceeded adding devotional for user {user_id}: {e}")
                        continue
        
                    devotional_doc_id = devotional_ref[1].id

                    devotional_record["doc_id"] = devotional_doc_id
                    try:
                        db.collection('devotionals').document(devotional_doc_id).set(devotional_record)
                    except DeadlineExceeded as e:
                        logging.error(f"DeadlineExceeded setting devotional for user {user_id}: {e}")
                        continue

                    #logging.info(devotional_record)
                    logging.info(f"Devotional uploaded for user {user_id} ({user_email})")

                    # Save user_id to users.json to prevent duplication
                    users_data[user_id] = {"processed_at": datetime.now(pytz.UTC).isoformat()}
                    save_users_data(users_data)
                    trigger_email(user_email, devotional_content.get("introduction", ""))
                else:
                    logging.info(f"Skipping user {user_id}")

            else:
                logging.error(f"User {user_id} does not exist in the database")

        # Prepare for the next batch using pagination
        last_doc = users_batch[-1]
        query = db.collection('users').order_by('__name__').start_after(last_doc).limit(batch_size)

    return {"message": "Devotionals created successfully"}

def trigger_email(email, devotional_data):
    access_token = os.getenv("KEAP_API_KEY")

    contact_id = get_keap_contact_id(access_token, email)
    if contact_id:
        logging.info(f"Contact ID for {email}: {contact_id}")
        update_keap_contact_field(contact_id, devotional_data, access_token)
        # print(f"Keap Update Contact Response: {update_contact_field}")
        keap_response = trigger_keap_devotional_email(contact_id, access_token)
        logging.info(f"Keap Email Trigger Response: {keap_response}")
    else:
        logging.info(f"No contact found for {email}")

def get_keap_contact_id(access_token: str, email: str):
    """
    Searches Keap for a contact by email and returns the contact ID.
    """
    url = "https://api.infusionsoft.com/crm/rest/v1/contacts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "email": email,  # Search by email
        "optional_properties": ["email_addresses"]  # Include email fields in response
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if "contacts" in data and len(data["contacts"]) > 0:
            return data["contacts"][0]["id"]  # Return first match's ID
        else:
            return None  # No contact found
    else:
        return {"error": response.status_code, "message": response.text}
    

def update_keap_contact_field(contact_id, devotiona_data, access_token):
    """
    Updates a custom field (ID 695) for a specific contact in Keap.
    """
    if contact_id <= 0:
        return {"error": "Invalid contact_id. Must be greater than 0."}

    url = f"https://api.infusionsoft.com/crm/rest/v1/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "custom_fields": [
            {
                "content": devotiona_data,
                "id": 695
            }
        ]
    }

    response = requests.patch(url, json=payload, headers=headers)
    
    return response.json() if response.status_code in [200, 201] else response.text
    

def trigger_keap_devotional_email(contact_id, access_token):
    """
    Triggers the Keap API devotional for a given contact ID.
    """
    if contact_id > 0:
        url = "https://api.infusionsoft.com/crm/rest/v1/campaigns/goals/is104/sendlsdevotional"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"contact_id": contact_id}

        response = requests.post(url, json=payload, headers=headers)
        
        return response.json() if response.status_code == 200 else response.text
    else:
        return {"error": "Invalid contact_id. Must be greater than 0."}


if __name__ == "__main__":
    response = create_daily_devotionals()
    logging.info(response)
