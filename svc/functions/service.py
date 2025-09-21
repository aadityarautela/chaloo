from typing import Dict, List, Any, Optional
from firebase_admin import db
import requests
import logging
# from google.cloud import secretmanager

# DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL")
# if not firebase_admin._apps:  # prevents double initialization
#     firebase_admin.initialize_app(options={"databaseURL": DATABASE_URL})


def generate_itenary_prompt(user_response: Dict[str, any]) -> str:
    logging.info("Generating itinerary prompt...")
    intenary_prompt = ""
    try:
        with open('promptTemplate.txt', 'r') as f:
            intenary_prompt = f.read()
        logging.info("Loaded prompt template from file.")
    except Exception as e:
        logging.error(f"Error loading prompt template: {e}")
        return ""

    user_formated_answer = user_response.get("prompt", "")
    user_custom_prompt = user_response.get("answers", {}).get("additionalComments", "")
    maps_api_response = user_response.get("maps_api_response", "")

    logging.info(f"User formatted answer: {user_formated_answer}")
    logging.info(f"User custom prompt: {user_custom_prompt}")
    logging.info(f"Maps API response: {maps_api_response}")

    intenary_prompt = intenary_prompt.replace("{formatted_user_answers} ", user_formated_answer)
    intenary_prompt = intenary_prompt.replace("{custom_user_requests_if_any}", user_custom_prompt)
    intenary_prompt = intenary_prompt.replace("{weather_data_if_any}", maps_api_response)

    logging.info("Itinerary prompt generated.")
    return intenary_prompt


def update_user(user_id: str, data: dict):
    """Service to save user inputs in DB (without itinerary)."""
    logging.info(f"Updating user {user_id} in DB...")
    prompt = data.get("prompt", "")
    answers = data.get("answers", {})
    logging.info(f"Prompt: {prompt}")
    logging.info(f"Answers: {answers}")
    ref = db.reference(f"users/{user_id}")
    ref.update({
        "prompt": prompt,
        "answers": answers,
    })
    logging.info(f"User {user_id} updated in DB.")
    return ref


def update_itenary_in_db(user_id: str, itenary: str):
    """Service to save itinerary in DB."""
    logging.info(f"Updating itinerary for user {user_id} in DB...")
    ref = db.reference(f"users/{user_id}")
    ref.update({
        "itenary": itenary
    })
    logging.info(f"Itinerary for user {user_id} updated in DB.")

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


# def get_secret(secret_id: str) -> str:
#     client = secretmanager.SecretManagerServiceClient()
#     name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
#     response = client.access_secret_version(request={"name": name})
#     return response.payload.data.decode("UTF-8")

# Usage
# GOOGLE_MAPS_API_KEY = get_secret("google-maps-api-key")
GOOGLE_MAPS_API_KEY = DATABASE_URL = 'AIzaSyAikS8o8_bpgPGM-4Adlb5ggHXhRhvEvco'

def get_destination_coordinates(destination: str) -> Optional[Dict[str, float]]:
    """Get latitude and longitude coordinates for a destination."""
    logging.info(f"Getting coordinates for destination: {destination}")
    try:
        if not GOOGLE_MAPS_API_KEY:
            logging.info("Google Maps API key not configured")
            return None
        geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': destination,
            'key': GOOGLE_MAPS_API_KEY
        }
        logging.info(f"Requesting geocoding for {destination}...")
        response = requests.get(geocoding_url, params=params)
        data = response.json()
        logging.info(f"Geocoding API response: {data}")
        if data.get('status') == 'OK' and data.get('results'):
            location = data['results'][0]['geometry']['location']
            logging.info(f"Coordinates found: {location}")
            return {
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
        else:
            logging.info(f"Geocoding failed for {destination}: {data.get('status')}")
            return None
    except Exception as e:
        logging.error(f"Error getting coordinates for {destination}: {e}")
        return None

def get_place_details(destination: str) -> Dict[str, Any]:
    """Get detailed information about the destination."""
    logging.info(f"Getting place details for destination: {destination}")
    try:
        if not GOOGLE_MAPS_API_KEY:
            logging.info("Google Maps API key not configured")
            return {}
        # First search for the place
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            'query': destination,
            'key': GOOGLE_MAPS_API_KEY
        }
        logging.info(f"Requesting place search for {destination}...")
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        logging.info(f"Place search API response: {search_data}")
        if not search_data.get('results'):
            logging.info(f"No place found for destination: {destination}")
            return {}
        place = search_data['results'][0]
        place_id = place.get('place_id')
        logging.info(f"Place ID: {place_id}")
        if not place_id:
            logging.info("No place_id found, returning basic place info.")
            return {
                'name': place.get('name', destination),
                'formatted_address': place.get('formatted_address', ''),
                'rating': place.get('rating'),
                'types': place.get('types', [])
            }
        # Get detailed information
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,types,rating,user_ratings_total,opening_hours,website,international_phone_number,reviews',
            'key': GOOGLE_MAPS_API_KEY
        }
        logging.info(f"Requesting place details for place_id: {place_id}")
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()
        logging.info(f"Place details API response: {details_data}")
        if details_data.get('status') == 'OK':
            result = details_data.get('result', {})
            logging.info(f"Detailed place info: {result}")
            return {
                'name': result.get('name', destination),
                'formatted_address': result.get('formatted_address', ''),
                'rating': result.get('rating'),
                'user_ratings_total': result.get('user_ratings_total'),
                'types': result.get('types', []),
                'website': result.get('website'),
                'phone': result.get('international_phone_number'),
                'opening_hours': result.get('opening_hours', {}).get('weekday_text', [])
            }
        logging.info("No detailed place info found.")
        return {}
    except Exception as e:
        logging.error(f"Error getting place details for {destination}: {e}")
        return {}

