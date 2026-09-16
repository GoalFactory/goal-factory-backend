import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "123"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

@app.get("/")
def home_route():
    return {"status": "GoalFactory TheSportsDB API online", "endpoint": "/api/kombi"}

@app.get("/api/kombi")
def get_kombi_data():
    try:
        all_events = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Wir fragen direkt die nächsten anstehenden Spiele der wichtigsten Fußball-Ligen ab:
        # 4328 = Premier League, 4331 = Bundesliga, 4332 = Serie A, 4335 = La Liga, 4346 = MLS
        league_ids = [4328, 4331, 4332, 4335, 4346]
        
        for lid in league_ids:
            url_next = f"{BASE_URL}/eventsnextleague.php?id={lid}"
            response_next = requests.get(url_next)
            data_next = response_next.json()
            events_next = data_next.get("events", [])
            if events_next:
                all_events.extend(events_next)

        if not all_events:
            return []

        results = []
        for i, ev in enumerate(all_events):
            # Sicherheitshalber prüfen, ob es sich um Fußball handelt
            sport_type = ev.get("strSport", "Soccer")
            if sport_type != "Soccer":
                continue

            match_id = str(ev.get("idEvent", i))
            date_event = ev.get("dateEvent", today_str)
            time_event = ev.get("strTime", "20:00")[:5]
            league = ev.get("strLeague", "Fußball Liga")
            country = ev.get("strCountry", "International")
            home = ev.get("strHomeTeam", "Heimteam")
            away = ev.get("strAwayTeam", "Gastteam")
            
            seed_val = (int(match_id) * 3) % 25 if match_id.isdigit() else 10
            prob_o25 = 65 + seed_val
            odd_o25 = round(2.00 - (prob_o25 / 100), 2)
            if odd_o25 < 1.35: 
                odd_o25 = 1.35

            results.append({
                "match_id": match_id,
                "time": f"{date_event} {time_event}",
                "country": country,
                "league": league,
                "home": home,
                "away": away,
                "odd_over25": odd_o25,
                "prob_over25": prob_o25,
                "prob_btts": 65,
                "prob_ht05": 82,
                "prob_over35": 45,
                "team_target": home,
                "odd_team_goal": 1.35,
                "prob_team_goal": 80,
                "fake_fav_team": home,
                "odd_fake_fav": 2.10,
                "fake_fav_reason": f"TheSportsDB Soccer: {home} vs {away}"
            })
            
        return results

    except Exception as e:
        print("Fehler beim Abruf:", e)
        return []

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("pregame_backend:app", host="0.0.0.0", port=port)
