import sqlite3
import pandas as pd
from datetime import date
import json

def create_database():
    """Create and populate the crime investigation database"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        case_id INTEGER PRIMARY KEY,
        case_name TEXT NOT NULL,
        crime_type TEXT NOT NULL,
        date_opened DATE,
        priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
        solved BOOLEAN DEFAULT 0,
        location TEXT,
        description TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suspects (
        suspect_id INTEGER PRIMARY KEY,
        case_id INTEGER,
        name TEXT NOT NULL,
        age INTEGER,
        occupation TEXT,
        last_seen TEXT,
        motive TEXT,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id INTEGER PRIMARY KEY,
        case_id INTEGER,
        description TEXT,
        evidence_type TEXT,
        collected_date DATE,
        forensic_value INTEGER CHECK(forensic_value BETWEEN 1 AND 10),
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detectives (
        detective_id INTEGER PRIMARY KEY,
        name TEXT,
        rank TEXT,
        active_cases INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interrogations (
        interrogation_id INTEGER PRIMARY KEY,
        suspect_id INTEGER,
        detective_id INTEGER,
        interrogation_date DATE,
        key_info TEXT,
        FOREIGN KEY (suspect_id) REFERENCES suspects(suspect_id),
        FOREIGN KEY (detective_id) REFERENCES detectives(detective_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT NOT NULL,
        total_score INTEGER DEFAULT 0,
        completed_levels INTEGER DEFAULT 0,
        fastest_completion_time REAL,
        total_attempts INTEGER DEFAULT 0,
        streak_count INTEGER DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player_name)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS challenge_times (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        level_num INTEGER,
        completion_time REAL,
        attempts_before_success INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES leaderboard(player_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS multiplayer_sessions (
        session_id TEXT PRIMARY KEY,
        host_name TEXT,
        session_code TEXT,
        current_level INTEGER DEFAULT 1,
        players TEXT,
        started BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
# Add these tables to your create_database() function

    # Multiplayer race sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_sessions (
        session_id TEXT PRIMARY KEY,
        host_name TEXT NOT NULL,
        session_code TEXT NOT NULL,
        players TEXT,  -- JSON array of player names
        player_progress TEXT,  -- JSON object of player progress
        status TEXT DEFAULT 'waiting',
        start_time TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Query guessing game sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guessing_sessions (
        session_id TEXT PRIMARY KEY,
        writer_name TEXT NOT NULL,
        session_code TEXT NOT NULL,
        secret_query TEXT,
        result_info TEXT,  -- JSON with row_count, columns, sample
        status TEXT DEFAULT 'waiting',
        guesses TEXT,  -- JSON array of guesses
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')    


    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM cases")
    if cursor.fetchone()[0] == 0:
        populate_sample_data(conn, cursor)
    
    # Initialize leaderboard with sample data
    cursor.execute("SELECT COUNT(*) FROM leaderboard")
    if cursor.fetchone()[0] == 0:
        sample_players = [
            ("Detective_Smith", 85, 4, 120.5, 8, 2),
            ("Sherlock_Holmes", 100, 5, 95.3, 5, 5),
            ("Miss_Marple", 60, 3, 150.2, 10, 1),
            ("Inspector_Clouseau", 40, 2, 180.0, 12, 0),
            ("Columbo", 75, 4, 110.8, 7, 1),
        ]
        cursor.executemany('''
        INSERT INTO leaderboard (player_name, total_score, completed_levels, fastest_completion_time, total_attempts, streak_count)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_players)
    
    conn.commit()
    conn.close()

def populate_sample_data(conn, cursor):
    """Populate database with sample crime data"""
    
    # Cases data
    cases_data = [
        (1, "The Midnight Burglary", "Burglary", date(2024, 1, 15), "High", 0, "Downtown", "Jewelry stolen from vault"),
        (2, "Park Avenue Murder", "Murder", date(2024, 1, 20), "High", 0, "Park Avenue", "Victim found in apartment"),
        (3, "Art Gallery Heist", "Theft", date(2024, 1, 10), "Medium", 1, "Museum District", "Painting stolen"),
        (4, "Corporate Espionage", "Fraud", date(2024, 1, 25), "High", 0, "Business District", "Trade secrets stolen"),
        (5, "Missing Person", "Missing Person", date(2024, 1, 5), "Low", 0, "Suburbs", "Person vanished"),
        (6, "Cyber Crime", "Fraud", date(2024, 1, 28), "High", 0, "Online", "Bank account hacking"),
        (7, "Street Robbery", "Robbery", date(2024, 1, 18), "Medium", 1, "Downtown", "Wallet stolen"),
        (8, "Car Theft", "Theft", date(2024, 1, 22), "Medium", 0, "Parking Garage", "Luxury car stolen"),
    ]
    
    cursor.executemany('''
    INSERT INTO cases (case_id, case_name, crime_type, date_opened, priority, solved, location, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', cases_data)
    
    # Suspects data
    suspects_data = [
        (1, 1, "James Wilson", 35, "Security Guard", "Near crime scene", "Inside job"),
        (2, 2, "Sarah Connor", 28, "Neighbor", "Last seen at 10 PM", "Dispute with victim"),
        (3, 2, "Michael Brown", 42, "Business Partner", "Out of town", "Financial motive"),
        (4, 3, "Elena Martinez", 31, "Art Dealer", "At gallery", "Wanted the painting"),
        (5, 4, "Robert Chen", 45, "Competitor CEO", "Business trip", "Corporate rivalry"),
        (6, 5, "Lisa Anderson", 29, "Friend", "Last contact Jan 3", "Unknown"),
        (7, 6, "Unknown Hacker", None, "Hacker", "Dark web", "Financial gain"),
        (8, 7, "Marcus Webb", 24, "Unemployed", "Near robbery scene", "Desperate for money"),
        (9, 8, "Victor Lee", 33, "Mechanic", "Near garage", "Car theft ring"),
    ]
    
    cursor.executemany('''
    INSERT INTO suspects (suspect_id, case_id, name, age, occupation, last_seen, motive)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', suspects_data)
    
    # Evidence data
    evidence_data = [
        (1, 1, "Fingerprints on window", "Physical", date(2024, 1, 16), 8),
        (2, 1, "Security footage", "Video", date(2024, 1, 16), 9),
        (3, 2, "Blood sample", "DNA", date(2024, 1, 21), 10),
        (4, 2, "Murder weapon", "Physical", date(2024, 1, 22), 9),
        (5, 3, "Empty frame", "Physical", date(2024, 1, 11), 7),
        (6, 4, "Hacked emails", "Digital", date(2024, 1, 26), 8),
        (7, 5, "Personal belongings", "Physical", date(2024, 1, 6), 5),
        (8, 6, "IP address logs", "Digital", date(2024, 1, 29), 9),
        (9, 7, "Security camera footage", "Video", date(2024, 1, 19), 6),
        (10, 8, "Tire tracks", "Physical", date(2024, 1, 23), 7),
    ]
    
    cursor.executemany('''
    INSERT INTO evidence (evidence_id, case_id, description, evidence_type, collected_date, forensic_value)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', evidence_data)
    
    # Detectives data
    detectives_data = [
        (1, "Detective Smith", "Senior Detective", 3),
        (2, "Detective Johnson", "Detective", 2),
        (3, "Detective Williams", "Junior Detective", 1),
    ]
    
    cursor.executemany('''
    INSERT INTO detectives (detective_id, name, rank, active_cases)
    VALUES (?, ?, ?, ?)
    ''', detectives_data)
    
    conn.commit()

def execute_query(query):
    """Execute SQL query and return results as DataFrame"""
    conn = sqlite3.connect('crime_academy.db')
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)

def get_table_info():
    """Get information about all tables"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    table_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        table_info[table_name] = {
            'columns': [col[1] for col in columns],
            'row_count': row_count,
            'sample': pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        }
    
    conn.close()
    return table_info

