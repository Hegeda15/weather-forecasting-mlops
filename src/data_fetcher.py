import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sqlalchemy import create_engine
from dotenv import load_dotenv

# .env fájl betöltése (ebben van a SUPABASE_DB_URL)
load_dotenv()
raw_db_url = os.getenv("SUPABASE_DB_URL")

if not raw_db_url:
    raise ValueError("A SUPABASE_DB_URL hiányzik a .env fájlból!")

# SQLAlchemy engine létrehozása
engine = create_engine(
    raw_db_url,
    connect_args={"prepare_threshold": None}
)

def fetch_and_push_weather():
    # Cache és retry beállítása a megbízhatóságért
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # API lekérés paraméterei (Budapest koordináták)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 47.4231,
        "longitude": 19.1195,
        "hourly": [
            "temperature_2m", 
            "relative_humidity_2m", 
            "rain", 
            "surface_pressure", 
            "precipitation", 
            "wind_speed_10m", 
            "wind_direction_10m", 
            "apparent_temperature", 
            "cloud_cover", 
            "wind_gusts_10m"
        ]
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Idősoros adatok feldolgozása
    hourly = response.Hourly()
    
    hourly_data = {
        "timestamp": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "rain": hourly.Variables(2).ValuesAsNumpy(),
        "surface_pressure": hourly.Variables(3).ValuesAsNumpy(),
        "precipitation": hourly.Variables(4).ValuesAsNumpy(),
        "wind_speed_10m": hourly.Variables(5).ValuesAsNumpy(),
        "wind_direction_10m": hourly.Variables(6).ValuesAsNumpy(),
        "apparent_temperature": hourly.Variables(7).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(8).ValuesAsNumpy(),
        "wind_gusts_10m": hourly.Variables(9).ValuesAsNumpy(),
    }

    df = pd.DataFrame(data=hourly_data)

    # Adatbázisba küldés (Supabase)
    if raw_db_url:
        # Az if_exists="append" biztosítja, hogy az új adatok hozzáíródjanak a meglévőkhöz
        df.to_sql("weather_logs", engine, if_exists="append", index=False, method="multi")
        print(f"Sikeresen elmentve {len(df)} sor a Supabase adatbázisba!")
    else:
        print("Hiba: SUPABASE_DB_URL nem található a környezeti változók között!")

if __name__ == "__main__":
    fetch_and_push_weather()