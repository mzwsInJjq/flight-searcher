import os
import json
from amadeus import Client, ResponseError

def download_sea_jfk():
    """Download flight offers from SEA to JFK and save to tests/SEA-JFK.txt"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    amadeus = Client(
        client_id=config['client_id'],
        client_secret=config['client_secret']
    )
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode='SEA',
            destinationLocationCode='JFK',
            departureDate='2025-08-01',
            adults=1,
            currencyCode='USD'
        )
        os.makedirs('tests', exist_ok=True)
        with open('tests/SEA-JFK.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(response.data, indent=2))
        print('Downloaded SEA-JFK.txt')
    except ResponseError as error:
        print(f'Error downloading SEA-JFK.txt: {error}')

def download_sea():
    """Download direct destinations from SEA and save to tests/SEA.txt"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    amadeus = Client(
        client_id=config['client_id'],
        client_secret=config['client_secret']
    )
    try:
        response = amadeus.airport.direct_destinations.get(departureAirportCode='SEA')
        os.makedirs('tests', exist_ok=True)
        with open('tests/SEA.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(response.data, indent=2))
        print('Downloaded SEA.txt')
    except ResponseError as error:
        print(f'Error downloading SEA.txt: {error}')

def main():
    download_sea_jfk()
    download_sea()

if __name__ == '__main__':
    main()
