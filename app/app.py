import os
import pandas as pd
from pathlib import Path
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from ipyleaflet import Map, Marker, AwesomeIcon, basemaps

# Load the data statically from the data directory relative to app.py
DATA_DIR = Path(__file__).parent / "data"
STATIONS_FILE = DATA_DIR / "stations.csv"
TEMPS_FILE = DATA_DIR / "water_temperatures.csv"

# Load the tables
stations_df = pd.read_csv(STATIONS_FILE)
temps_df = pd.read_csv(TEMPS_FILE)

# Ensure correct data types
stations_df["StationID"] = stations_df["StationID"].astype(str)
temps_df["StationID"] = temps_df["StationID"].astype(str)
temps_df["Date_Time"] = pd.to_datetime(temps_df["Date_Time"])

# Get stations that actually have temperature records
active_stations = stations_df[stations_df["HasData"] == True]
station_choices = {row["StationID"]: f"{row['StationName']} ({row['StationID']})" for _, row in active_stations.iterrows()}

# Define custom CSS styling for dashboard beauty
app_css = """
.card {
    border-radius: 12px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 15px;
    border: 1px solid #e9ecef !important;
    padding: 15px;
    background-color: #ffffff;
}
.card-avg {
    border-left: 5px solid #0d6efd !important;
}
.card-hot {
    border-left: 5px solid #dc3545 !important;
}
.card-cool {
    border-left: 5px solid #0dcaf0 !important;
}
.card-title {
    font-size: 0.9rem;
    color: #6c757d;
    text-transform: uppercase;
    font-weight: 600;
}
.card-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #212529;
    margin-top: 5px;
}
.card-subtitle {
    font-size: 0.8rem;
    color: #8c959d;
    margin-top: 2px;
}
"""

# App UI layout
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Dashboard Controls", style="font-weight: 700; margin-bottom: 20px;"),
        ui.input_select(
            id="station_select",
            label="Select Station:",
            choices=station_choices,
            selected=active_stations["StationID"].iloc[0]
        ),
        ui.hr(),
        ui.input_switch(
            id="temp_unit_switch",
            label="Show in Fahrenheit (°F)",
            value=False
        ),
        ui.p(
            "Toggle this switch to instantly convert all statistics, summary cards, and the chart to Celsius or Fahrenheit.",
            style="font-size: 0.85rem; color: #6c757d; margin-top: 10px;"
        ),
        ui.hr(),
        ui.h5("About the Data", style="font-weight: 600; font-size: 0.95rem;"),
        ui.p(
            "This app visualizes coastal California water temperatures between June 19, 2026 and July 20, 2026. "
            "Data is retrieved from NOAA Tide & Currents stations.",
            style="font-size: 0.8rem; color: #6c757d;"
        ),
        width=320,
    ),
    # Header area
    ui.h2("California Coastal Water Temperature Dashboard", style="font-weight: 800; margin-bottom: 25px; color: #1e293b;"),
    
    # Top Row: Summary Cards (Avg, Hottest, Coolest)
    ui.layout_column_wrap(
        ui.div(
            ui.div("Average Temperature", class_="card-title"),
            ui.div(ui.output_text("avg_temp_val"), class_="card-value"),
            ui.div("Average over 1 month", class_="card-subtitle"),
            class_="card card-avg"
        ),
        ui.div(
            ui.div("Hottest Recorded Temp", class_="card-title"),
            ui.div(ui.output_text("hot_temp_val"), class_="card-value"),
            ui.div(ui.output_text("hot_temp_date"), class_="card-subtitle"),
            class_="card card-hot"
        ),
        ui.div(
            ui.div("Coolest Recorded Temp", class_="card-title"),
            ui.div(ui.output_text("cool_temp_val"), class_="card-value"),
            ui.div(ui.output_text("cool_temp_date"), class_="card-subtitle"),
            class_="card card-cool"
        ),
        width=1/3
    ),
    
    # Bottom Row: Map and Chart
    ui.layout_column_wrap(
        ui.div(
            ui.h4("Station Locator Map", style="font-weight: 700; margin-bottom: 10px; font-size: 1.1rem;"),
            ui.p("Click on any blue marker to inspect that station's temperatures.", style="font-size: 0.85rem; color: #6c757d; margin-bottom: 15px;"),
            output_widget("station_map"),
            style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; height: 500px;"
        ),
        ui.div(
            ui.h4("Water Temperature Trend Line", style="font-weight: 700; margin-bottom: 10px; font-size: 1.1rem;"),
            ui.p("Hourly raw observation points and overall trend.", style="font-size: 0.85rem; color: #6c757d; margin-bottom: 15px;"),
            ui.output_plot("temp_chart"),
            style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; height: 500px;"
        ),
        width=1/2
    ),
    
    # Custom CSS style block
    ui.tags.style(app_css),
    
    title="California Coastal Water Temp Dashboard"
)

