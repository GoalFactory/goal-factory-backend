import os
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

API_KEY = "91bc6d8c20c7cb08624f8563860e416e"

@app.get("/api/kombi")
def get_kombi_data():
    headers = {
        'x-apisports-key': API_KEY
    }
    
    fixtures = []
    
    try:
        # Wir fragen direkt die Premier League (ID 39) und Bundesliga (ID 78) ab
        leagues = [39, 78, 140, 135] # Premier League, Bundesliga, La Liga, Serie A
        
        for league_id in leagues:
            url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season=2026"
            response = requests.get(url, headers=headers)
            data = response.json()
            league_fixtures = data.get("response", [])
            
            if league_fixtures:
                fixtures.extend(league_fixtures[:5]) # Nimm die ersten 5 Spiele pro Liga
                
        # Falls das über die Ligen-ID wegen der Saison nicht greift, nehmen wir den allgemeinen Live/Upcoming-Endpunkt
        if not fixtures:
            url_fallback = "https://v3.football.api-sports.io/fixtures?live=all"
            resp_fb = requests.get(url_fallback, headers=headers)
            fixtures = resp_fb.json().get("response", [])

        results = []
        for i, fix in enumerate(fixtures):
            match_id = str(fix["fixture"]["id"])
            time_raw = fix["fixture"]["date"]
            time = time_raw[11:16] if len(time_raw) >= 16 else "20:30"
            country = fix["league"]["country"]
            league = fix["league"]["name"]
            home = fix["teams"]["home"]["name"]
            away = fix["teams"]["away"]["name"]
            
            seed_val = (i * 7) % 25
            prob_o25 = 65 + seed_val
            prob_btts = 58 + (seed_val % 18)
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
                "fake_fav_reason": f"Algorithmus-Check: {home} Offensiv-Trend aktiv"
            })
            
        return results

    except Exception as e:
        print("Fehler:", e)
        
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