def get_nearby_attractions(destination: str, interests: List[str] = None, radius: int = 15000) -> List[Dict[str, Any]]:
    """Get nearby attractions based on user interests."""
    logging.info(f"Getting nearby attractions for destination: {destination}")
    try:
        if not GOOGLE_MAPS_API_KEY:
            logging.info("Google Maps API key not configured")
            return []
        # Get destination coordinates
        logging.info(f"Getting coordinates for {destination} to find nearby attractions...")
        coords = get_destination_coordinates(destination)
        if not coords:
            logging.info(f"No coordinates found for {destination}")
            return []
        lat, lng = coords['lat'], coords['lng']
        logging.info(f"Coordinates for {destination}: lat={lat}, lng={lng}")
        # Map interests to Google Places API types
        place_types = ['tourist_attraction', 'point_of_interest']
        if interests:
            logging.info(f"User interests: {interests}")
            interest_mapping = {
                'culture': ['museum', 'art_gallery', 'library'],
                'art': ['museum', 'art_gallery'],
                'nature': ['park', 'natural_feature', 'zoo'],
                'shopping': ['shopping_mall', 'department_store'],
                'nightlife': ['night_club', 'bar'],
                'food': ['restaurant'],
                'beaches': ['natural_feature'],
                'architecture': ['church', 'synagogue', 'hindu_temple', 'mosque']
            }
            for interest in interests:
                if interest in interest_mapping:
                    logging.info(f"Mapping interest '{interest}' to place types {interest_mapping[interest]}")
                    place_types.extend(interest_mapping[interest])
        attractions = []
        # Remove duplicates while preserving order
        place_types = list(dict.fromkeys(place_types))
        logging.info(f"Final place types for search: {place_types}")
        for place_type in place_types[:6]:  # Limit API calls
            logging.info(f"Searching for nearby places of type: {place_type}")
            nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': radius,
                'type': place_type,
                'key': GOOGLE_MAPS_API_KEY
            }
            response = requests.get(nearby_url, params=params)
            data = response.json()
            logging.info(f"Nearby search API response for type {place_type}: {data}")
            if data.get('results'):
                for result in data['results'][:4]:  # Top 4 per type
                    if result.get('rating', 0) >= 4.0:  # Only well-rated places
                        logging.info(f"Found attraction: {result.get('name')} (type: {place_type}, rating: {result.get('rating')})")
                        attractions.append({
                            'name': result.get('name'),
                            'type': place_type,
                            'rating': result.get('rating'),
                            'user_ratings_total': result.get('user_ratings_total'),
                            'vicinity': result.get('vicinity'),
                            'price_level': result.get('price_level'),
                            'photos': len(result.get('photos', [])) > 0
                        })
        # Sort by rating and limit total results
        logging.info(f"Sorting attractions by rating and user ratings total...")
        attractions.sort(key=lambda x: (x.get('rating', 0), x.get('user_ratings_total', 0)), reverse=True)
        logging.info(f"Returning top {min(15, len(attractions))} attractions.")
        return attractions[:15]
    except Exception as e:
        logging.error(f"Error getting attractions for {destination}: {e}")
        return []