def server(input, output, session):
    # Reactive value to coordinate bidirectionally between map marker clicks and select dropdown changes
    reactive_station = reactive.Value(active_stations["StationID"].iloc[0])
    
    # 1. Sync dropdown selection -> reactive_station
    @reactive.Effect
    @reactive.event(input.station_select)
    def _sync_select_to_val():
        reactive_station.set(input.station_select())
        
    # 2. Sync reactive_station -> dropdown selection
    @reactive.Effect
    def _sync_val_to_select():
        ui.update_select("station_select", selected=reactive_station())
        
    # Reactive calculation to get temperature data for the selected station
    @reactive.Calc
    def selected_data():
        sid = reactive_station()
        df = temps_df[temps_df["StationID"] == sid].copy()
        return df.sort_values("Date_Time")
        
    # Unit converter helper function
    def format_temp(celsius_val):
        if pd.isna(celsius_val):
            return "N/A"
        if input.temp_unit_switch():
            f_val = (celsius_val * 9 / 5) + 32
            return f"{f_val:.1f}°F"
        return f"{celsius_val:.1f}°C"

    # OUTPUTS: Summary Cards
    @output
    @render.text
    def avg_temp_val():
        df = selected_data()
        if df.empty:
            return "N/A"
        return format_temp(df["Water_Temperature"].mean())
        
    @output
    @render.text
    def hot_temp_val():
        df = selected_data()
        if df.empty:
            return "N/A"
        return format_temp(df["Water_Temperature"].max())

    @output
    @render.text
    def hot_temp_date():
        df = selected_data()
        if df.empty:
            return ""
        idx = df["Water_Temperature"].idxmax()
        hottest_time = df.loc[idx, "Date_Time"]
        return f"Observed on: {hottest_time.strftime('%b %d, %H:%M')}"

    @output
    @render.text
    def cool_temp_val():
        df = selected_data()
        if df.empty:
            return "N/A"
        return format_temp(df["Water_Temperature"].min())

    @output
    @render.text
    def cool_temp_date():
        df = selected_data()
        if df.empty:
            return ""
        idx = df["Water_Temperature"].idxmin()
        coolest_time = df.loc[idx, "Date_Time"]
        return f"Observed on: {coolest_time.strftime('%b %d, %H:%M')}"

    # OUTPUT: Interactive Station Map
    @render_widget
    def station_map():
        # Initialize Leaflet Map centered on California Coast
        m = Map(
            center=(37.2, -119.5),
            zoom=5.5,
            basemap=basemaps.CartoDB.Positron,
            scroll_wheel_zoom=True
        )
        
        # We add markers for all stations. Blue for active, gray for inactive.
        for _, row in stations_df.iterrows():
            sid = str(row["StationID"])
            sname = str(row["StationName"])
            lat = row["Latitude"]
            lng = row["Longitude"]
            has_data = bool(row["HasData"])
            
            if pd.isna(lat) or pd.isna(lng):
                continue
                
            # Style markers differently based on if data exists
            if has_data:
                # Active stations
                icon = AwesomeIcon(
                    name="tint",
                    marker_color="blue",
                    icon_color="white"
                )
                opacity = 1.0
            else:
                # Inactive stations
                icon = AwesomeIcon(
                    name="times",
                    marker_color="gray",
                    icon_color="white"
                )
                opacity = 0.5
                
            marker = Marker(
                location=(lat, lng),
                title=f"{sname} (ID: {sid})" + ("" if has_data else " [No Data]"),
                icon=icon,
                opacity=opacity,
                draggable=False
            )
            
            # Clicking an active marker updates our reactive value
            if has_data:
                def make_click_handler(station_id):
                    def handler(**kwargs):
                        reactive_station.set(station_id)
                    return handler
                marker.on_click(make_click_handler(sid))
                
            m.add_layer(marker)
            
        return m

    # OUTPUT: Time-series Line Chart
    @output
    @render.plot
    def temp_chart():
        df = selected_data()
        if df.empty:
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.text(0.5, 0.5, "No observations available for this station", ha="center", va="center")
            return fig
            
        # Determine values to plot
        is_fahrenheit = input.temp_unit_switch()
        temps = df["Water_Temperature"]
        unit_str = "°C"
        
        if is_fahrenheit:
            temps = (temps * 9 / 5) + 32
            unit_str = "°F"
            
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)
        
        # Plot data
        ax.plot(df["Date_Time"], temps, color="#0d6efd", linewidth=1.5, alpha=0.85, label="Observation")
        
        # Add rolling average/smooth curve
        rolling_avg = temps.rolling(window=120, min_periods=1, center=True).mean()
        ax.plot(df["Date_Time"], rolling_avg, color="#dc3545", linewidth=2.0, label="12-Hour Trend")
        
        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=4))
        fig.autofmt_xdate()
        
        # Set titles and labels
        station_name = active_stations[active_stations["StationID"] == reactive_station()]["StationName"].iloc[0]
        ax.set_title(f"{station_name} Water Temperatures (June 19 - July 20, 2026)", fontsize=11, fontweight="bold", pad=15)
        ax.set_ylabel(f"Water Temperature ({unit_str})", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        
        # Style legend and remove top/right spines
        ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
            
        plt.tight_layout()
        return fig

app = App(app_ui, server)
