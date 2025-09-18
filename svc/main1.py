import logging
from firebase_functions import https_fn
from firebase_admin import initialize_app
import vertexai
from vertexai.generative_models import GenerativeModel

# This is a good practice for Cloud Functions
logging.basicConfig(level=logging.INFO)
initialize_app()

PROJECT_ID = "ai-planner-backend-qwerty"
LOCATION = "us-central1"

# --- CHANGE 1: THE FUNCTION NAME IS NOW 'generate_itinerary' ---
# It's better to have a descriptive name.
@https_fn.on_call()
def generate_itinerary(req: https_fn.CallableRequest) -> any:
    # --- CHANGE 2: USE THE CORRECT TYPE HINT 'CallableRequest' ---
    # This is the correct signature for an on_call function.

    logging.info(f"Function triggered. Request data: {req.data}")

    # Lazy initialization of Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # --- CHANGE 3: USE THE MOST STABLE AND WIDELY AVAILABLE MODEL ---
    model = GenerativeModel("gemini-2.0-flash-001")

    try:
        # For a CallableRequest, data is directly in req.data
        if not req.data or "destination" not in req.data:
            logging.error("Request data is missing or malformed.")
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Request must include a 'destination' key.",
            )
        
        destination = req.data["destination"]
        logging.info(f"Input destination: {destination}")
        
        prompt = f"Create a simple 3-day travel itinerary for {destination}. Be concise."
        
        response = model.generate_content(prompt)
        # start chat 
        
        logging.info("Successfully generated itinerary.")
        # Return a simple dictionary, which will be automatically converted to JSON
        return {"itinerary": response.text}

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to generate itinerary.",
        )