def get_restaurants_by_preferences(destination: str, dietary_restrictions: List[str] = None, budget_level: str = None) -> List[Dict[str, Any]]:
    """Get restaurants filtered by dietary restrictions and budget level."""
    logging.info(f"Getting restaurants for destination: {destination}")
    try:
        if not GOOGLE_MAPS_API_KEY:
            logging.info("Google Maps API key not configured")
            return []
        restaurants = []
        search_queries = []
        # Build search queries based on dietary restrictions
        if dietary_restrictions and 'none' not in dietary_restrictions:
            logging.info(f"Dietary restrictions: {dietary_restrictions}")
            dietary_mapping = {
                'vegetarian': 'vegetarian restaurant',
                'vegan': 'vegan restaurant', 
                'halal': 'halal restaurant',
                'kosher': 'kosher restaurant',
                'gluten_free': 'gluten free restaurant'
            }
            for restriction in dietary_restrictions:
                if restriction in dietary_mapping:
                    logging.info(f"Adding search query for restriction: {restriction}")
                    search_queries.append(dietary_mapping[restriction])
        # Add general restaurant searches
        if budget_level:
            logging.info(f"Budget level: {budget_level}")
            budget_mapping = {
                'budget': 'cheap eats',
                'mid': 'mid-range restaurant',
                'luxury': 'fine dining restaurant',
                'flexible': 'popular restaurant'
            }
            if budget_level in budget_mapping:
                logging.info(f"Adding search query for budget: {budget_level}")
                search_queries.append(budget_mapping[budget_level])
        # Default searches if no specific preferences
        if not search_queries:
            logging.info("No specific preferences, using default restaurant queries.")
            search_queries = ['best restaurants', 'local cuisine', 'popular restaurants']
        # Limit to avoid too many API calls
        search_queries = search_queries[:4]
        logging.info(f"Final restaurant search queries: {search_queries}")
        for query in search_queries:
            logging.info(f"Searching for restaurants with query: {query}")
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                'query': f"{query} {destination}",
                'type': 'restaurant',
                'key': GOOGLE_MAPS_API_KEY
            }
            response = requests.get(search_url, params=params)
            data = response.json()
            logging.info(f"Restaurant search API response for query '{query}': {data}")
            if data.get('results'):
                for result in data['results'][:3]:  # Top 3 per query
                    if result.get('rating', 0) >= 4.0:  # Only well-rated restaurants
                        logging.info(f"Found restaurant: {result.get('name')} (rating: {result.get('rating')})")
                        restaurants.append({
                            'name': result.get('name'),
                            'rating': result.get('rating'),
                            'user_ratings_total': result.get('user_ratings_total'),
                            'price_level': result.get('price_level'),
                            'cuisine_type': query,
                            'formatted_address': result.get('formatted_address'),
                            'vicinity': result.get('vicinity')
                        })
        # Remove duplicates based on name and sort by rating
        logging.info("Removing duplicate restaurants and sorting by rating...")
        seen_names = set()
        unique_restaurants = []
        for restaurant in restaurants:
            if restaurant['name'] not in seen_names:
                seen_names.add(restaurant['name'])
                unique_restaurants.append(restaurant)
        unique_restaurants.sort(key=lambda x: (x.get('rating', 0), x.get('user_ratings_total', 0)), reverse=True)
        logging.info(f"Returning top {min(12, len(unique_restaurants))} restaurants.")
        return unique_restaurants[:12]
    except Exception as e:
        logging.error(f"Error getting restaurants for {destination}: {e}")
        return []

def get_maps_api_context(destination: str, answers: Dict[str, Any]) -> str:
    """Main function to get comprehensive Maps API context."""
    logging.info(f"Building Maps API context for destination: {destination}")
    try:
        if not GOOGLE_MAPS_API_KEY:
            logging.info("Google Maps API key not available")
            return "Google Maps integration not available."
        logging.info(f"Getting place details for {destination}...")
        place_details = get_place_details(destination)
        logging.info(f"Place details: {place_details}")
        interests = answers.get('interests', [])
        logging.info(f"User interests: {interests}")
        attractions = get_nearby_attractions(destination, interests)
        logging.info(f"Nearby attractions: {attractions}")
        dietary_restrictions = answers.get('dietary', [])
        budget_level = answers.get('budget_level', '')
        logging.info(f"Dietary restrictions: {dietary_restrictions}, Budget level: {budget_level}")
        restaurants = get_restaurants_by_preferences(destination, dietary_restrictions, budget_level)
        logging.info(f"Restaurants: {restaurants}")
        context_parts = []
        # Add place details
        if place_details:
            name = place_details.get('name', destination)
            address = place_details.get('formatted_address', '')
            rating = place_details.get('rating')
            place_info = f"Destination: {name}"
            if address:
                place_info += f" is located at {address}"
            if rating:
                place_info += f" (Rating: {rating}/5)"
            context_parts.append(place_info + ".")
            logging.info(f"Added place info to context: {place_info}")
        # Add top attractions
        if attractions:
            top_attractions = [attr['name'] for attr in attractions[:8] if attr.get('name')]
            if top_attractions:
                context_parts.append(f"Highly-rated attractions nearby: {', '.join(top_attractions)}.")
                logging.info(f"Added attractions to context: {top_attractions}")
        # Add restaurant recommendations
        if restaurants:
            restaurant_info = []
            for rest in restaurants[:6]:
                name = rest.get('name', '')
                rating = rest.get('rating', 0)
                price_level = rest.get('price_level', 0)
                price_indicator = '$' * max(1, min(price_level, 4)) if price_level else ''
                restaurant_info.append(f"{name} ({rating}★ {price_indicator})")
            if restaurant_info:
                context_parts.append(f"Recommended restaurants: {', '.join(restaurant_info)}.")
                logging.info(f"Added restaurants to context: {restaurant_info}")
        final_context = ' '.join(context_parts)
        logging.info(f"Generated Maps context: {final_context}")
        logging.info(f"Generated Maps context length: {len(final_context)} characters")
        return final_context if final_context.strip() else "Local context not available."
    except Exception as e:
        logging.error(f"Error building Maps context: {e}")
        return "Error retrieving local context."