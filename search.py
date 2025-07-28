from amadeus import Client, ResponseError
import json
from utils import convert_time_format, duration_to_string

cached_results = ['', '']

def search_cheapest_flights(origin_airport: str, destination_airport: str, departure_date: str, adults: int = 1, testing: bool = False):
    try:
        '''
        Find the cheapest flights from origin_airport to destination_airport

        origin_airport: IATA code of the origin airport
        destination_airport: IATA code of the destination airport
        departure_date: Date of departure in YYYY-MM-DD format
        adults: Number of adults traveling (default is 1)
        testing: If you want to test the function without making an API call, you can use a local file with sample data.
        '''
        # Load client_id and client_secret and authenticate
        with open('config.json', 'r') as f:
            config = json.load(f)
            client_id = config['client_id']
            client_secret = config['client_secret']

        # Initialize Amadeus client
        amadeus = Client(
            client_id=client_id,
            client_secret=client_secret
        )
        
        if not testing:
            # Make the API call to search for flight offers
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_airport,
                destinationLocationCode=destination_airport,
                departureDate=departure_date,
                adults=adults,
                currencyCode="USD"
            )
            cached_results[0] = json.dumps(response.data, indent=2)
            return print_cheapest_flights(cached_results[0])

        # For testing, read from a local file
        elif testing:
            response = open('tests/SEA-JFK.txt', 'r')
            cached_results[0] = ''
            return print_cheapest_flights(response.read())
    except ResponseError as error:
        raise error

def print_cheapest_flights(flights_data: str):
    response = json.loads(flights_data)
    # In print_cheapest_flights, build a flat list of rows with an "Offer" column
    rows = []
    for flight_idx, flight in enumerate(response):
        price_total = flight["price"]["total"]
        price_currency = flight["price"]["currency"]
        for itinerary in flight["itineraries"]:
            for seg_idx, segment in enumerate(itinerary["segments"]):
                rows.append([
                    f"{flight_idx+1}-{seg_idx+1}",
                    f"{segment['carrierCode']}{segment['number']}",
                    f"{segment['departure']['iataCode']} - {segment['arrival']['iataCode']}",
                    segment["aircraft"]["code"] if "aircraft" in segment else "",
                    f"{segment['departure'].get('terminal', '?')} - {segment['arrival'].get('terminal', '?')}",
                    convert_time_format(segment["departure"]["at"]),
                    convert_time_format(segment["arrival"]["at"]),
                    duration_to_string(segment["duration"]),
                    f"{price_total} {price_currency}"
                ])
    return rows

def search_airport_routes(airport_name: str, testing: bool = False):
    """
    Search for airport routes by airport name or IATA code
    airport_name: Name or IATA code of the airport to search for routes
    testing: If you want to test the function without making an API call, you can use a local file with sample data.
    """
    try:
        # Load client_id and client_secret and authenticate
        with open('config.json', 'r') as f:
            config = json.load(f)
            client_id = config['client_id']
            client_secret = config['client_secret']

        # Initialize Amadeus client
        amadeus = Client(
            client_id=client_id,
            client_secret=client_secret
        )
        if not testing:
            # Make the API call to search for direct destinations from the airport
            response = amadeus.airport.direct_destinations.get(departureAirportCode=airport_name)
            cached_results[1] = json.dumps(response.data, indent=2)
            return print_airport_routes(cached_results[1])

        # For testing, read from a local file
        elif testing:
            with open('tests/SEA.txt', 'r') as f:
                cached_results[1] = ''
                return print_airport_routes(f.read())
    except ResponseError as error:
        raise error

def print_airport_routes(routes_data: str):
    """
    Print the airport routes in a flat list format
    routes_data: JSON string containing the airport routes data
    """
    response = json.loads(routes_data)
    # Build a flat list of rows with airport route details
    rows = []
    for city in response:
        rows.append([
            city["iataCode"],
            city["name"].title(),
            city["address"]["stateCode"] if "stateCode" in city["address"] else "",
            city["address"]["countryCode"],
            city["address"]["regionCode"],
            city["geoCode"]["latitude"],
            city["geoCode"]["longitude"],
        ])
    return rows