def save_score_to_leaderboard(player_name, score, level_completed, completion_time, attempts):
    """Save player score to leaderboard"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    # Check if player exists
    cursor.execute("SELECT * FROM leaderboard WHERE player_name = ?", (player_name,))
    player = cursor.fetchone()
    
    if player:
        # Update existing player
        cursor.execute('''
        UPDATE leaderboard 
        SET total_score = total_score + ?,
            completed_levels = completed_levels + ?,
            total_attempts = total_attempts + ?,
            streak_count = CASE 
                WHEN ? = 1 THEN streak_count + 1 
                ELSE 0 
            END,
            fastest_completion_time = MIN(COALESCE(fastest_completion_time, ?), ?),
            last_active = CURRENT_TIMESTAMP
        WHERE player_name = ?
        ''', (score, 1, attempts, level_completed, completion_time, completion_time, player_name))
    else:
        # Create new player
        cursor.execute('''
        INSERT INTO leaderboard (player_name, total_score, completed_levels, fastest_completion_time, total_attempts, streak_count)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_name, score, 1, completion_time, attempts, 1 if level_completed else 0))
    
    # Record challenge time
    cursor.execute('''
    INSERT INTO challenge_times (player_id, level_num, completion_time, attempts_before_success)
    VALUES ((SELECT player_id FROM leaderboard WHERE player_name = ?), ?, ?, ?)
    ''', (player_name, level_completed, completion_time, attempts))
    
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    """Get top players from leaderboard"""
    conn = sqlite3.connect('crime_academy.db')
    query = f'''
    SELECT player_name, total_score, completed_levels, 
           ROUND(fastest_completion_time, 1) as best_time,
           streak_count
    FROM leaderboard
    ORDER BY total_score DESC, completed_levels DESC, fastest_completion_time ASC
    LIMIT {limit}
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_player_rank(player_name):
    """Get player's rank on leaderboard"""
    df = get_leaderboard(100)
    if player_name in df['player_name'].values:
        rank = df[df['player_name'] == player_name].index[0] + 1
        return rank
    return None

def create_multiplayer_session(host_name, session_code):
    """Create a new multiplayer session"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO multiplayer_sessions (session_id, host_name, session_code, players)
    VALUES (?, ?, ?, ?)
    ''', (session_code, host_name, session_code, json.dumps([host_name])))
    
    conn.commit()
    conn.close()
    return session_code

def join_multiplayer_session(session_code, player_name):
    """Join an existing multiplayer session"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT players FROM multiplayer_sessions WHERE session_code = ?", (session_code,))
    result = cursor.fetchone()
    
    if result:
        players = json.loads(result[0])
        if player_name not in players:
            players.append(player_name)
            cursor.execute('''
            UPDATE multiplayer_sessions 
            SET players = ? 
            WHERE session_code = ?
            ''', (json.dumps(players), session_code))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def get_multiplayer_session(session_code):
    """Get multiplayer session details"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM multiplayer_sessions WHERE session_code = ?", (session_code,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'session_id': result[0],
            'host_name': result[1],
            'session_code': result[2],
            'current_level': result[3],
            'players': json.loads(result[4]),
            'started': result[5],
            'created_at': result[6]
        }
    return None