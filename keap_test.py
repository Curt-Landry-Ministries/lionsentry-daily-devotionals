import os
import requests
from dotenv import load_dotenv

load_dotenv()

import requests

def send_keap_email_v2(access_token: str, contacts: list = None, send_to_addresses: list = None, cc_addresses: list = None):
    """
    Sends an email using Keap API v2.
    """
    url = "https://api.infusionsoft.com/crm/rest/v2/emails:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


    # Construct payload
    payload = {
        "address_field": "string",
        "contacts": [
            contacts
        ],
        "html_content": "string",
        "plain_content": "string",
        "subject": "string",
        "user_id": "string"
    }
    print(payload)

    # Add optional fields if provided
    if cc_addresses:
        payload["cc_addresses"] = cc_addresses

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}


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


def main():

    # Example usage
    access_token = os.getenv("KEAP_API_KEY")
    email = "tdunlavey@curtlandry.com"

    contact_id = get_keap_contact_id(access_token, email)
    if contact_id:
        print(f"Contact ID for {email}: {contact_id}")
        # Example usage
        contacts = contact_id  # Contact IDs from Keap (optional)
        send_to_addresses = ["lionsentry@curtlandry.com"]  # Direct email addresses (optional)
        subject = "Exciting News!"
        from_email = "lionsentry@curtlandry .com"
        from_name = "Lionsentry"
        cc_addresses = ["brandon@lionsentry.com"]

        response = send_keap_email_v2(access_token, contacts, send_to_addresses, subject, from_email, from_name, cc_addresses)
        print(response)
    else:
        print(f"No contact found for {email}")


if __name__ == "__main__": main()
