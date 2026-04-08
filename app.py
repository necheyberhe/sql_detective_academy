import streamlit as st
import pandas as pd
import sqlite3
import time
import json
import datetime
from ai_hints import AIHintGenerator
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id INTEGER PRIMARY KEY,
        case_id INTEGER,
        description TEXT,
        evidence_type TEXT,
        collected_date DATE
    )
    ''')
    
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
        'hint': 'Use SELECT * FROM cases to see all columns and rows',
        'concept': 'Basic SELECT statements',
        'success': 'Great detective! You\'ve accessed the case files.',
        'tip': 'SELECT * FROM cases;'
    },
    2: {
        'name': 'Following the Evidence',
        'description': 'Filter cases to find specific crimes',
        'task': 'Find all unsolved murder cases',
        'hint': 'Use WHERE to filter solved = 0 and crime_type = "Murder"',
        'concept': 'WHERE clause for filtering',
        'success': 'Excellent! You\'ve identified the active murder cases.',
        'tip': "SELECT * FROM cases WHERE solved = 0 AND crime_type = 'Murder';"
    },
    3: {
        'name': 'Prioritizing Cases',
        'description': 'Sort and limit results to focus on top priorities',
        'task': 'Find the 3 most recent high-priority cases',
        'hint': 'Use ORDER BY date_opened DESC and LIMIT 3, with WHERE priority = "High"',
        'concept': 'ORDER BY and LIMIT',
        'success': 'Perfect prioritization! These cases need immediate attention.',
        'tip': "SELECT * FROM cases WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3;"
    },
    4: {
        'name': 'Crime Statistics',
        'description': 'Analyze crime patterns with aggregation',
        'task': 'Count how many cases of each crime type exist',
        'hint': 'Use GROUP BY crime_type and COUNT(*) to count cases per type',
        'concept': 'GROUP BY and aggregations',
        'success': 'You\'re thinking like a data analyst! These statistics reveal patterns.',
        'tip': 'SELECT crime_type, COUNT(*) as case_count FROM cases GROUP BY crime_type;'
    },
    5: {
        'name': 'Connecting the Dots',
        'description': 'Combine evidence with case information',
        'task': 'List all evidence with their corresponding case names',
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
if 'race_host' not in st.session_state:
    st.session_state.race_host = False
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
    
    st.markdown("### 🎮 Game Mode")
    game_mode = st.radio(
        "Select mode:",
        ["🎯 Solo Mode", "🏁 Race Mode", "🎭 Query Guessing Game"],
        label_visibility="collapsed"
    )
    
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
            st.success("🤖 AI hints active!")
        else:
            st.warning("⚠️ No OpenAI API key found. Using fallback hints.")
    else:
        st.info("💡 Toggle on for smart AI hints")

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
        
        if st.session_state.get('race_session_id') and st.session_state.race_host:
            if st.button("🚦 Start Race", use_container_width=True):
                start_race_session(st.session_state.race_session_id)
                st.success("🏁 Race started!")
                st.rerun()
    
    else:
        session_code = st.text_input("Enter Race Code:", placeholder="e.g., A1B2C3D4")
        if st.button("🔗 Join Race", use_container_width=True) and session_code:
            session_code = session_code.upper()
            if join_race_session(session_code, st.session_state.player_name):
                st.session_state.race_session_id = session_code
                st.session_state.race_host = False
                st.success(f"✅ Joined race: {session_code}!")
                st.rerun()
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
                if st.session_state.get('race_host', False):
                    st.info("👑 You are the host. Click 'Start Race' above to begin!")
                else:
                    st.info("Waiting for host to start...")
                    # Auto-refresh every 3 seconds for players waiting
                    import time
                    time.sleep(3)
                    st.rerun()
            else:
                st.success("🏁 RACE IN PROGRESS!")
                if status['start_time']:
                    start = datetime.datetime.fromisoformat(status['start_time'])
                    elapsed = (datetime.datetime.now() - start).total_seconds()
                    st.markdown(f"⏱️ Race Time: {elapsed:.1f}s")
            
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
        
        if st.session_state.get('guessing_session_id') and st.session_state.guessing_role == 'writer':
            st.markdown("---")
            st.markdown("### ✍️ Write Your Secret Query")
            secret_query = st.text_area("Your SQL query:", height=100, key="secret_query")
            
            if st.button("🔒 Lock Query", use_container_width=True) and secret_query:
                result, error = execute_query(secret_query)
                if not error:
                    result_info = {
                        'row_count': len(result),
                        'columns': list(result.columns) if not result.empty else [],
                        'sample': result.head(3).to_dict() if not result.empty else {}
                    }
                    lock_guessing_query(st.session_state.guessing_session_id, secret_query, result_info)
                    st.success("✅ Game locked!")
    
    else:
        game_code = st.text_input("Enter Game Code:", placeholder="e.g., A1B2C3D4")
        if st.button("🎯 Join Game", use_container_width=True) and game_code:
            game_code = game_code.upper()
            success, writer = join_guessing_game(game_code, st.session_state.player_name)
            if success:
                st.session_state.guessing_session_id = game_code
                st.session_state.guessing_role = 'guesser'
                st.success(f"✅ Joined game: {game_code}!")

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
                padding: 2rem; border-radius: 1rem; text-align: center;">
        <h1>🏆 MASTER DETECTIVE! 🏆</h1>
        <p>Final Score: {st.session_state.score} points</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🎮 Play Again"):
        st.session_state.completed_levels = set()
        st.session_state.current_level = 1
        st.session_state.score = 0
        st.rerun()
    st.stop()

# ============ CRITICAL: Only show gameplay if race is active ============
show_gameplay = False

if st.session_state.game_mode == 'solo':
    show_gameplay = True
    
elif st.session_state.game_mode == 'race':
    if st.session_state.get('race_session_id'):
        race_data = get_race_status(st.session_state.race_session_id)
        if race_data and race_data['status'] == 'racing':
            show_gameplay = True
        else:
            # Race not started - show waiting message and STOP
            st.warning("⏳ Waiting for host to start the race...")
            st.info(f"Race Code: {st.session_state.race_session_id}")
            if st.button("🔄 Refresh"):
                st.rerun()
            st.stop()  # This prevents gameplay from showing
    else:
        st.info("Join or create a race in the sidebar!")
        st.stop()
        
elif st.session_state.game_mode == 'guessing':
    game = get_guessing_game(st.session_state.guessing_session_id) if st.session_state.guessing_session_id else None
    if game and game['result_info']:
        info = game['result_info']
        st.markdown("### 🔍 Clues")
        st.write(f"Rows: {info['row_count']}")
        st.write(f"Columns: {info['columns']}")
        if info['sample']:
            st.dataframe(pd.DataFrame(info['sample']))
    else:
        st.info("Waiting for writer to lock a query...")
    st.stop()

# Show gameplay only if approved
if show_gameplay:
    current_level = st.session_state.current_level
    level = levels[current_level]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 1rem; color: white; margin-bottom: 1rem;">
        <h2>🔍 Level {current_level}: {level['name']}</h2>
        <p><strong>Mission:</strong> {level['task']}</p>
        <p><strong>Concept:</strong> {level['concept']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✍️ Write Your SQL Query")
    attempts = st.session_state.level_attempts.get(current_level, 0)
    st.caption(f"Attempts: {attempts}")
    
    query = st.text_area("Enter your SQL query:", height=100, value=level['tip'], key="sql_input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Execute Query", type="primary", use_container_width=True):
            if query:
                st.session_state.level_attempts[current_level] = attempts + 1
                result, error = execute_query(query)
                
                if error:
                    st.error(f"SQL Error: {error}")
                else:
                    st.dataframe(result, use_container_width=True)
                    
                    if current_level not in st.session_state.completed_levels:
                        is_correct, feedback = validate_level(current_level, result, query)
                        if is_correct:
                            st.session_state.score += 20
                            st.session_state.completed_levels.add(current_level)
                            
                            if st.session_state.game_mode == 'race':
                                update_race_progress(st.session_state.race_session_id, st.session_state.player_name, st.session_state.completed_levels)
                            
                            st.balloons()
                            st.success(feedback)
                            
                            if current_level < 5:
                                st.session_state.current_level += 1
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.warning(feedback)
    
    with col2:
        if st.button("💡 Get Hint", use_container_width=True):
            st.info(f"Hint: {level['hint']}")
    
    # Progress Visualization
    st.markdown("---")
    st.markdown("### 🎯 Case Files Progress")
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i-1]:
            if i in st.session_state.completed_levels:
                st.markdown(f"✅ Level {i}")
            else:
                st.markdown(f"⬜ Level {i}")
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

    