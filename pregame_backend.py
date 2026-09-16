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
API_KEY = "1c6dd087a5bcd9d9cf78cb286d7cfa"

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

def fetch_and_store_data():
    """Holt echte Pflichtspiele von api-sports.io"""
    headers = {
        'x-apisports-key': API_KEY
    }
    
    try:
        # Wir fragen die Premier League (ID 39) für die aktuelle Saison ab
        url = "https://v3.football.api-sports.io/fixtures?league=39&season=2026"
        response = requests.get(url, headers=headers)
        data = response.json()
        fixtures = data.get("response", [])

        if fixtures:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM matches")

            for fix in fixtures[:15]:
                match_id = str(fix["fixture"]["id"])
                time_raw = fix["fixture"]["date"]
                time = time_raw[11:16] if len(time_raw) >= 16 else "20:30"
                country = fix["league"]["country"]
                league = fix["league"]["name"]
                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]

                cursor.execute("""
                    INSERT OR REPLACE INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match_id, time, country, league, home, away,
                    1.75, 78, 65, 82, 45, home, 1.35, 80, home, 2.10, "Starke Form & Value Quote"
                ))
            conn.commit()
            conn.close()
            print(f"Erfolgreich {len(fixtures)} Spiele gespeichert!")
    except Exception as e:
        print(f"Fehler: {e}")

@app.on_event("startup")
def startup_event():
    init_db()
    fetch_and_store_data()

@app.get("/api/kombi")
def get_kombi_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches")
    rows = cursor.fetchall()
    
    # Falls die Datenbank leer ist, versuche sofort Daten nachzuladen!
    if not rows:
        conn.close()
        fetch_and_store_data()
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM matches")
        rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
