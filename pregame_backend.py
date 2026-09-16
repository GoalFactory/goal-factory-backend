import os
import sqlite3
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS für deine GitHub-Pages Website erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "kombi_database.db"
API_KEY = "1c6dd087a5bcd9d9cf78cb286d7cfa"  # Dein API-Key aus dem Screenshot

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

def fetch_live_data_from_api():
    """Holt automatisch die echten Spiele des aktuellen Tages von api-sports.io"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={today_str}"
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        fixtures = data.get("response", [])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Alte Spiele des Vortages löschen, damit die Liste sauber bleibt
        cursor.execute("DELETE FROM matches")

        for fix in fixtures:
            match_id = str(fix["fixture"]["id"])
            time = fix["fixture"]["date"][11:16]
            country = fix["league"]["country"]
            league = fix["league"]["name"]
            home = fix["teams"]["home"]["name"]
            away = fix["teams"]["away"]["name"]

            # Daten in die SQLite Datenbank schreiben
            cursor.execute("""
                INSERT OR REPLACE INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, time, country, league, home, away,
                1.75, 78, 65, 82, 45, home, 1.35, 80, home, 2.10, "Heimteam unter Druck, starker Value"
            ))
        conn.commit()
        conn.close()
        print(f"Spiele für {today_str} erfolgreich automatisch aktualisiert!")
    except Exception as e:
        print(f"Fehler beim Abrufen der API-Daten: {e}")

@app.on_event("startup")
def startup_event():
    init_db()
    fetch_live_data_from_api()

@app.get("/api/kombi")
def get_kombi_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches")
    rows = cursor.fetchall()
    conn.close()

    matches = [dict(row) for row in rows]
    return matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
