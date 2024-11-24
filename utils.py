# fix our path to import the firebase module using os and changing the path to the correct one
import os
import sys

# Add the parent directory to sys.path so it can find the 'firebase' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from firebase.firebase_admin_sdk import db

def build_user_data(user_id):
    # Fetch user document from 'users' collection
    user_doc = db.collection('users').document(user_id).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_email = user_data.get('email')
        first_name = user_data.get('firstName', "").replace('"', '')  # Strip quotes from firstName
        
        # Additional checks for the email
        if user_email and not (user_email.startswith('test') or user_email.startswith('Test')):            
            # Fetch onboarding answers collection using correct collection name and field name
            onboarding_answers = db.collection('onboardingAnswers').where('userID', '==', user_id).stream()
            user_data['onboardingAnswers'] = []
            for answer in onboarding_answers:
                user_data['onboardingAnswers'].append(answer.to_dict())
                    
            # Fetch why statements collection using correct collection name and field name
            why_statements = db.collection('whyStatements').where('forUser', '==', user_id).stream()  # Changed to 'forUser' based on screenshot
            user_data['whyStatements'] = []
            for statement in why_statements:
                user_data['whyStatements'].append(statement.to_dict())

            return user_data
    
    return None

def __main__():
    # Get input from the console for a user id then log all of the data we gather for that id
    user_id = os.getenv("USER_ID")
    user_data = build_user_data(user_id)
    if user_data:
        print(user_data)
    else:
        print(f"No user data found for user id: {user_id}")

if __name__ == "__main__":
    __main__()
