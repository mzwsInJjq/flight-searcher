import gradio as gr
from gradio_folium import Folium

import search
from utils import render_title, select, create_airport_map
import fr24

def main():
    # Page 1: Home
    with gr.Blocks(theme=gr.themes.Ocean(), title="Flight Searcher") as demo:
        render_title("Flight Searcher")
        with gr.Column():
            origin_airport = gr.Textbox(label="Origin Airport (IATA Code)", placeholder="e.g. SEA")
            destination_airport = gr.Textbox(label="Destination Airport (IATA Code)", placeholder="e.g. JFK")
            departure_date = gr.Textbox(label="Departure Date (YYYY-MM-DD)", placeholder="e.g. 2030-01-01")
            adults = gr.Number(label="Number of Adults", value=1, precision=0, minimum=1)
            testing_checkbox = gr.Checkbox(label="Testing Mode (no API call)", value=False)
            search_button = gr.Button("Search Flights")
            output = gr.Dataframe(
                headers=["Offer #", "Flight #", "Route", "Aircraft", "DEP & ARR Terminals", "DEP Time", "ARR Time", "Duration", "Total Price"],
                label="Flight Segments",
                elem_id="output_box"
            )
            export_button_1 = gr.Button("Export to JSON")
            file_download_1 = gr.File(label="Download JSON", visible=False)
            message_1 = gr.Markdown(visible=False)

            def export_json_1():
                from search import cached_results
                import tempfile
                
                if cached_results[0] != '':
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
                    tmp.write(cached_results[0])
                    tmp.close()
                    return gr.update(value=tmp.name, visible=True), gr.update(value="", visible=False)
                else:
                    return gr.update(value=None, visible=False), gr.update(value="No results have been cached. This functionality does not support testing mode.", visible=True)

            export_button_1.click(export_json_1, inputs=None, outputs=[file_download_1, message_1])

            search_button.click(
                fn=search.search_cheapest_flights,
                inputs=[origin_airport, destination_airport, departure_date, adults, testing_checkbox],
                outputs=output,
                api_name="search_flights"
            )
        with gr.Accordion("About", open=False):
            gr.Markdown("""
                This application allows you to search for the cheapest flights between two airports using the Amadeus API and FlightRadar24 API.
                Enter the IATA codes for the origin and destination airports, and the departure date to find available flights.
                The results will display flight segments with details such as flight number, route, aircraft type, terminals, departure and arrival times, duration, and total price.
            """)

    # Page 2: Airport Routes Search
    with demo.route("Airport Routes Search"):
        with gr.Column():
            gr.Markdown("### Airport Routes Search")

            airport_search_box = gr.Textbox(label="Search for Routes from", placeholder="Enter airport name or IATA code to search", elem_id="airport_search_box")
            search_button = gr.Button("Search")
            testing_checkbox = gr.Checkbox(label="Testing Mode (no API call)", value=False)
            route_outputs = gr.Dataframe(headers=["IATA Code", "Name", "State", "Country", "Region", "Latitude", "Longitude"], label="Airport Routes")
            export_button_2 = gr.Button("Export to JSON")
            file_download_2 = gr.File(label="Download JSON", visible=False)
            message_2 = gr.Markdown(visible=False)

            def export_json_2():
                from search import cached_results
                import tempfile

                if cached_results[1] != '':
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
                    tmp.write(cached_results[1])
                    tmp.close()
                    return gr.update(value=tmp.name, visible=True), gr.update(value="", visible=False)
                else:
                    return gr.update(value=None, visible=False), gr.update(value="No results have been cached. This functionality does not support testing mode.", visible=True)

            export_button_2.click(export_json_2, inputs=None, outputs=[file_download_2, message_2])

            search_button.click(
                fn=search.search_airport_routes,
                inputs=[airport_search_box, testing_checkbox],
                outputs=route_outputs,
            )

            # Create and Update Airport Map using Gradio Folium component
            folium_map = Folium(elem_id="airport_map")

            route_outputs.select(
                fn=select,
                inputs=[route_outputs],
                outputs=[folium_map]
            )

            route_outputs.change(
                fn=create_airport_map,
                inputs=[route_outputs],
                outputs=[folium_map]
            )

            gr.Markdown("""
                This feature allows you to search for airport routes by airport name or IATA code.
                Enter the name or code to find available routes and their details.
            """)

    # Page 3: Arrival / Departure Boards
    with demo.route("Arrival / Departure Boards"):
        with gr.Column():
            gr.Markdown("### Airport Arrival / Departure Boards")
            airport_code_input = gr.Textbox(label="Airport Code (IATA/ICAO)", placeholder="e.g. SEA", elem_id="airport_code_input")
            search_button = gr.Button("Get Arrival / Departure Boards")

            with gr.Row():
                with gr.Column():
                    local_time_output = gr.Textbox(label="Local Time", interactive=False, lines=5)
                with gr.Column():
                    delay_index_output = gr.Textbox(label="Arrival/Departure Delay Index", interactive=False, lines=5)
                with gr.Column():
                    weather_output = gr.Textbox(label="Weather", interactive=False, lines=5)

            arrivals_output = gr.Dataframe(
                headers=["Origin", "Name", "Airline", "Flight", "Scheduled", "Status", "T", "Gate"],
                label="Arrivals",
                elem_id="arrivals_output"
            )

            departures_output = gr.Dataframe(
                headers=["Destination", "Name", "Airline", "Flight", "Scheduled", "Status", "T", "Gate"],
                label="Departures",
                elem_id="departures_output"
            )

            def get_airport_details(airport_code):
                airport_details = fr24.get_airport_details(airport_code)
                departures = fr24.airport_dep_board(airport_details)
                arrivals = fr24.airport_arr_board(airport_details)
                local_time = fr24.get_local_time(airport_details)
                
                # Get delay index
                arrival_delay, departure_delay = fr24.delay_index(airport_details)

                # Handle null values for delays
                if not arrival_delay:
                    arrival_delay = 0.0
                if not departure_delay:
                    departure_delay = 0.0
                
                delay_text = f"Arrivals: {arrival_delay:.2f}\nDepartures: {departure_delay:.2f}"

                # Get weather
                weather_data = fr24.weather(airport_details)
                if weather_data:
                    temp_c, temp_f, condition, humidity, wind_speed_kmh, wind_speed_mph, wind_speed_text, wind_direction_degree, wind_direction_text, visibility_km, visibility_miles = weather_data
                    weather_text = f"{temp_f} °F ({temp_c} °C) {condition}\nHumidity: {humidity}%\nWind: {wind_speed_mph} mph ({wind_speed_kmh} km/h) {wind_speed_text}\nDirection: {wind_direction_degree}° {wind_direction_text}\nVisibility: {visibility_miles} miles ({visibility_km} km)"
                else:
                    weather_text = "Not available"

                return departures, arrivals, local_time, delay_text, weather_text

            export_button_3 = gr.Button("Export to JSON")
            file_download_3 = gr.File(label="Download JSON", visible=False)
            message_3 = gr.Markdown(visible=False)
            def export_json_3():
                import tempfile

                if fr24.cached_fr24_results[0] != '':
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
                    tmp.write(fr24.cached_fr24_results[0])
                    tmp.close()
                    return gr.update(value=tmp.name, visible=True), gr.update(value="", visible=False)
                else:
                    return gr.update(value=None, visible=False), gr.update(value="No results have been cached.", visible=True)
                
            export_button_3.click(export_json_3, inputs=None, outputs=[file_download_3, message_3])

            search_button.click(
                fn=get_airport_details,
                inputs=airport_code_input,
                outputs=[departures_output, arrivals_output, local_time_output, delay_index_output, weather_output]
            )
            gr.Markdown("""
                This feature allows you to view the arrival and departure boards for a specific airport.
                Enter the IATA or ICAO code of the airport to get the latest flight information.
            """)
    
    # Page 4: Flight Status
    with demo.route("Flight Status"):
        with gr.Column():
            gr.Markdown("### Flight Status")
            flight_number_input = gr.Textbox(label="Flight / Registration (Fuzzy Matching)", placeholder="e.g. AS26 or N977AK", elem_id="flight_number_input")
            search_button = gr.Button("Get Flight Status")

            flight_status_output = gr.Textbox(label="Flight Status", interactive=False, lines=6)
            flight_map_output = Folium(label="Flight Tracker", elem_id="flight_map_output")
            export_button_4 = gr.Button("Export to JSON")
            file_download_4 = gr.File(label="Download JSON", visible=False)
            message_4 = gr.Markdown(visible=False)
            def export_json_4():
                import tempfile

                if fr24.cached_fr24_results[1] != '':
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
                    tmp.write(fr24.cached_fr24_results[1])
                    tmp.close()
                    return gr.update(value=tmp.name, visible=True), gr.update(value="", visible=False)
                else:
                    return gr.update(value=None, visible=False), gr.update(value="No results have been cached.", visible=True)
            export_button_4.click(export_json_4, inputs=None, outputs=[file_download_4, message_4])

            def get_status_and_map(flight_id):
                status = fr24.get_flight_status(flight_id)
                flight_map = fr24.get_flight_map()
                return status, flight_map

            search_button.click(
                fn=get_status_and_map,
                inputs=flight_number_input,
                outputs=[flight_status_output, flight_map_output]
            )
            gr.Markdown("""
                This feature allows you to check the status of a specific flight.
                Enter the flight number to get the latest status information and a live map.
            """)
    
    # Launch the app
    demo.launch()

if __name__ == '__main__':
    main()