import os
import sqlite3
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "kombi_database.db"
API_KEY = "91bc6d8c20c7cb08624f8563860e416e"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            time TEXT,
            country TEXT,
            league TEXT,
            home TEXT,
            away TEXT,
            odd_over25 REAL,
            prob_over25 INTEGER,
            prob_btts INTEGER,
            prob_ht05 INTEGER,
            prob_over35 INTEGER,
            team_target TEXT,
            odd_team_goal REAL,
            prob_team_goal INTEGER,
            fake_fav_team TEXT,
            odd_fake_fav REAL,
            fake_fav_reason TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.get("/api/kombi")
def get_kombi_data():
    headers = {
        'x-apisports-key': API_KEY
    }
    
    try:
        # Wir testen den Status-Endpunkt der API
        url = "https://v3.football.api-sports.io/status"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        print("API STATUS ANTWORT:", data)
        
        # Wenn die API aktiv ist, holen wir die heutigen Spiele mit dem Datum 2026-09-16
        fixtures_url = "https://v3.football.api-sports.io/fixtures?date=2026-09-16"
        resp_fix = requests.get(fixtures_url, headers=headers)
        fix_data = resp_fix.json()
        
        print("SPIELE ANTWORT:", fix_data)
        
        fixtures = fix_data.get("response", [])
        
        if fixtures:
            results = []
            for fix in fixtures[:15]:
                match_id = str(fix["fixture"]["id"])
                time_raw = fix["fixture"]["date"]
                time = time_raw[11:16] if len(time_raw) >= 16 else "20:30"
                country = fix["league"]["country"]
                league = fix["league"]["name"]
                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]
                
                results.append({
                    "match_id": match_id,
                    "time": time,
                    "country": country,
                    "league": league,
                    "home": home,
                    "away": away,
                    "odd_over25": 1.75,
                    "prob_over25": 78,
                    "prob_btts": 65,
                    "prob_ht05": 82,
                    "prob_over35": 45,
                    "team_target": home,
                    "odd_team_goal": 1.35,
                    "prob_team_goal": 80,
                    "fake_fav_team": home,
                    "odd_fake_fav": 2.10,
                    "fake_fav_reason": "Live-Daten aus API"
                })
            return results

    except Exception as e:
        print("Fehler:", e)
        
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
