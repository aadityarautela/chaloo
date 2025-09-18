import logging
from firebase_functions import https_fn
from firebase_admin import initialize_app
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content

# This is a good practice for Cloud Functions
logging.basicConfig(level=logging.INFO)
initialize_app()

PROJECT_ID = "ai-planner-backend-qwerty"
LOCATION = "us-central1"

# Initialize Vertex AI and the model once to be reused across function invocations
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-001")

@https_fn.on_call()
def generate_itinerary(req: https_fn.CallableRequest) -> any:
    """A stateless function to generate a new itinerary from a single prompt."""
    logging.info(f"Function 'generate_itinerary' triggered. Request data: {req.data}")

    try:
        if not req.data or "destination" not in req.data:
            logging.error("Request data is missing 'destination'.")
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Request must include a 'destination' key.",
            )
        
        destination = req.data["destination"]
        logging.info(f"Input destination: {destination}")
        
        prompt = f"Create a simple 3-day travel itinerary for {destination}. Be concise."
        
        chat = model.start_chat()
        response = chat.send_message(prompt)
        
        logging.info("Successfully generated itinerary.")
        return {"itinerary": response.text}

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to generate itinerary.",
        )

@https_fn.on_call()
def gen_itinerary_chat(req: https_fn.CallableRequest) -> any:
    """A stateful chat function to have a conversation about an itinerary."""
    logging.info(f"Function 'gen_itinerary_chat' triggered. Request data: {req.data}")
    
    try:
        if not req.data or "prompt" not in req.data:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Request must include a 'prompt' key.",
            )
        
        prompt = req.data["prompt"]
        # History is optional, defaults to an empty list for a new chat
        history_data = req.data.get("history", [])

        history = [Content.from_dict(item) for item in history_data]

        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        
        logging.info("Successfully received chat response.")
        
        # Extract the updated history to send back to the client
        updated_history = [
            {'parts': [{'text': message.parts[0].text}], 'role': message.role}
            for message in chat.history
        ]

        return {
            "response": response.text,
            "history": updated_history
        }

    except Exception as e:
        logging.error(f"An error occurred in chat function: {e}", exc_info=True)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to process chat message.",
        )