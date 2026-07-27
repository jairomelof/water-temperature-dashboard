import os
import io
import urllib.parse
import requests
import pandas as pd

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data")
os.makedirs(DATA_DIR, exist_ok=True)

STATIONS_URL = "https://raw.githubusercontent.com/jairomelo/NOAA-water-temp-CA/main/stations.csv"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/jairomelo/NOAA-water-temp-CA/main/data/"
NOAA_MDAPI_BASE = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations"

def fetch_station_metadata(station_id):
    """
    Fetch latitude and longitude for a given station ID from NOAA's Metadata API.
    """
    url = f"{NOAA_MDAPI_BASE}/{station_id}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "stations" in data and len(data["stations"]) > 0:
                station_info = data["stations"][0]
                lat = station_info.get("lat")
                lng = station_info.get("lng")
                return lat, lng
    except Exception as e:
        print(f"Error fetching metadata for station {station_id}: {e}")
    return None, None

def main():
    print("Fetching station list from NOAA-water-temp-CA repo...")
    r = requests.get(STATIONS_URL)
    if r.status_code != 200:
        print(f"Failed to fetch stations list: HTTP {r.status_code}")
        return
    
    stations_df = pd.read_csv(io.StringIO(r.text))
    print(f"Found {len(stations_df)} stations in list.")
    
    # We will collect metadata (lat, lng) and actual temperature data
    stations_metadata = []
    all_temp_dfs = []
    
    for idx, row in stations_df.iterrows():
        station_id = str(row['id']).strip()
        station_name = str(row['name']).strip()
        
        print(f"\nProcessing station {station_id} ({station_name})...")
        
        # 1. Fetch Lat/Lng metadata
        lat, lng = fetch_station_metadata(station_id)
        if lat is not None and lng is not None:
            print(f"  Coordinates: ({lat}, {lng})")
        else:
            print("  Warning: Could not fetch coordinates.")
            
        # 2. Try to fetch temperature observations CSV from GitHub
        # We need to URL-encode the station name to handle spaces properly
        encoded_name = urllib.parse.quote(station_name)
        filename = f"water_temperature-{encoded_name}-20260619-20260720.csv"
        temp_csv_url = f"{GITHUB_RAW_BASE}{filename}"
        
        has_data = False
        try:
            r_temp = requests.get(temp_csv_url, timeout=10)
            if r_temp.status_code == 200:
                df = pd.read_csv(io.StringIO(r_temp.text))
                
                # Check for columns and filter out unneeded ones
                # Required: StationID, StationName, Date_Time, Water_Temperature
                expected_cols = ['StationID', 'StationName', 'Date_Time', 'Water_Temperature']
                
                # Verify columns exist
                missing_cols = [c for col in expected_cols if (c := next((actual for actual in df.columns if actual.strip() == col), None)) is None]
                if missing_cols:
                    # Rename columns to standard ones if there are minor mismatches
                    df = df.rename(columns=lambda x: x.strip())
                    
                # Select only the required columns
                df = df[['StationID', 'StationName', 'Date_Time', 'Water_Temperature']]
                
                # Clean up Types & Formats
                df['StationID'] = df['StationID'].astype(str)
                df['StationName'] = df['StationName'].astype(str)
                df['Date_Time'] = pd.to_datetime(df['Date_Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df['Water_Temperature'] = pd.to_numeric(df['Water_Temperature'], errors='coerce')
                
                # Drop rows with null values in crucial fields
                df = df.dropna(subset=['Date_Time', 'Water_Temperature'])
                
                all_temp_dfs.append(df)
                has_data = True
                print(f"  Successfully loaded {len(df)} temperature records.")
            else:
                print(f"  No temperature data file found (HTTP {r_temp.status_code}).")
        except Exception as e:
            print(f"  Error loading temperature data: {e}")
            
        stations_metadata.append({
            'StationID': station_id,
            'StationName': station_name,
            'Latitude': lat,
            'Longitude': lng,
            'HasData': has_data
        })
        
    # Write consolidated stations metadata
    stations_metadata_df = pd.DataFrame(stations_metadata)
    stations_output_path = os.path.join(DATA_DIR, "stations.csv")
    stations_metadata_df.to_csv(stations_output_path, index=False)
    print(f"\nSaved stations metadata to {stations_output_path}")
    
    # Consolidate and write temperature data
    if all_temp_dfs:
        consolidated_temp_df = pd.concat(all_temp_dfs, ignore_index=True)
        temp_output_path = os.path.join(DATA_DIR, "water_temperatures.csv")
        consolidated_temp_df.to_csv(temp_output_path, index=False)
        print(f"Saved consolidated temperature records to {temp_output_path} ({len(consolidated_temp_df)} total rows).")
    else:
        print("\nWarning: No temperature records were successfully loaded!")

if __name__ == "__main__":
    main()
