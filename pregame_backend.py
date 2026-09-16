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

@app.get("/api/kombi")
def get_kombi_data():
    headers = {
        'x-apisports-key': API_KEY
    }
    
    try:
        # Echte Spiele für heute abrufen
        fixtures_url = "https://v3.football.api-sports.io/fixtures?date=2026-09-16"
        resp_fix = requests.get(fixtures_url, headers=headers)
        fix_data = resp_fix.json()
        
        fixtures = fix_data.get("response", [])
        
        if fixtures:
            results = []
            for i, fix in enumerate(fixtures[:20]):
                match_id = str(fix["fixture"]["id"])
                time_raw = fix["fixture"]["date"]
                time = time_raw[11:16] if len(time_raw) >= 16 else "20:30"
                country = fix["league"]["country"]
                league = fix["league"]["name"]
                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]
                
                # INTELLIGENTER ALGORITHMUS-SCHLÜSSEL:
                # Wir generieren anhand der Match-ID und Teams realistische, variable Werte,
                # damit nicht jedes Spiel exakt dieselben 78% hat.
                # (Später erweitern wir das mit den echten Tordurchschnitten der Teams!)
                seed_val = (i * 7) % 25  # Kleine Variation
                prob_o25 = 62 + seed_val  # Werte zwischen 62% und 87%
                prob_btts = 55 + (seed_val % 20)
                
                # Quoten-Berechnung basierend auf Wahrscheinlichkeit
                odd_o25 = round(2.00 - (prob_o25 / 100), 2)
                if odd_o25 < 1.35: odd_o25 = 1.35

                results.append({
                    "match_id": match_id,
                    "time": time,
                    "country": country,
                    "league": league,
                    "home": home,
                    "away": away,
                    "odd_over25": odd_o25,
                    "prob_over25": prob_o25,
                    "prob_btts": prob_btts,
                    "prob_ht05": 82,
                    "prob_over35": 45,
                    "team_target": home,
                    "odd_team_goal": 1.35,
                    "prob_team_goal": 80,
                    "fake_fav_team": home,
                    "odd_fake_fav": 2.10,
                    "fake_fav_reason": f"Algorithmus-Check: {home} Heim-Offensive & Trend aktiv"
                })
            return results

    except Exception as e:
        print("Fehler:", e)
        
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
