import os
import requests
import googlemaps
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')
USER_MESSAGE = os.getenv('USER_MESSAGE')

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def send_telegram_message(text):
    """Sends a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

def get_commute_options(origin, destination):
    """Fetches commute options using Google Maps API and provides estimates."""
    try:
        now = datetime.now()
        directions_result = gmaps.directions(origin,
                                             destination,
                                             mode="driving",
                                             region="in", 
                                             departure_time=now)
        
        if not directions_result:
            return "Could not find driving directions. Please check if the locations are correct."

        leg = directions_result[0]['legs'][0]
        duration = leg['duration']['text']
        distance = leg['distance']['text']
        
        dist_km = float(distance.replace(' km', ''))
        auto_fare = 30 + (dist_km * 15)
        cab_fare = 70 + (dist_km * 20)
        
        response = (
            f"📍 *Route: {origin.title()} to {destination.title()}*\n"
            f"---------------------------------------\n"
            f"🚗 *Cab/Auto Estimate*\n"
            f"   - *Travel Time:* {duration}\n"
            f"   - *Distance:* {distance}\n"
            f"   - *Est. Auto Fare:* ₹{auto_fare:.0f} - ₹{auto_fare + 30:.0f}\n"
             f"   - *Est. Metro Fare:* ₹{metro_fare:.0f} - ₹{metro_fare + 45:.0f}\n"
            f"   - *Est. Cab Fare:* ₹{cab_fare:.0f} - ₹{cab_fare + 50:.0f}\n\n"
            f"_(Full Bus and Metro data coming soon!)_"
        )
        return response

    except Exception as e:
        print(f"Error with Google Maps API: {e}")
        return f"Sorry, I couldn't fetch commute data for '{origin}' to '{destination}'. Please try again."

if __name__ == "__main__":
    if not all([TELEGRAM_BOT_TOKEN, GOOGLE_API_KEY, CHAT_ID, USER_MESSAGE]):
        print("Error: Missing one or more environment variables.")
        send_telegram_message("A configuration error occurred. Please contact the administrator.")
    else:
        try:
            parts = USER_MESSAGE.split(" to ")
            if len(parts) == 2:
                origin_loc = parts[0].strip()
                destination_loc = parts[1].strip()
                
                send_telegram_message(f"Searching for routes from *{origin_loc.title()}* to *{destination_loc.title()}*...")
                
                final_response = get_commute_options(origin_loc, destination_loc)
                send_telegram_message(final_response)
            else:
                send_telegram_message("Please format your request as: `Origin to Destination` (e.g., `Koramangala to Majestic`).")
        except Exception as e:
            print(f"An error occurred during execution: {e}")
            send_telegram_message("Oops! Something went wrong. Please try again.")
