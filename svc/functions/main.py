import logging
import os
import time

from firebase_functions import https_fn
from firebase_admin import initialize_app
import firebase_admin

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from service import *

# Import the Google Cloud Logging library
import google.cloud.logging

# --- LAZY INITIALIZATION SETUP ---
# Declare clients and models in the global scope, but initialize them as None.
# They will be initialized on the first function invocation.
firebase_app = None
vertexai_model = None
logging_client = None


def _initialize_globals():
    """
    Initializes all global clients and models if they haven't been already.
    This function is called at the beginning of the main function handler.
    """
    global firebase_app, vertexai_model, logging_client

    # Set up logging first
    if logging_client is None:
        logging.info("Initializing Google Cloud Logging client...")
        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging()
        logging.info("Google Cloud Logging client initialized.")

    # Initialize Firebase
    if not firebase_admin._apps:
        logging.info("Initializing Firebase app...")
        DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL")
        logging.info(f"DATABASE_URL from env: {DATABASE_URL}")
        firebase_app = firebase_admin.initialize_app(options={"databaseURL": DATABASE_URL})
        logging.info("Firebase app initialized.")
    else:
        logging.info("Firebase app already initialized.")

    # Initialize Vertex AI
    if vertexai_model is None:
        PROJECT_ID = "ai-planner-backend-qwerty"
        LOCATION = "us-central1"
        logging.info(f"Initializing Vertex AI with project: {PROJECT_ID}, location: {LOCATION}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logging.info("Vertex AI initialized.")
        vertexai_model = GenerativeModel("gemini-2.0-flash-001")
        logging.info("GenerativeModel 'gemini-2.0-flash-001' initialized.")


@https_fn.on_call()
def gen_itinerary_chat(req: https_fn.CallableRequest) -> any:
    """A stateful chat function to have a conversation about an itinerary."""
    # This is the key: Initialize everything on the first run.
    _initialize_globals()

    logging.info("gen_itinerary_chat called.")
    logging.info(f"Request data: {req.data}")

    try:
        if not req.data:
            logging.info("No request data received.")
        if not req.data or "prompt" not in req.data:
            logging.info("Request missing 'prompt' key.")
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Request must include a 'prompt' key.",
            )

        # Constant Userid
        user_id = "user69"
        logging.info(f"Using user_id: {user_id}")

        data = {
            "prompt": req.data["prompt"],
            "answers": req.data["answers"]
        }
        logging.info(f"User data: {data}")

        # Updating DB with User Response
        logging.info("Updating user in DB with response data...")
        update_user(user_id, data)
        logging.info("User DB update complete.")

        # Verify min required vars and call maps api
        required_keys = [
            "destination_city",  # Key 1
            "travel_dates"  # Key 2
        ]
        answers = data["answers"]
        logging.info(f"Answers received: {answers}")

        if all(key in answers for key in required_keys):
            logging.info("All required keys are present in 'answers'.")
            # Call Maps API to get additional context
            try:
                logging.info("Calling Google Maps API...")
                data["maps_api_response"] = get_maps_api_context(
                    destination=answers["destination_city"],
                    answers=answers
                )
                logging.info(f"Maps API response: {data['maps_api_response']}")
                logging.info(f"Maps API response length: {len(data['maps_api_response'])} characters")
            except Exception as e:
                logging.error(f"Maps API call failed: {e}")
                data["maps_api_response"] = "Maps context unavailable due to API error."
        else:
            missing_keys = [key for key in required_keys if key not in answers]
            logging.info(f"Missing required keys: {missing_keys}")
            data["maps_api_response"] = "Insufficient information for Maps API context."

        # Generate Itinerary Prompt
        logging.info("Generating itinerary prompt...")
        itinerary_prompt = generate_itenary_prompt(data)
        logging.info(f"Itinerary prompt: {itinerary_prompt}")

        # LLM Call with Itinerary Prompt only if User Prompt is not empty.
        response = ""
        if data.get("prompt", "").strip():
            logging.info("Prompt is not empty. Starting chat with model...")
            chat = vertexai_model.start_chat(history=[]) # Use the lazily-initialized model
            logging.info("Chat started. Sending message to model...")
            response = chat.send_message(itinerary_prompt)
            logging.info(f"Model response: {response.text}")
            logging.info("Successfully received chat response.")
        else:
            logging.info("Empty prompt, skipping AI generation")
            return {"response": "Please provide travel preferences to generate an itinerary."}

        # Updating entry in the DB
        logging.info("Updating itinerary in DB...")
        update_itenary_in_db(user_id, response.text)
        logging.info("Itinerary DB update complete.")

        logging.info("Returning response to client.")
        return {
            "response": response.text,
        }

    except Exception as e:
        logging.error(f"An error occurred in chat function: {e}", exc_info=True)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to process chat message.",
        )