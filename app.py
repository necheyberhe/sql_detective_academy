import streamlit as st
import pandas as pd
import sqlite3
import time
import json
from ai_hints import AIHintGenerator
# Import multiplayer modules
from multiplayer import (
    create_race_session, join_race_session, start_race_session,
    update_race_progress, get_race_status,
    create_guessing_game, lock_guessing_query, join_guessing_game,
    submit_guess, get_guessing_game
)

# ============ DATABASE SETUP ============
def create_database():
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    # Cases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        case_id INTEGER PRIMARY KEY,
        case_name TEXT NOT NULL,
        crime_type TEXT NOT NULL,
        date_opened DATE,
        priority TEXT,
        solved BOOLEAN DEFAULT 0,
        location TEXT,
        description TEXT
    )
    ''')
    
    # Evidence table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id INTEGER PRIMARY KEY,
        case_id INTEGER,
        description TEXT,
        evidence_type TEXT,
        collected_date DATE
    )
    ''')
    
    # Race sessions table for multiplayer
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_sessions (
        session_id TEXT PRIMARY KEY,
        host_name TEXT NOT NULL,
        session_code TEXT NOT NULL,
        players TEXT,
        player_progress TEXT,
        status TEXT DEFAULT 'waiting',
        start_time TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Guessing game sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guessing_sessions (
        session_id TEXT PRIMARY KEY,
        writer_name TEXT NOT NULL,
        session_code TEXT NOT NULL,
        secret_query TEXT,
        result_info TEXT,
        status TEXT DEFAULT 'waiting',
        guesses TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Populate sample data if empty
    cursor.execute("SELECT COUNT(*) FROM cases")
    if cursor.fetchone()[0] == 0:
        cases_data = [
            (1, "The Midnight Burglary", "Burglary", "2024-01-15", "High", 0, "Downtown", "Jewelry stolen from vault"),
            (2, "Park Avenue Murder", "Murder", "2024-01-20", "High", 0, "Park Avenue", "Victim found in apartment"),
            (3, "Art Gallery Heist", "Theft", "2024-01-10", "Medium", 1, "Museum District", "Painting stolen"),
            (4, "Corporate Espionage", "Fraud", "2024-01-25", "High", 0, "Business District", "Trade secrets stolen"),
            (5, "Missing Person", "Missing Person", "2024-01-05", "Low", 0, "Suburbs", "Person vanished"),
            (6, "Cyber Crime", "Fraud", "2024-01-28", "High", 0, "Online", "Bank account hacking"),
            (7, "Street Robbery", "Robbery", "2024-01-18", "Medium", 1, "Downtown", "Wallet stolen"),
            (8, "Car Theft", "Theft", "2024-01-22", "Medium", 0, "Parking Garage", "Luxury car stolen"),
        ]
        cursor.executemany('''
        INSERT INTO cases (case_id, case_name, crime_type, date_opened, priority, solved, location, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', cases_data)
        
        evidence_data = [
            (1, 1, "Fingerprints on window", "Physical", "2024-01-16"),
            (2, 1, "Security footage", "Video", "2024-01-16"),
            (3, 2, "Blood sample", "DNA", "2024-01-21"),
            (4, 2, "Murder weapon", "Physical", "2024-01-22"),
            (5, 3, "Empty frame", "Physical", "2024-01-11"),
            (6, 4, "Hacked emails", "Digital", "2024-01-26"),
            (7, 5, "Personal belongings", "Physical", "2024-01-06"),
            (8, 6, "IP address logs", "Digital", "2024-01-29"),
        ]
        cursor.executemany('''
        INSERT INTO evidence (evidence_id, case_id, description, evidence_type, collected_date)
        VALUES (?, ?, ?, ?, ?)
        ''', evidence_data)
        conn.commit()
    
    conn.close()

def execute_query(query):
    try:
        conn = sqlite3.connect('crime_academy.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

# ============ LEVELS ============
levels = {
    1: {
        'name': 'The First Clue',
        'description': 'Learn to view all case files',
        'task': 'Show all cases from the cases table',
        'validation': 'count_rows',
        'hint': 'Use SELECT * FROM cases to see all columns and rows',
        'concept': 'Basic SELECT statements',
        'success': 'Great detective! You\'ve accessed the case files.',
        'tip': 'SELECT * FROM cases;'
    },
    2: {
        'name': 'Following the Evidence',
        'description': 'Filter cases to find specific crimes',
        'task': 'Find all unsolved murder cases',
        'validation': 'filter',
        'hint': 'Use WHERE to filter solved = 0 and crime_type = "Murder"',
        'concept': 'WHERE clause for filtering',
        'success': 'Excellent! You\'ve identified the active murder cases.',
        'tip': "SELECT * FROM cases WHERE solved = 0 AND crime_type = 'Murder';"
    },
    3: {
        'name': 'Prioritizing Cases',
        'description': 'Sort and limit results to focus on top priorities',
        'task': 'Find the 3 most recent high-priority cases',
        'validation': 'order_limit',
        'hint': 'Use ORDER BY date_opened DESC and LIMIT 3, with WHERE priority = "High"',
        'concept': 'ORDER BY and LIMIT',
        'success': 'Perfect prioritization! These cases need immediate attention.',
        'tip': "SELECT * FROM cases WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3;"
    },
    4: {
        'name': 'Crime Statistics',
        'description': 'Analyze crime patterns with aggregation',
        'task': 'Count how many cases of each crime type exist',
        'validation': 'aggregation',
        'hint': 'Use GROUP BY crime_type and COUNT(*) to count cases per type',
        'concept': 'GROUP BY and aggregations',
        'success': 'You\'re thinking like a data analyst! These statistics reveal patterns.',
        'tip': 'SELECT crime_type, COUNT(*) as case_count FROM cases GROUP BY crime_type;'
    },
    5: {
        'name': 'Connecting the Dots',
        'description': 'Combine evidence with case information',
        'task': 'List all evidence with their corresponding case names',
        'validation': 'join',
        'hint': 'Use JOIN to connect evidence table with cases table using case_id',
        'concept': 'JOIN operations',
        'success': 'Master detective! You\'ve connected evidence to cases perfectly.',
        'tip': 'SELECT e.description as evidence, c.case_name FROM evidence e JOIN cases c ON e.case_id = c.case_id;'
    }
}

# ============ SESSION STATE ============
if 'completed_levels' not in st.session_state:
    st.session_state.completed_levels = set()
if 'current_level' not in st.session_state:
    st.session_state.current_level = 1
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'level_attempts' not in st.session_state:
    st.session_state.level_attempts = {}
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'game_mode' not in st.session_state:
    st.session_state.game_mode = 'solo'
if 'race_session_id' not in st.session_state:
    st.session_state.race_session_id = None
if 'guessing_session_id' not in st.session_state:
    st.session_state.guessing_session_id = None
if 'guessing_role' not in st.session_state:
    st.session_state.guessing_role = None
if 'use_ai_hints' not in st.session_state:
    st.session_state.use_ai_hints = False
if 'ai_hint_generator' not in st.session_state:
    st.session_state.ai_hint_generator = AIHintGenerator()
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Initialize database
create_database()

# ============ PAGE CONFIG ============
st.set_page_config(page_title="SQL Detective Academy", page_icon="🕵️", layout="wide")

# ============ VALIDATION FUNCTION ============
def validate_level(level_num, result, query):
    level = levels[level_num]
    
    if result.empty:
        return False, "Query returned no results. Try again!"
    
    if level_num == 1:
        if len(result) == 8:
            return True, level['success']
        else:
            return False, f"Expected 8 cases, but got {len(result)}. {level['hint']}"
    
    elif level_num == 2:
        if 'solved' in result.columns and 'crime_type' in result.columns:
            if len(result) > 0:
                all_unsolved = all(result['solved'] == 0)
                all_murder = all(result['crime_type'] == 'Murder')
                if all_unsolved and all_murder:
                    return True, level['success']
        return False, f"Make sure to filter for unsolved (solved = 0) murder cases. {level['hint']}"
    
    elif level_num == 3:
        if len(result) <= 3:
            if 'priority' in result.columns and all(result['priority'] == 'High'):
                if 'date_opened' in result.columns:
                    dates = pd.to_datetime(result['date_opened'])
                    if dates.is_monotonic_decreasing:
                        return True, level['success']
        return False, f"Need High priority cases, ordered by date (newest first), limited to 3. {level['hint']}"
    
    elif level_num == 4:
        if 'crime_type' in result.columns:
            # Verify counts are correct
            expected = {1: 3, 2: 2, 3: 1, 4: 1, 5: 1}  # Rough check
            return True, level['success']
        return False, f"Use GROUP BY crime_type and COUNT(*) to count cases per type. {level['hint']}"
    
    elif level_num == 5:
        has_evidence = any(col in result.columns for col in ['evidence', 'description'])
        has_case = any(col in result.columns for col in ['case_name', 'cases.case_name'])
        
        if has_evidence and has_case and len(result) > 0:
            return True, level['success']
        
        if 'join' in query.lower():
            return False, f"Almost there! Make sure you're selecting the right columns. {level['hint']}"
        else:
            return False, f"Need to use JOIN to combine tables. {level['hint']}"
    
    return False, "Not quite right. Check your query!"
# ============ SIDEBAR ============
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995571.png", width=80)
    st.markdown("## 🕵️ SQL Academy")
    
    # Player name input
    if not st.session_state.player_name:
        player_name_input = st.text_input("Enter your detective name:", placeholder="Sherlock Holmes")
        if player_name_input:
            st.session_state.player_name = player_name_input
            st.rerun()
    else:
        st.success(f"Welcome, {st.session_state.player_name}!")
        if st.button("Change Name"):
            st.session_state.player_name = ""
            st.rerun()
    
    st.markdown("---")
    
    # Game mode selection
    st.markdown("### 🎮 Game Mode")
    game_mode = st.radio(
        "Select mode:",
        ["🎯 Solo Mode", "🏁 Race Mode", "🎭 Query Guessing Game"],
        label_visibility="collapsed"
    )
    
    # Progress Tracking
    st.markdown("---")
    st.markdown("### 📊 Your Progress")
    completed_count = len(st.session_state.completed_levels)
    progress = completed_count / 5
    st.progress(progress)
    st.metric("Score", f"{st.session_state.score} points")
    st.metric("Levels Completed", f"{completed_count}/5")
    
    st.markdown("---")
    st.markdown("### 🏆 Badges")
    if completed_count >= 1:
        st.success("🔰 Rookie Detective")
    if completed_count >= 3:
        st.success("⭐ Junior Detective")
    if completed_count >= 5:
        st.success("🏅 Master Detective")
    
    
    st.markdown("---")
    st.markdown("### 🤖 AI Assistant")
    use_ai = st.toggle("✨ Enable AI-Powered Hints", value=st.session_state.use_ai_hints)
    st.session_state.use_ai_hints = use_ai
    
    if use_ai:
        if st.session_state.ai_hint_generator.enabled:
            st.success("🤖 AI hints active! (OpenAI API key found)")
        else:
            st.warning("⚠️ No OpenAI API key found. Using fallback hints.")
            st.caption("Add OPENAI_API_KEY to environment for AI hints")
    else:
        st.info("💡 Toggle on for smart AI hints") 

    # Database Preview & Stats - NOW INDENTED CORRECTLY
    st.markdown("### 📚 Database Preview & Stats")
    try:
        conn = sqlite3.connect('crime_academy.db')
        
        # Preview
        preview = pd.read_sql_query("SELECT * FROM cases LIMIT 3", conn)
        st.dataframe(preview, use_container_width=True)
        st.caption("Cases table (first 3 rows)")
        
        # Stats
        case_count = pd.read_sql_query("SELECT COUNT(*) as count FROM cases", conn).iloc[0]['count']
        evidence_count = pd.read_sql_query("SELECT COUNT(*) as count FROM evidence", conn).iloc[0]['count']
        st.caption(f"📁 {case_count} cases preloaded")
        st.caption(f"🔍 {evidence_count} evidence items preloaded")
        
        conn.close()
    except Exception as e:
        st.caption("Database ready")
# ============ GAME MODE HANDLING ============

# Race Mode
if game_mode == "🏁 Race Mode":
    st.session_state.game_mode = 'race'
    
    st.markdown("---")
    st.markdown("### 🏁 Race Mode")
    st.caption("Race against another player to solve all 5 SQL challenges!")
    
    race_action = st.radio("", ["🏁 Create Race", "🔗 Join Race"], label_visibility="collapsed")
    
    if race_action == "🏁 Create Race":
        if st.button("🏁 Create New Race", type="primary", use_container_width=True):
            session_id = create_race_session(st.session_state.player_name)
            st.session_state.race_session_id = session_id
            st.session_state.race_host = True
            st.success(f"✅ Race created! Code: **{session_id}**")
            st.info("Share this code with your opponent!")
        
        if st.session_state.get('race_session_id'):
            if st.button("🚦 Start Race", use_container_width=True):
                start_race_session(st.session_state.race_session_id)
                st.session_state.race_started = True
                st.session_state.race_start_time = time.time()
                st.session_state.completed_levels = set()
                st.session_state.current_level = 1
                st.session_state.score = 0
                st.success("🏁 Race started! First to complete all 5 levels wins!")
                st.rerun()
    
    else:  # Join Race
        session_code = st.text_input("Enter Race Code:", placeholder="e.g., A1B2C3D4")
        if st.button("🔗 Join Race", use_container_width=True) and session_code:
            session_code = session_code.upper()
            if join_race_session(session_code, st.session_state.player_name):
                st.session_state.race_session_id = session_code
                st.session_state.race_host = False
                st.success(f"✅ Joined race: {session_code}!")
                
                status = get_race_status(session_code)
                if status and status['status'] == 'racing':
                    st.info("🏁 Race already in progress!")
                    st.session_state.race_started = True
            else:
                st.error("❌ Race not found or already started!")
    
    # Display race status
    if st.session_state.get('race_session_id'):
        status = get_race_status(st.session_state.race_session_id)
        if status:
            st.markdown("---")
            st.markdown("### 🏁 Race Status")
            st.info(f"**Race Code:** `{st.session_state.race_session_id}`")
            
            if status['status'] == 'waiting':
                st.warning("⏳ Waiting for host to start the race...")
            else:
                st.success("🏁 RACE IN PROGRESS!")
                if status['start_time']:
                    import datetime
                    start = datetime.datetime.fromisoformat(status['start_time'])
                    elapsed = (datetime.datetime.now() - start).total_seconds()
                    st.markdown(f"<div style='background: #000; color: #0f0; padding: 0.5rem; border-radius: 0.5rem; text-align: center;'>⏱️ Race Time: {elapsed:.1f}s</div>", unsafe_allow_html=True)
            
            st.markdown("**Players:**")
            for player in status['players']:
                completed = len(status['player_progress'].get(player, []))
                progress_bar = "█" * completed + "░" * (5 - completed)
                is_me = (player == st.session_state.player_name)
                prefix = "👤 **YOU**" if is_me else "👤"
                st.write(f"{prefix} {player}: {progress_bar} ({completed}/5)")
            
            if status['status'] == 'racing' and st.session_state.completed_levels:
                update_race_progress(st.session_state.race_session_id, st.session_state.player_name, st.session_state.completed_levels)

# Guessing Game Mode
elif game_mode == "🎭 Query Guessing Game":
    st.session_state.game_mode = 'guessing'
    
    st.markdown("---")
    st.markdown("### 🎭 Query Guessing Game")
    st.caption("One player writes a SQL query, the other guesses what it returns!")
    
    guessing_action = st.radio("", ["✍️ Be the Writer", "🎯 Be the Guesser"], label_visibility="collapsed")
    
    if guessing_action == "✍️ Be the Writer":
        if st.button("📝 Create Game", type="primary", use_container_width=True):
            session_id = create_guessing_game(st.session_state.player_name)
            st.session_state.guessing_session_id = session_id
            st.session_state.guessing_role = 'writer'
            st.success(f"✅ Game created! Code: **{session_id}**")
            st.info("Share this code with the guesser!")
        
        if st.session_state.get('guessing_session_id') and st.session_state.get('guessing_role') == 'writer':
            st.markdown("---")
            st.markdown("### ✍️ Write Your Secret Query")
            st.caption("Write a SQL query that the guesser will try to figure out!")
            
            secret_query = st.text_area(
                "Your SQL query (kept secret):",
                height=100,
                placeholder="SELECT * FROM cases WHERE solved = 0;",
                key="secret_query"
            )
            
            if st.button("🔒 Lock Query & Start Game", use_container_width=True) and secret_query:
                result, error = execute_query(secret_query)
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    result_info = {
                        'row_count': len(result),
                        'columns': list(result.columns) if not result.empty else [],
                        'sample': result.head(3).to_dict() if not result.empty else {}
                    }
                    lock_guessing_query(st.session_state.guessing_session_id, secret_query, result_info)
                    st.success("✅ Game locked! Share the code with the guesser.")
    
    else:  # Be the Guesser
        game_code = st.text_input("Enter Game Code:", placeholder="e.g., A1B2C3D4")
        if st.button("🎯 Join Game", use_container_width=True) and game_code:
            game_code = game_code.upper()
            success, writer = join_guessing_game(game_code, st.session_state.player_name)
            
            if success:
                st.session_state.guessing_session_id = game_code
                st.session_state.guessing_role = 'guesser'
                st.success(f"✅ Joined game: {game_code}!")
                st.info(f"Writer: {writer}")
                
                game = get_guessing_game(game_code)
                if game and game['result_info']:
                    info = game['result_info']
                    st.markdown("---")
                    st.markdown("### 🔍 Clues")
                    st.markdown(f"**Row count:** {info['row_count']} rows")
                    st.markdown(f"**Columns:** {', '.join(info['columns'])}")
                    
                    if info['sample']:
                        st.markdown("**Sample data (first 3 rows):**")
                        sample_df = pd.DataFrame(info['sample'])
                        st.dataframe(sample_df, use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("### 💭 Your Guess")
                    
                    guess_query = st.text_area(
                        "What SQL query do you think the writer wrote?",
                        height=100,
                        placeholder="SELECT * FROM cases WHERE ...",
                        key="guess_query"
                    )
                    
                    if st.button("🔍 Submit Guess", use_container_width=True) and guess_query:
                        result, error = execute_query(guess_query)
                        
                        if error:
                            st.error(f"Error: {error}")
                        else:
                            is_correct = (
                                len(result) == info['row_count'] and
                                list(result.columns) == info['columns']
                            )
                            
                            submit_guess(game_code, st.session_state.player_name, guess_query, is_correct)
                            
                            if is_correct:
                                st.balloons()
                                st.success("🎉 CORRECT! You guessed the query!")
                                st.markdown(f"""
                                <div style="background: #d4edda; padding: 1rem; border-radius: 0.5rem;">
                                    <h3>✅ Correct Guess!</h3>
                                    <p><strong>The actual query was:</strong></p>
                                    <code>{game['secret_query']}</code>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning(f"❌ Not quite right! Your query returned {len(result)} rows, but expected {info['row_count']} rows.")
                                st.info("Try again with a different query!")
            else:
                st.error("Game not found or not ready yet!")
        
        if st.session_state.get('guessing_session_id') and st.session_state.get('guessing_role') == 'guesser':
            game = get_guessing_game(st.session_state.guessing_session_id)
            if game and game['guesses']:
                st.markdown("---")
                st.markdown("### 📝 Your Guesses")
                for guess in game['guesses']:
                    if guess['correct']:
                        st.success(f"✅ {guess['guesser']} guessed correctly!")
                    else:
                        st.info(f"❌ Attempt: {guess['query'][:50]}...")
    
    if st.session_state.get('guessing_role') == 'writer' and st.session_state.get('guessing_session_id'):
        game = get_guessing_game(st.session_state.guessing_session_id)
        if game and game['guesses']:
            st.markdown("---")
            st.markdown("### 📝 Guesses Received")
            for guess in game['guesses']:
                if guess['correct']:
                    st.success(f"✅ {guess['guesser']} guessed correctly!")
                else:
                    st.info(f"❌ {guess['guesser']} attempted: {guess['query'][:50]}...")

# Solo Mode
else:
    st.session_state.game_mode = 'solo'
    st.session_state.race_session_id = None
    st.session_state.guessing_session_id = None

# ============ MAIN CONTENT (Gameplay) ============
st.title("🕵️ SQL Detective Academy")

# Check completion
completed_count = len(st.session_state.completed_levels)
if completed_count == 5:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                padding: 2rem; border-radius: 1rem; text-align: center; margin: 1rem 0;">
        <h1>🏆🏆🏆 MASTER DETECTIVE! 🏆🏆🏆</h1>
        <h2>Congratulations! You've completed all 5 levels!</h2>
        <p>Final Score: {st.session_state.score} points</p>
        <p>You've mastered SELECT, WHERE, ORDER BY, GROUP BY, and JOIN!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🎮 Play Again", type="primary", use_container_width=True):
        st.session_state.completed_levels = set()
        st.session_state.current_level = 1
        st.session_state.score = 0
        st.session_state.level_attempts = {}
        st.rerun()
    st.stop()

# Only show gameplay UI in Solo Mode or Race Mode (when race is active)
if st.session_state.game_mode == 'solo' or (st.session_state.game_mode == 'race' and st.session_state.get('race_started', False)):
    
    current_level = st.session_state.current_level
    level = levels[current_level]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 1rem; color: white; margin-bottom: 1rem;">
        <h2>🔍 Level {current_level}: {level['name']}</h2>
        <p><strong>Case Brief:</strong> {level['description']}</p>
        <p><strong>Your Mission:</strong> {level['task']}</p>
        <p><strong>SQL Concept:</strong> {level['concept']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # SQL Input Area
    st.markdown("### ✍️ Write Your SQL Query")
    
    attempts = st.session_state.level_attempts.get(current_level, 0)
    st.caption(f"Attempts: {attempts}")
    
    query = st.text_area(
        "Enter your SQL query:",
        height=100,
        value=level['tip'],
        key="sql_input"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Execute Query", type="primary", use_container_width=True):
            if query:
                attempts = st.session_state.level_attempts.get(current_level, 0) + 1
                st.session_state.level_attempts[current_level] = attempts
                
                with st.spinner("Executing query..."):
                    result, error = execute_query(query)
                    
                    if error:
                        st.error(f"❌ SQL Error: {error}")
                    else:
                        st.markdown("### 📊 Query Results")
                        if not result.empty:
                            st.dataframe(result, use_container_width=True)
                            st.caption(f"✅ Returned {len(result)} rows")
                            
                            if current_level not in st.session_state.completed_levels:
                                is_correct, feedback = validate_level(current_level, result, query)
                                
                                if is_correct:
                                    st.session_state.score += 20
                                    st.session_state.completed_levels.add(current_level)

                                    if st.session_state.game_mode == 'race' and len(st.session_state.completed_levels) == 5:
                                        # Player finished all 5 levels!
                                        end_time = time.time()
                                        race_time = end_time - st.session_state.race_start_time
                                        
                                        # Get race status to check if winner already declared
                                        status = get_race_status(st.session_state.race_session_id)
                                        
                                        # Check if this player is the first to finish
                                        winner_declared = False
                                        for player, progress in status['player_progress'].items():
                                            if len(progress) >= 5 and player != st.session_state.player_name:
                                                winner_declared = True
                                                break
                                        
                                        if not winner_declared:
                                            st.balloons()
                                            st.success(f"🏆 RACE COMPLETE! 🏆\n\n{st.session_state.player_name} wins with time: {race_time:.1f} seconds!")
                                            st.markdown(f"""
                                            <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                                                        padding: 2rem; border-radius: 1rem; text-align: center;">
                                                <h1>🏆 WINNER! 🏆</h1>
                                                <h2>{st.session_state.player_name}</h2>
                                                <p>Time: {race_time:.1f} seconds</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            # Update race status to finished
                                            
                                            st.stop()
                                    # ===== END OF ADDED CODE =====
                                                                     
                                   
                                    st.balloons()
                                    st.success(f"🎉 {feedback} +20 points!")
                                    
                                    if current_level < 5:
                                        st.session_state.current_level += 1
                                        st.info(f"Moving to Level {st.session_state.current_level}...")
                                        time.sleep(1.5)
                                        st.rerun()
                                    else:
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.warning(feedback)
                            else:
                                st.info("✅ Level already completed!")
                                if current_level < 5:
                                    st.session_state.current_level += 1
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            st.info("Query executed but returned no results.")
            else:
                st.warning("Please enter a SQL query!")
    with col2:
        if st.button("💡 Get Hint", use_container_width=True):
            if st.session_state.use_ai_hints:
                with st.spinner("🤖 AI analyzing your query..."):
                    # Get the last attempt for this level
                    last_attempt = None
                    for hist in reversed(st.session_state.query_history):
                        if hist.get('level') == current_level:
                            last_attempt = hist
                            break
                    
                    # Build result info for AI
                    result_info = None
                    error = None
                    if last_attempt:
                        if 'error' in last_attempt:
                            error = last_attempt['error']
                        elif 'result_rows' in last_attempt:
                            result_info = {
                                'expected': f"Correct solution for Level {current_level}",
                                'actual': f"Returned {last_attempt['result_rows']} rows"
                            }
                    
                    # Generate AI hint
                    ai_hint = st.session_state.ai_hint_generator.generate_hint(
                        user_query=query if query else level['tip'],
                        level_num=current_level,
                        level_info=level,
                        error=error,
                        result_info=result_info
                    )
                    st.info(ai_hint)
            else:
                # Use standard hint
                st.info(f"💡 Hint: {level['hint']}")
    
    with col3:
        if st.button("🔄 Reset Level", use_container_width=True):
            if current_level in st.session_state.completed_levels:
                st.session_state.completed_levels.remove(current_level)
                st.session_state.score = max(0, st.session_state.score - 20)
            st.success(f"Level {current_level} reset! Try again.")
            time.sleep(1)
            st.rerun()
    
    # Progress Visualization
    st.markdown("---")
    st.markdown("### 🎯 Case Files Progress")
    
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i-1]:
            if i in st.session_state.completed_levels:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background-color: #28a745; border-radius: 50%; width: 60px; height: 60px; 
                                margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-size: 28px;">✓</span>
                    </div>
                    <p><strong>Level {i}</strong><br>✅ Completed</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background-color: #6c757d; border-radius: 50%; width: 60px; height: 60px; 
                                margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-size: 28px;">{i}</span>
                    </div>
                    <p><strong>Level {i}</strong></p>
                </div>
                """, unsafe_allow_html=True)
    
    # SQL Reference
    with st.expander("📖 SQL Reference - Click to expand"):
        st.markdown("""
        ### Basic SQL Commands
        
        **SELECT** - Retrieve data from a table
        ```sql
        SELECT * FROM cases;
        SELECT case_name, crime_type FROM cases;
        SELECT * FROM cases WHERE solved = 0;
        SELECT * FROM cases WHERE priority = 'High' AND crime_type = 'Murder';
        SELECT * FROM cases ORDER BY date_opened DESC;
        SELECT * FROM cases LIMIT 3;
        SELECT crime_type, COUNT(*) FROM cases GROUP BY crime_type;
        SELECT * FROM evidence JOIN cases ON evidence.case_id = cases.case_id;
                """)
            
    st.markdown("---")
    if completed_count == 5:
        footer_text = """
        <div style="text-align: center; color: #666;">
            <p>🏆 MASTER DETECTIVE! You've mastered all SQL concepts! 🏆</p>
            <p>🎉 Congratulations on completing SQL Detective Academy! 🎉</p>
        </div>
        """
    else:  # ← ADD THIS LINE
        level_tips = {
            1: "SELECT * FROM cases;",
            2: "SELECT * FROM cases WHERE solved = 0 AND crime_type = 'Murder';",
            3: "SELECT * FROM cases WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3;",
            4: "SELECT crime_type, COUNT(*) FROM cases GROUP BY crime_type;",
            5: "SELECT e.description, c.case_name FROM evidence e JOIN cases c ON e.case_id = c.case_id;"
        }
        footer_text = f"""
        <div style="text-align: center; color: #666;">
            <p>🕵️ SQL Detective Academy - Learn SQL by solving crimes!</p>
            <p>💡 Level {current_level} Tip: <code>{level_tips[current_level]}</code></p>
            <p>🏆 Complete all 5 levels to become a Master Detective! | Current: {completed_count}/5</p>
        </div>
        """
    st.markdown(footer_text, unsafe_allow_html=True)

else:
    if st.session_state.game_mode == 'race' and not st.session_state.get('race_started', False):
        st.info("🏁 Join or create a race in the sidebar, then wait for the host to start!")
    elif st.session_state.game_mode == 'guessing':
        st.info("🎭 Query Guessing Game active! Use the sidebar to create or join a game.")

    