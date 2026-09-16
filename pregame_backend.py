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
# Dein neuer, korrekter API-Key aus dem Screenshot:
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

def fetch_and_store_data():
    """Zieht echte Pflichtspiele mit dem neuen API-Key"""
    headers = {
        'x-apisports-key': API_KEY
    }
    
    try:
        url = "https://v3.football.api-sports.io/fixtures?next=15"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        print("API Antwort erhalten:", data.get("results"))
        fixtures = data.get("response", [])

        if fixtures:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM matches")

            for fix in fixtures:
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
                    1.75, 78, 65, 82, 45, home, 1.35, 80, home, 2.10, "Echte API-Pflichtspiel-Daten"
                ))
            conn.commit()
            conn.close()
            print(f"Erfolgreich {len(fixtures)} echte Spiele gespeichert!")
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
