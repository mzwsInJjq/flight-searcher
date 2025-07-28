import re
import json
import datetime
import folium
from collections import deque
from folium.plugins import AntPath
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from FlightRadar24 import FlightRadar24API

fr_api = FlightRadar24API()
cached_fr24_results = ['', '']
cached_flight = deque(maxlen=1)

def get_local_time(airport_details=None, timezone_name=None):
    """
    Get the current local time for a given airport.
    airport_details: JSON object containing airport details from FlightRadar24 API
    timezone_name: Optional timezone name to use if not provided in airport_details.
    If neither is provided, returns "Not available".
    """
    if not airport_details and not timezone_name:
        return "Not available"
    
    try:
        if not timezone_name:
            timezone_name = airport_details['airport']['pluginData']['details']['timezone']['name']
        tz = ZoneInfo(timezone_name)
        local_time = datetime.datetime.now(tz)
        return local_time.strftime('%m-%d-%Y %I:%M%p')
    except (KeyError, ZoneInfoNotFoundError):
        return "Timezone not available"

def remove_parentheses(text):
    """
    Remove text within parentheses and the parentheses themselves from a string.
    """
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def convert_time_in_string(text: str) -> str:
    """
    Finds a 24-hour time (HH:MM) in a string and converts it to 12-hour format (e.g., 05:05PM).
    If no time is found, the original string is returned.

    Args:
        text: The input string, which may or may not contain a time.
              e.g., "Delayed 17:05", "Landed 09:30", "On time"

    Returns:
        The string with the time converted, or the original string.
    """
    # This regex finds a pattern of one or two digits, a colon, and two digits.
    # It's designed to match HH:MM or H:MM.
    time_pattern = re.compile(r'\b(\d{1,2}):(\d{2})\b')

    # The `sub` function finds the pattern and calls the lambda for each match.
    def replacer(match):
        time_str = match.group(0)  # The full matched string, e.g., "17:05"
        try:
            # Parse the found time string
            t = datetime.datetime.strptime(time_str, '%H:%M').time()
            # Format it to 12-hour format, e.g., "05:05PM"
            formatted_time = t.strftime('%I:%M%p')

            return formatted_time
        except ValueError:
            # If strptime fails (e.g., for "99:99"), return the original match
            return time_str

    return time_pattern.sub(replacer, text)

def get_airport_details(airport_code):
    try:
        airport_details = fr_api.get_airport_details(airport_code)
        cached_fr24_results[0] = json.dumps(airport_details, indent=2)
        return airport_details
    except Exception as e:
        print(f"The IATA / ICAO Code is invalid: {e}")
        return None

def airport_dep_board(airport_details):
    """
    Get the departure board for a given airport.
    airport_details: JSON object containing airport details from FlightRadar24 API"""
    if airport_details is None:
        return []
    
    try:
        timezone_name = airport_details['airport']['pluginData']['details']['timezone']['name']
        tz = ZoneInfo(timezone_name)
    except (KeyError, ZoneInfoNotFoundError):
        tz = None

    departures = airport_details['airport']['pluginData']['schedule']['departures']['data']
    if not departures:
        print("No departures found for this airport.")
        return []
    
    # Build a flat list of rows with departure details
    rows = []
    for dep_flight in departures:
        flight = dep_flight['flight']['identification']['number']['default'] if dep_flight['flight']['identification']['number']['default'] else ''
        airline = remove_parentheses(dep_flight['flight']['airline']['name']) if dep_flight['flight']['airline'] else ''
        destination_iata = dep_flight['flight']['airport']['destination']['code']['iata']
        # destination_name = dep_flight['flight']['airport']['destination']['name']
        destination_city = dep_flight['flight']['airport']['destination']['position']['region']['city']
        scheduled_departure = datetime.datetime.fromtimestamp(dep_flight['flight']['time']['scheduled']['departure'], tz=tz).strftime('%m-%d-%Y %I:%M%p')
        status = convert_time_in_string(dep_flight['flight']['status']['text'])
        terminal = dep_flight['flight']['airport']['origin']['info']['terminal'] if dep_flight['flight']['airport']['origin']['info']['terminal'] else ''
        gate = dep_flight['flight']['airport']['origin']['info']['gate'] if dep_flight['flight']['airport']['origin']['info']['gate'] else ''

        # Append the flight details to the rows list
        rows.append([
            destination_iata,
            destination_city,
            airline,
            flight,
            scheduled_departure,
            status,
            terminal,
            gate
        ])

    return rows

