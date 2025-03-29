import os
import requests
from dotenv import load_dotenv

load_dotenv()

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
    

def update_keap_contact_field(contact_id, devotional_content, access_token):
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
                "content": devotional_content,
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




def main():

    # Example usage
    access_token = os.getenv("KEAP_API_KEY")
    email = ""

    contact_id = get_keap_contact_id(access_token, email)
    if contact_id:
        print(f"Contact ID for {email}: {contact_id}")
        update_contact_field = update_keap_contact_field(contact_id, "Worship each day", access_token)
        print(f"Keap Update Contact Response: {update_contact_field}")
        keap_response = trigger_keap_devotional_email(contact_id, access_token)
        print(f"Keap Email Trigger Response: {keap_response}")
    else:
        print(f"No contact found for {email}")


if __name__ == "__main__": main()
