import logging
from firebase_functions import https_fn
from firebase_admin import initialize_app
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from service import *

# This is a good practice for Cloud Functions
logging.basicConfig(level=logging.INFO)
DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL")
if not firebase_admin._apps:  # prevents double initialization
    firebase_admin.initialize_app(options={"databaseURL": DATABASE_URL})


PROJECT_ID = "ai-planner-backend-qwerty"
LOCATION = "us-central1"

# Initialize Vertex AI and the model once to be reused across function invocations
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-001")

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
        
        # Constant Userid
        user_id = "user69"

        data = {
            "prompt": req.data["prompt"],
            "answers": req.data["answers"]
        }
        
        # Updating DB with User Response
        update_user(user_id, data)

        #Verify min required vars and call maps api
        required_keys = [
            "destination_city",  # Key 1
            "travel_dates"  # Key 2
        ]
        answers = data["answers"]
        if all(key in answers for key in required_keys):
            logging.info("All required keys are present in 'answers'.")
            #Call maps API to get additional context

        data["maps_api_response"] = "" #replace it with actual response if any

        #Generate Itenary Prompt
        itenary_prompt = generate_itenary_prompt(data)


        # LLM Call with Internary Prompt only if User Prompt is not empty.
        response = ""
        if "prompt" in data and data["prompt"] is not None:
            chat = model.start_chat(history=[])
            response = chat.send_message(itenary_prompt)
        
        logging.info("Successfully received chat response.")

        #Updating entry in the DB
        update_itenary_in_db(user_id, response.text)
        
        # # Extract the updated history to send back to the client
        # updated_history = [
        #     {'parts': [{'text': message.parts[0].text}], 'role': message.role}
        #     for message in chat.history
        # ]

        return {
            "response": response.text,
        }

    except Exception as e:
        logging.error(f"An error occurred in chat function: {e}", exc_info=True)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to process chat message.",
        )