def airport_arr_board(airport_details):
    """
    Get the arrival board for a given airport.
    airport_details: JSON object containing airport details from FlightRadar24 API
    """
    if airport_details is None:
        return []
    
    try:
        timezone_name = airport_details['airport']['pluginData']['details']['timezone']['name']
        tz = ZoneInfo(timezone_name)
    except (KeyError, ZoneInfoNotFoundError):
        tz = None
    
    arrivals = airport_details['airport']['pluginData']['schedule']['arrivals']['data']
    if not arrivals:
        print("No arrivals found for this airport.")
        return []
    
    # Build a flat list of rows with arrival details
    rows = []
    for arr_flight in arrivals:
        flight = arr_flight['flight']['identification']['number']['default'] if arr_flight['flight']['identification']['number']['default'] else ''
        airline = remove_parentheses(arr_flight['flight']['airline']['name']) if arr_flight['flight']['airline'] else ''
        origin_iata = arr_flight['flight']['airport']['origin']['code']['iata']
        # origin_name = arr_flight['flight']['airport']['origin']['name']
        origin_city = arr_flight['flight']['airport']['origin']['position']['region']['city']
        scheduled_arrival = datetime.datetime.fromtimestamp(arr_flight['flight']['time']['scheduled']['arrival'], tz=tz).strftime('%m-%d-%Y %I:%M%p')
        status = convert_time_in_string(arr_flight['flight']['status']['text'])
        terminal = arr_flight['flight']['airport']['destination']['info']['terminal'] if arr_flight['flight']['airport']['destination']['info']['terminal'] else ''
        gate = arr_flight['flight']['airport']['destination']['info']['gate'] if arr_flight['flight']['airport']['destination']['info']['gate'] else ''

        # Append the flight details to the rows list
        rows.append([
            origin_iata,
            origin_city,
            airline,
            flight,
            scheduled_arrival,
            status,
            terminal,
            gate
        ])

    return rows

def delay_index(airport_details):
    """
    Get the delay index for a given airport.
    airport_details: JSON object containing airport details from FlightRadar24 API
    """
    if airport_details is None:
        return
    
    delay_index = airport_details['airport']['pluginData']['details']['delayIndex']
    arrivals = delay_index['arrivals']
    departures = delay_index['departures']

    return arrivals, departures

def weather(airport_details):
    """
    Get the weather for a given airport.
    airport_details: JSON object containing airport details from FlightRadar24 API
    """
    if airport_details is None:
        return
    
    weather = airport_details['airport']['pluginData']['weather']
    if not weather:
        print("No weather data found for this airport.")
        return None
    
    temp_c = weather['temp']['celsius']
    temp_f = weather['temp']['fahrenheit']
    condition = weather['sky']['condition']['text']
    humidity = weather['humidity']

    wind_speed_kmh = weather['wind']['speed']['kmh']
    wind_speed_mph = weather['wind']['speed']['mph']
    wind_speed_text = weather['wind']['speed']['text']
    wind_direction_degree = weather['wind']['direction']['degree']
    wind_direction_text = weather['wind']['direction']['text']

    visibility_km = weather['sky']['visibility']['km']
    visibility_miles = weather['sky']['visibility']['mi']

    return temp_c, temp_f, condition, humidity, wind_speed_kmh, wind_speed_mph, wind_speed_text, wind_direction_degree, wind_direction_text, visibility_km, visibility_miles

def get_flight_status(flight_id):
    """
    Get the status of a flight by its ID. This function now returns the full details dictionary.
    """
    flight_id = flight_id.strip().upper()
    
    flights = fr_api.get_flights(registration=flight_id)

    if not flights:
        flight_id = fr_api.search(flight_id)['live']
        if len(flight_id) == 0:
            cached_flight.clear()
            return "No live flight found."
        
        flight_id = flight_id[0]['label'].split(' ')[-1][1:-1]
        flights = fr_api.get_flights(registration=flight_id)

        if not flights:
            cached_flight.clear()
            return "No live flight found."

    # Get the first flight object from the list. This is a "summary" object.
    flight_obj = flights[0]
    
    try:
        # Fetch the full details dictionary using the summary object.
        details = fr_api.get_flight_details(flight_obj)
        
        # Apply the fetched details to the flight object to make it complete.
        flight_obj.set_flight_details(details)
        
        # Cache the fully detailed object and the raw JSON for export.
        cached_flight.append(flight_obj)
        cached_fr24_results[1] = json.dumps(details, indent=2)

        # For the text status, format some key info from the now-detailed object.
        status_text = f"""
        {flight_obj.callsign}
        {flight_obj.registration}
        {flight_obj.aircraft_code}
        Origin: {flight_obj.origin_airport_name} ({flight_obj.origin_airport_iata})
        Destination: {flight_obj.destination_airport_name} ({flight_obj.destination_airport_iata})
        Status: {convert_time_in_string(flight_obj.status_text)}
        """
        return status_text.strip()

    except Exception as e:
        print(f"Error fetching details for {flight_obj.id}: {e}")
        cached_flight.clear()
        return f"Could not retrieve details for flight {flight_id}."

