import os
import requests
import googlemaps
from datetime import datetime
import json
import math

# --- Environment Variables ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')
USER_MESSAGE = os.getenv('USER_MESSAGE')

# --- Load Metro Data ---
try:
    with open('metro_data.json', 'r') as f:
        metro_data = json.load(f)
except FileNotFoundError:
    metro_data = None

# --- Initialize Google Maps Client ---
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def send_telegram_message(text):
    """Sends a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

def get_metro_options(origin_coords, dest_coords):
    """Calculates the best metro route based on proximity to stations."""
    if not metro_data:
        return ""

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of Earth in kilometers
        dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Find the nearest stations to origin and destination
    stations = metro_data['stations']
    start_station = min(stations, key=lambda s: haversine(origin_coords['lat'], origin_coords['lng'], s['lat'], s['lon']))
    end_station = min(stations, key=lambda s: haversine(dest_coords['lat'], dest_coords['lng'], s['lat'], s['lon']))

    # If stations are too far from the points, metro is not a good option
    if haversine(origin_coords['lat'], origin_coords['lng'], start_station['lat'], start_station['lon']) > 3:
        return "" # More than 3km from nearest station

    # Simplified fare and time calculation
    # Fare: Min ₹10, Max ₹60. Approx ₹5 per station.
    # Time: Approx 3 mins per station + 15 mins wait/walk time.
    interchange = metro_data['interchange']
    
    if start_station['name'] == end_station['name']:
        return "" # No metro travel needed

    if start_station['line'] == end_station['line'] or start_station['line'] == 'Both' or end_station['line'] == 'Both':
        num_stations = abs(start_station['id'] - end_station['id'])
        route_desc = f"from *{start_station['name']}* to *{end_station['name']}*"
    else: # Requires interchange
        interchange_station = next(s for s in stations if s['name'] == interchange)
        num_stations = abs(start_station['id'] - interchange_station['id']) + abs(interchange_station['id'] - end_station['id'])
        route_desc = f"from *{start_station['name']}* to *{end_station['name']}* (via {interchange})"

    fare = min(10 + (num_stations - 1) * 5, 60)
    time = num_stations * 3 + 15

    return (
        f"🚇 *Metro Option*\n"
        f"   - *Route:* {route_desc}\n"
        f"   - *Est. Time:* ~{time} min\n"
        f"   - *Est. Fare:* ₹{fare:.0f}\n"
    )

def get_cab_auto_options(origin, destination, directions_result):
    """Formats the cab/auto options."""
    if not directions_result:
        return "Could not find driving directions."

    leg = directions_result[0]['legs'][0]
    duration = leg['duration']['text']
    distance = leg['distance']['text']
    
    dist_km = float(distance.replace(' km', ''))
    auto_fare = 30 + (dist_km * 15)
    cab_fare = 70 + (dist_km * 20)
    
    return (
        f"🚗 *Cab/Auto Estimate*\n"
        f"   - *Travel Time:* {duration}\n"
        f"   - *Distance:* {distance}\n"
        f"   - *Est. Auto Fare:* ₹{auto_fare:.0f} - ₹{auto_fare + 30:.0f}\n"
        f"   - *Est. Cab Fare:* ₹{cab_fare:.0f} - ₹{cab_fare + 50:.0f}\n"
    )

if __name__ == "__main__":
    if not all([TELEGRAM_BOT_TOKEN, GOOGLE_API_KEY, CHAT_ID, USER_MESSAGE]):
        print("Error: Missing one or more environment variables.")
        send_telegram_message("A configuration error occurred.")
    else:
        try:
            parts = USER_MESSAGE.split(" to ")
            if len(parts) == 2:
                origin_loc, dest_loc = parts[0].strip(), parts[1].strip()
                send_telegram_message(f"Searching for routes from *{origin_loc.title()}* to *{dest_loc.title()}*...")
                
                # Get directions and coordinates from Google Maps
                now = datetime.now()
                directions_result = gmaps.directions(origin_loc, dest_loc, mode="driving", region="in", departure_time=now)
                
                # Build the final response
                cab_info = get_cab_auto_options(origin_loc, dest_loc, directions_result)
                
                origin_coords = directions_result[0]['legs'][0]['start_location']
                dest_coords = directions_result[0]['legs'][0]['end_location']
                metro_info = get_metro_options(origin_coords, dest_coords)
                
                final_response = f"📍 *Route: {origin_loc.title()} to {dest_loc.title()}*\n---------------------------------------\n"
                final_response += cab_info
                if metro_info:
                    final_response += "\n" + metro_info

                send_telegram_message(final_response)
            else:
                send_telegram_message("Please format your request as: `Origin to Destination`.")
        except Exception as e:
            print(f"An error occurred during execution: {e}")
            send_telegram_message("Oops! Something went wrong. Please try again.")
