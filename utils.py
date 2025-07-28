import gradio as gr
from folium import Map, Marker
from datetime import datetime
from pandas import Timedelta

def render_title(title: str = "Flight Searcher"):
        return gr.HTML(f"""
        <link href="https://fonts.googleapis.com/css2?family=Ubuntu&display=swap" rel="stylesheet">
        <h1 style = "text-align:center;
            font-family: 'Ubuntu',
            sans-serif;
            font-weight: 500;
            font-style: italic;
            font-size: 3em;">
            {title}
        </h1>
        """)

def select(df, data: gr.SelectData):
    row = df.iloc[data.index[0], :]
    m = Map(location=[float(row['Latitude']), float(row['Longitude'])], zoom_start=6, tiles="CartoDB positron")
    Marker([float(row['Latitude']), float(row['Longitude'])], popup=row.get('Name', str(row['Latitude']) + ',' + str(row['Longitude']))).add_to(m)
    return m

def create_airport_map(rows):
    m = Map(location=[0, 0], zoom_start=1, tiles="CartoDB positron")
    for _, row in rows.iterrows():
        try:
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            name = row['Name'] + ' ' + row['IATA Code']
            Marker([lat, lon], popup=name).add_to(m)
        except (ValueError, TypeError, KeyError):
            continue
    return m

def save_to_csv(df, filename: str):
    """
    Save DataFrame to CSV file.
    df: DataFrame to save
    filename: Name of the file to save as
    """

    df.to_csv(filename, index=False)
    return f"Data saved to {filename}"

def save_to_json(data, filename: str):
    """
    Save a Python object (list, dict, etc.) to a JSON file.
    data: The object to save (list, dict, etc.)
    filename: Name of the file to save as
    """
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"Data saved to {filename}"

def convert_time_format(time_str: str, from_format: str = "%Y-%m-%dT%H:%M:%S", to_format: str = "%m-%d-%Y %I:%M%p"):
    """
    Convert time string from one format to another.
    time_str: Time string to convert
    from_format: Current format of the time string
    to_format: Desired format of the time string
    """
    try:
        dt = datetime.strptime(time_str, from_format)
        return dt.strftime(to_format)
    except ValueError as e:
        return f"Error converting time: {e}"
    
def duration_to_string(duration: str) -> str:
    dt = Timedelta(duration)
    return str(dt).replace("0 days ", "")