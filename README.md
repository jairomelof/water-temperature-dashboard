# California Coastal Water Temperature Dashboard

A highly interactive, zero-server **Shiny for Python + WebAssembly (Shinylive)** data dashboard built to visualize coastal water temperatures in California. 

The dashboard runs entirely in the user's browser via WebAssembly (Pyodide), meaning it requires no backend Python server and can be hosted 100% statically on platforms like GitHub Pages.

---

## 🌊 Key Features
- **Interactive Leaflet Map (`ipyleaflet`):** Highlighting 16 major coastal California stations. Active stations (with data) are marked in blue, and clicking them updates the dashboard instantly. Inactive stations (no current NOAA data) are marked in gray.
- **Dynamic Stats Cards:** Displays real-time summary statistics for the selected station—**Average Temperature**, **Hottest Record**, and **Coolest Record** (with precise date and observation time).
- **Celsius/Fahrenheit Toggle:** Converts all summary statistics and chart axes instantly between metric (°C) and imperial (°F).
- **Water Temperature Trend Line:** Employs `matplotlib` to render raw observation data points alongside a smoothed **12-Hour Trend line** showing overall movement.

---

## 📂 Project Structure
```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment workflow
├── app/
│   ├── app.py                  # Main Shiny Dashboard application code
│   └── data/
│       ├── stations.csv        # Pre-processed station list with coordinates
│       └── water_temperatures.csv # Consolidated water temperature recordings
├── fetch_data.py               # Raw NOAA API data fetch & ingestion script
├── requirements.txt            # Python application dependencies
└── README.md                   # This instruction file
```

---

## 🛠️ Local Development & Testing

### 1. Set Up Environment
Create and activate a virtual environment, and install dependencies:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Ingest Latest Data (Optional)
The ingestion script reads the station names, queries the NOAA Metadata API for geographic coordinates, downloads individual CSVs from the NOAA-water-temp-CA cache, cleanses columns, and outputs consolidated files under `app/data/`:
```bash
python fetch_data.py
```

### 3. Run the Dashboard Locally
Start the local development server with the `--reload` flag to preview code changes instantly:
```bash
shiny run app/app.py --reload
```
Open your browser and navigate to **`http://127.0.0.1:8000`**.

---

## 🚀 GitHub Pages Deployment via GitHub Actions

This project contains a GitHub Actions workflow `.github/workflows/deploy.yml` that automates deploying your dashboard to GitHub Pages. It runs the data ingestion script to ensure fresh data, compiles the application to static WebAssembly using `shinylive`, and deploys the bundle directly.

### Step-by-Step GitHub Configuration Instructions

To enable and configure deployment on your repository:

1. **Push the Code to GitHub:**
   In your local repository directory, initialize git, commit all files, and push to your public GitHub repository (`main` branch):
   ```bash
   git init
   git add .
   git commit -m "Initialize dashboard, data ingestion pipeline, and deploy workflow"
   git branch -M main
   git remote add origin https://github.com/jairomelof/water-temperature-dashboard.git
   git push -u origin main
   ```

2. **Configure GitHub Pages Permissions:**
   - Go to your repository on GitHub: `https://github.com/jairomelof/water-temperature-dashboard`
   - Click on the **Settings** tab.
   - On the left sidebar, click on **Pages**.
   - Under the **Build and deployment** section, look for **Source**.
   - Change the **Source** dropdown selection from **Deploy from a branch** to **GitHub Actions**.

3. **Verify the Deployment:**
   - Once pushed and with pages source set to **GitHub Actions**, go to the **Actions** tab on your repository.
   - You will see the **Deploy Dashboard to GitHub Pages** workflow running.
   - When the workflow completes successfully, it will output a deployment link in the log.
   - Your dashboard will be live at: `https://jairomelof.github.io/water-temperature-dashboard/`

---

## 📊 Data Details
- **Date Range:** June 19, 2026 to July 20, 2026.
- **Source Data Repository:** [jairomelo/NOAA-water-temp-CA](https://github.com/jairomelo/NOAA-water-temp-CA)
- **Columns used:** `StationID`, `StationName`, `Date_Time`, `Water_Temperature`
