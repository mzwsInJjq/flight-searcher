# Flight Searcher

Flight Searcher is a Python application for searching, visualizing, and exporting flight data. It combines the Amadeus API for flight offers and the FlightRadar24 API for live flight tracking, all wrapped in an interactive Gradio web interface with Folium maps.

## Features

- **Search Cheapest Flights:**
  - Find the cheapest flights between two airports using the Amadeus API.
  - View detailed flight segments, aircraft, terminals, times, and prices.
  - Export search results to JSON.

- **Live Flight Tracking:**
  - Track live flights by registration using FlightRadar24.
  - Visualize real-time aircraft position and trail on an interactive map.
  - View origin/destination airport details and local times.

- **Airport Routes Search:**
  - Search for all direct routes from a given airport.
  - Visualize airport locations on a map.
  - Export route data to JSON.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/mzwsInJjq/flight-searcher.git
   cd flight-searcher
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `config.json` file in the project root with your Amadeus API credentials:
   ```json
   {
     "client_id": "YOUR_AMADEUS_CLIENT_ID",
     "client_secret": "YOUR_AMADEUS_CLIENT_SECRET"
   }
   ```
   **Note:** Do not share or commit your `config.json`.

## Usage

Run the Gradio app:
```bash
python app.py
```

Open the provided local URL in your browser to use the interface.

## Project Structure

- `app.py` — Main Gradio app and UI logic
- `fr24.py` — FlightRadar24 API integration and live map generation
- `search.py` — Amadeus API integration and flight search logic
- `utils.py` — Helper functions for formatting and map rendering
- `requirements.txt` — Python dependencies
- `tests/` — Test data and files

## Dependencies
- gradio
- gradio-folium
- folium
- amadeus
- FlightRadarAPI
- pandas

Install all dependencies with `pip install -r requirements.txt`.

## License
MIT License

## Disclaimer
This project is for educational and personal use. API usage may be subject to rate limits and terms of service. Always keep your API credentials secure.
