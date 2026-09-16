import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- 1. KÖRNYEZETI VÁLTOZÓK BETÖLTÉSE ---
load_dotenv()

raw_db_url = os.getenv("SUPABASE_DB_URL")

if not raw_db_url:
    raise ValueError("Hiányzik a SUPABASE_DB_URL a .env fájlból!")

# Adatbázis motor létrehozása a connection string alapján
engine = create_engine(raw_db_url)

# --- 2. OPEN-METEO CLIENT & API KÉRÉS ---
cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 47.4231,
    "longitude": 19.1195,
    "start_date": "2026-05-01",
    "end_date": "2026-09-08",
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "surface_pressure",
        "wind_speed_10m",
        "wind_gusts_10m",
        "wind_direction_10m",
        "cloud_cover",
    ],
}

print("Múltbéli adatok lekérése az Open-Meteo Archívumból...")
responses = openmeteo.weather_api(url, params=params)
response = responses[0]

# --- 3. ADATOK FELDOLGOZÁSA (NUMPY -> PANDAS DATAFRAME) ---
hourly = response.Hourly()

hourly_data = {
    "timestamp": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    )
}

hourly_data["temperature_2m"] = hourly.Variables(0).ValuesAsNumpy()
hourly_data["relative_humidity_2m"] = hourly.Variables(1).ValuesAsNumpy()
hourly_data["apparent_temperature"] = hourly.Variables(2).ValuesAsNumpy()
hourly_data["precipitation"] = hourly.Variables(3).ValuesAsNumpy()
hourly_data["rain"] = hourly.Variables(4).ValuesAsNumpy()
hourly_data["surface_pressure"] = hourly.Variables(5).ValuesAsNumpy()
hourly_data["wind_speed_10m"] = hourly.Variables(6).ValuesAsNumpy()
hourly_data["wind_gusts_10m"] = hourly.Variables(7).ValuesAsNumpy()
hourly_data["wind_direction_10m"] = hourly.Variables(8).ValuesAsNumpy()
hourly_data["cloud_cover"] = hourly.Variables(9).ValuesAsNumpy()

df = pd.DataFrame(data=hourly_data)

print(f"Összesen {len(df)} órányi adat előkészítve a feltöltésre.")

# --- 4. BETÖLTÉS AZ ADATBÁZISBA (SQLAlchemy to_sql) ---
print("Feltöltés indítása a Supabase 'weather_logs' táblába...")

# if_exists='append': hozzáfűzi a meglévő táblához
# index=False: nem hoz létre külön index oszlopot a DataFrame-ből
df.to_sql(
    name="weather_logs",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=1000,
    method="multi"
)

print("Sikeresen feltöltve az összes múltbéli adat!")