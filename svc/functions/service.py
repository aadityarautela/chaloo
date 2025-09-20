from typing import Dict
import firebase_admin
from firebase_admin import db, credentials
import os

# DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL")
# if not firebase_admin._apps:  # prevents double initialization
#     firebase_admin.initialize_app(options={"databaseURL": DATABASE_URL})


def generate_itenary_prompt(user_response: Dict[str, any]) -> str:
    intenary_prompt = ""
    with open('promptTemplate.txt', 'r') as f:
        intenary_prompt = f.read()

    user_formated_answer = user_response.get("prompt", "")
    user_custom_prompt = user_response.get("answers", {}).get("additionalComments", "")
    maps_api_response = user_response.get("maps_api_response", "")

    intenary_prompt = intenary_prompt.replace("{formatted_user_answers} ", user_formated_answer)
    intenary_prompt = intenary_prompt.replace("{custom_user_requests_if_any}", user_custom_prompt)
    intenary_prompt = intenary_prompt.replace("{weather_data_if_any}", maps_api_response)

    return intenary_prompt


def update_user(user_id: str, data: dict):
    """Service to save user inputs in DB (without itinerary)."""

    prompt = data.get("prompt", "")
    answers = data.get("answers", {})

    ref = db.reference(f"users/{user_id}")
    ref.update({
        "prompt": prompt,
        "answers": answers,
    })
    return ref


def update_itenary_in_db(user_id: str, itenary: str):
    """Service to save itinerary in DB."""
    ref = db.reference(f"users/{user_id}")
    ref.update({
        "itenary": itenary
    })

    # def write_to_db():

    # if __name__ == "__main__":
    # user_response = {
    #     "prompt": "I'm planning to visit Paris. I have 3 days for my trip.",
    #     "additionalContext": "Include at least one wine-tasting and a sunset spot.",
    #     "answers": {
    #         "destination_city": "Paris",
    #         "travel_time_days": 3
    #     }
    # }
#     print(generate_itenary_prompt(user_response))

