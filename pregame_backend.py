import os
import random
import sqlite3
from datetime import datetime
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "kombi_maker.db"
API_KEY = "1c468d087a5bc9d69cf718cb286d7d5a"
API_HOST = "v3.football.api-sports.io"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kombi_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            country TEXT,
            league TEXT,
            home TEXT,
            away TEXT,
            time TEXT,
            odd_over25 REAL,
            prob_over25 REAL,
            prob_btts REAL,
            prob_ht05 REAL,
            prob_over35 REAL,
            team_target TEXT,
            odd_team_goal REAL,
            prob_team_goal REAL,
            fake_fav_team TEXT,
            fake_fav_odd REAL,
            fake_fav_reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def fetch_live_api_matches():
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://{API_HOST}/fixtures?date={today_str}"
    
    headers = {
        'x-apisports-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if "response" in data and len(data["response"]) > 0:
            matches_to_save = []
            for item in data["response"][:50]:
                fixture = item.get("fixture", {})
                league = item.get("league", {})
                teams = item.get("teams", {})
                
                match_id = str(fixture.get("id"))
                country = league.get("country", "International")
                league_name = league.get("name", "League")
                home = teams.get("home", {}).get("name", "Home Team")
                away = teams.get("away", {}).get("name", "Away Team")
                
                date_str = fixture.get("date")
                match_time = "18:00"
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        match_time = dt.strftime("%H:%M")
                    except:
                        pass
                
                odd_over25 = round(random.uniform(1.50, 2.30), 2)
                prob_over25 = random.randint(55, 92)
                prob_btts = random.randint(50, 88)
                prob_ht05 = random.randint(70, 95)
                prob_over35 = random.randint(30, 75)
                
                is_home_underdog = random.choice([True, False])
                target_team = away if is_home_underdog else home
                odd_team_goal = round(random.uniform(1.45, 2.10), 2)
                prob_team_goal = random.randint(60, 88)
                
                fake_fav_team = home if random.choice([True, False]) else away
                fake_fav_odd = round(random.uniform(2.10, 3.40), 2)
                reasons = [
                    "Buchmacher unterschätzt aktuelle Form des Gegners",
                    "Schlechtere H2H-Bilanz in den letzten 3 direkten Duellen",
                    "Tabellennachbarn – Quote für Favorit viel zu niedrig angesetzt",
                    "Wichtige Ausfälle beim vermeintlichen Favoriten"
                ]
                fake_fav_reason = random.choice(reasons)
                
                matches_to_save.append((
                    match_id, country, league_name, home, away, match_time,
                    odd_over25, prob_over25, prob_btts, prob_ht05, prob_over35,
                    target_team, odd_team_goal, prob_team_goal,
                    fake_fav_team, fake_fav_odd, fake_fav_reason
                ))
            return matches_to_save
    except Exception as e:
        print(f"⚠️ API Fehler: {e}")
    
    return []

@app.on_event("startup")
def startup_event():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM kombi_matches')
    conn.commit()
    
    print("🔄 Lade Spiele von API-Football...")
    api_matches = fetch_live_api_matches()
    
    if len(api_matches) > 0:
        cursor.executemany('''
            INSERT INTO kombi_matches (match_id, country, league, home, away, time, odd_over25, prob_over25, prob_btts, prob_ht05, prob_over35, team_target, odd_team_goal, prob_team_goal, fake_fav_team, fake_fav_odd, fake_fav_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', api_matches)
        conn.commit()
        print(f"✅ {len(api_matches)} Spiele geladen!")
    else:
        print("⚠️ Lade Fallback-Spiele...")
        for i in range(1, 31):
            cursor.execute('''
                INSERT INTO kombi_matches (match_id, country, league, home, away, time, odd_over25, prob_over25, prob_btts, prob_ht05, prob_over35, team_target, odd_team_goal, prob_team_goal, fake_fav_team, fake_fav_odd, fake_fav_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (f"fb_{i}", "Germany", "Bundesliga", f"Team A{i}", f"Team B{i}", "20:30", 1.85, 75, 70, 85, 45, f"Team B{i}", 1.75, 72, f"Team A{i}", 2.45, "Schlechtere H2H-Bilanz"))
        conn.commit()
        
    conn.close()

@app.get("/api/kombi")
def get_kombi_matches():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT match_id, country, league, home, away, time, odd_over25, prob_over25, prob_btts, prob_ht05, prob_over35, team_target, odd_team_goal, prob_team_goal, fake_fav_team, fake_fav_odd, fake_fav_reason FROM kombi_matches')
    rows = cursor.fetchall()
    conn.close()

    matches = []
    for r in rows:
        matches.append({
            "match_id": r[0], "country": r[1], "league": r[2], "home": r[3], "away": r[4], "time": r[5],
            "odd_over25": r[6], "prob_over25": r[7], "prob_btts": r[8], "prob_ht05": r[9], "prob_over35": r[10],
            "team_target": r[11], "odd_team_goal": r[12], "prob_team_goal": r[13],
            "fake_fav_team": r[14], "fake_fav_odd": r[15], "fake_fav_reason": r[16]
        })
    return matches

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
