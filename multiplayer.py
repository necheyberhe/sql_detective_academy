"""
Multiplayer Module for SQL Detective Academy
Handles race mode and query guessing game with database persistence
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime

def create_race_session(host_name):
    """Create a new race session"""
    import uuid
    session_id = str(uuid.uuid4())[:8].upper()
    
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    players_json = json.dumps([host_name])
    player_progress_json = json.dumps({host_name: []})
    
    cursor.execute('''
    INSERT INTO race_sessions (session_id, host_name, session_code, players, player_progress, status)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, host_name, session_id, players_json, player_progress_json, 'waiting'))
    
    conn.commit()
    conn.close()
    return session_id

def join_race_session(session_code, player_name):
    """Join an existing race session"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT players, player_progress, status FROM race_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    
    if result:
        players = json.loads(result[0])
        player_progress = json.loads(result[1])
        status = result[2]
        
        if status == 'waiting' and player_name not in players:
            players.append(player_name)
            player_progress[player_name] = []
            
            cursor.execute('''
            UPDATE race_sessions 
            SET players = ?, player_progress = ?
            WHERE session_id = ?
            ''', (json.dumps(players), json.dumps(player_progress), session_code))
            
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def start_race_session(session_code):
    """Start the race"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE race_sessions 
    SET status = 'racing', start_time = CURRENT_TIMESTAMP
    WHERE session_id = ?
    ''', (session_code,))
    
    conn.commit()
    conn.close()

def update_race_progress(session_code, player_name, completed_levels):
    """Update player's progress in race"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT player_progress FROM race_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    
    if result:
        player_progress = json.loads(result[0])
        player_progress[player_name] = list(completed_levels)
        
        cursor.execute('''
        UPDATE race_sessions 
        SET player_progress = ?
        WHERE session_id = ?
        ''', (json.dumps(player_progress), session_code))
        
        conn.commit()
    conn.close()

def get_race_status(session_code):
    """Get current race status"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM race_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'session_id': result[0],
            'host_name': result[1],
            'players': json.loads(result[3]),
            'player_progress': json.loads(result[4]),
            'status': result[5],
            'start_time': result[6]
        }
    return None

def create_guessing_game(writer_name):
    """Create a new query guessing game"""
    import uuid
    session_id = str(uuid.uuid4())[:8].upper()
    
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO guessing_sessions (session_id, writer_name, session_code, status, guesses)
    VALUES (?, ?, ?, ?, ?)
    ''', (session_id, writer_name, session_id, 'waiting', json.dumps([])))
    
    conn.commit()
    conn.close()
    return session_id

def lock_guessing_query(session_code, query, result_info):
    """Lock the secret query for guessing game"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE guessing_sessions 
    SET secret_query = ?, result_info = ?, status = 'ready'
    WHERE session_id = ?
    ''', (query, json.dumps(result_info), session_code))
    
    conn.commit()
    conn.close()

def join_guessing_game(session_code, guesser_name):
    """Join a guessing game as guesser"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, writer_name FROM guessing_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == 'ready':
        return True, result[1]
    return False, None

def submit_guess(session_code, guesser_name, guess_query, is_correct):
    """Submit a guess to the guessing game"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT guesses FROM guessing_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    
    if result:
        guesses = json.loads(result[0])
        guesses.append({
            'guesser': guesser_name,
            'query': guess_query,
            'correct': is_correct,
            'timestamp': str(datetime.now())
        })
        
        cursor.execute('''
        UPDATE guessing_sessions 
        SET guesses = ?
        WHERE session_id = ?
        ''', (json.dumps(guesses), session_code))
        
        conn.commit()
    conn.close()

def get_guessing_game(session_code):
    """Get guessing game details"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM guessing_sessions WHERE session_id = ?", (session_code,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'session_id': result[0],
            'writer_name': result[1],
            'secret_query': result[3],
            'result_info': json.loads(result[4]) if result[4] else None,
            'status': result[5],
            'guesses': json.loads(result[6]) if result[6] else []
        }
    return None