def get_flight_map():
    flight = cached_flight[0] if cached_flight else None

    if not flight:
        return folium.Map(location=[0, 0], zoom_start=1)
    
    # The flight object in the cache is now fully detailed.
    # We can directly check for the 'trail' attribute.
    if not hasattr(flight, 'trail') or not flight.trail:
        print("Flight object has no trail data.")
        return folium.Map(location=[0, 0], zoom_start=1)
    
    # 1. Determine the longitude offset needed to prevent map wrapping.
    origin_lon = flight.origin_airport_longitude
    destination_lon = flight.destination_airport_longitude

    lon_diff = destination_lon - origin_lon

    # 2. Apply the calculated offset to all points in the trail.
    offset = 0
    if lon_diff > 180:
        offset = -360
    elif lon_diff < -180:
        offset = 360
    
    trail_coordinates = [(point['lat'], point['lng'] + offset * ((1 if point['lng'] >= 0 else 0) if offset == -360 else (1 if point['lng'] <= 0 else 0))) for point in flight.trail]

    # 3. Create the flight map with the adjusted trail coordinates.
    # print(f"offset: {offset} for {flight.callsign or flight.registration}")

    current_position = (trail_coordinates[0][0], trail_coordinates[0][1])
    
    flight_map = folium.Map(location=current_position, zoom_start=6, tiles="CartoDB positron")

    AntPath(locations=trail_coordinates, color='blue', weight=2.5, delay=800, dash_array=[10, 20]).add_to(flight_map)

    # Aircraft popup information
    aircraft_popup = f"""
    <b>{flight.callsign or flight.registration}</b><br>
    Altitude: {flight.altitude} ft<br>
    Speed: {flight.ground_speed} kts<br>
    Heading: {flight.heading}°
    """

    # Create a plane icon with rotation based on the flight's heading
    plane_color = flight.status_icon if flight.status_icon else 'black'
    icon_html = f"""
    <div style="transform: rotate({flight.heading}deg);">
        <i class="fa-solid fa-plane-up" style="font-size:20px; color:{plane_color}; -webkit-text-stroke: 1px black;"></i>
    </div>
    """
    plane_icon = folium.DivIcon(html=icon_html)

    folium.Marker(
        location=current_position,
        popup=folium.Popup(aircraft_popup, max_width=300),
        icon=plane_icon
    ).add_to(flight_map)

    # Add origin and destination markers
    if flight.origin_airport_iata:
        origin_popup = f"""<b>{flight.origin_airport_name} ({flight.origin_airport_iata})</b><br>
        {"Terminal " + flight.origin_airport_terminal + " " if flight.origin_airport_terminal  != "N/A" else ''}{"Gate " + flight.origin_airport_gate if flight.origin_airport_gate != "N/A" else ''}<br>
        Local Time: {get_local_time(timezone_name=flight.origin_airport_timezone_name)}<br>"""
        folium.Marker(
            location=[flight.origin_airport_latitude, flight.origin_airport_longitude],
            popup=origin_popup,
            icon=folium.Icon(color='green', icon='plane-departure')
        ).add_to(flight_map)
    
    if flight.destination_airport_iata:
        destination_popup = f"""<b>{flight.destination_airport_name} ({flight.destination_airport_iata})</b><br>
        {"Terminal " + flight.destination_airport_terminal + " " if flight.destination_airport_terminal  != "N/A" else ''}{"Gate " + flight.destination_airport_gate if flight.destination_airport_gate != "N/A" else ''}<br>
        Local Time: {get_local_time(timezone_name=flight.destination_airport_timezone_name)}<br>"""
        folium.Marker(
            location=[flight.destination_airport_latitude, flight.destination_airport_longitude + offset],
            popup=destination_popup,
            icon=folium.Icon(color='red', icon='plane-arrival')
        ).add_to(flight_map)

    return flight_map