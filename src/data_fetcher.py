import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sqlalchemy import create_engine
from dotenv import load_dotenv

def fetch_and_push_weather():
    # 1. Környezeti változó beolvasása (.env-ből vagy GitHub Secrets-ből)
    load_dotenv()
    raw_db_url = os.getenv("SUPABASE_DB_URL")

    if not raw_db_url:
        raise ValueError("A SUPABASE_DB_URL hiányzik a környezeti változók közül!")

    # 2. Database Engine létrehozása
    engine = create_engine(
        raw_db_url,
        connect_args={"prepare_threshold": None}
    )

    # 3. API lekérés beállítása
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

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

    # 4. Adatok átalakítása DataFrame-mé
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
        "wind_direction_10m": hourly.Variables(6).Variables if hasattr(hourly.Variables(6), 'Variables') else hourly.Variables(6).ValuesAsNumpy(),
        "apparent_temperature": hourly.Variables(7).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(8).ValuesAsNumpy(),
        "wind_gusts_10m": hourly.Variables(9).ValuesAsNumpy(),
    }

    df = pd.DataFrame(data=hourly_data)
    now_utc = pd.Timestamp.now(tz="UTC")
    df = df[df["timestamp"] <= now_utc]

    # 5. Duplikációk kiszűrése (a legfrissebb meglévő timestamp lekérdezése)
    try:
        max_time_query = "SELECT MAX(timestamp) FROM weather_logs;"
        max_time = pd.read_sql(max_time_query, con=engine).iloc[0, 0]

        if max_time is not None:
            max_time = pd.to_datetime(max_time, utc=True)
            df = df[df["timestamp"] > max_time]
    except Exception as e:
        print(f"⚠️ Nem sikerült a lekérdezés az adatbázisból (pl. ha üres még a tábla): {e}")

    # 6. Adatbázisba írás (csak ha maradt új sor)
    if not df.empty:
        df.to_sql("weather_logs", engine, if_exists="append", index=False, method="multi")
        print(f"✅ Sikeresen elmentve {len(df)} új sor a Supabase adatbázisba!")
    else:
        print("ℹ️ Nincsenek új mentendő adatok (minden rekord szerepel már az adatbázisban).")

if __name__ == "__main__":
    fetch_and_push_weather()