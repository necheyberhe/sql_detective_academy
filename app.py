import streamlit as st
import pandas as pd
import time
from database import (create_database, execute_query, get_table_info, 
                      save_score_to_leaderboard, get_leaderboard, get_player_rank,
                      create_multiplayer_session, join_multiplayer_session, get_multiplayer_session)
from game_logic import SQLGame, MultiplayerRace

# Page configuration
st.set_page_config(
    page_title="SQL Detective Academy",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #1e3c72;
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #2c4e8a;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .hint-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .level-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin: 1rem 0;
    }
    .leaderboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.75rem;
        border-radius: 0.5rem;
        color: white;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); }
    .rank-2 { background: linear-gradient(135deg, #C0C0C0, #808080); }
    .rank-3 { background: linear-gradient(135deg, #CD7F32, #8B4513); }
    .timer {
        font-family: monospace;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        background: #000;
        color: #0f0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .streak-badge {
        background: #ff4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .progress-circle {
        text-align: center;
        padding: 0.5rem;
    }
    .level-number {
        background-color: #6c757d;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 18px;
    }
    .level-completed {
        background-color: #28a745;
    }
    .sql-editor textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'completed_levels' not in st.session_state:
        st.session_state.completed_levels = set()
    if 'current_level' not in st.session_state:
        st.session_state.current_level = 1
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'hints_used' not in st.session_state:
        st.session_state.hints_used = 0
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'player_name' not in st.session_state:
        st.session_state.player_name = ""
    if 'competitive_mode' not in st.session_state:
        st.session_state.competitive_mode = False
    if 'time_trial_mode' not in st.session_state:
        st.session_state.time_trial_mode = False
    if 'level_attempts' not in st.session_state:
        st.session_state.level_attempts = {}
    if 'level_completion_times' not in st.session_state:
        st.session_state.level_completion_times = {}
    if 'current_streak' not in st.session_state:
        st.session_state.current_streak = 0
    if 'race_mode' not in st.session_state:
        st.session_state.race_mode = False
    if 'multiplayer_session' not in st.session_state:
        st.session_state.multiplayer_session = None
    if 'race_session' not in st.session_state:
        st.session_state.race_session = None

# Initialize
create_database()
game = SQLGame()
multiplayer = MultiplayerRace()
init_session_state()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995571.png", width=80)
    st.title("🕵️ SQL Academy")
    
    # Player name input
    if not st.session_state.player_name:
        player_name_input = st.text_input("Enter your detective name:", 
                                           placeholder="Sherlock Holmes")
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
    st.subheader("🏆 Game Mode")
    mode = st.radio(
        "Choose your mode:",
        ["🎯 Solo Mode", "⏱️ Time Trial", "👥 Multiplayer Race"],
        label_visibility="collapsed"
    )
    
    if mode == "⏱️ Time Trial":
        st.session_state.time_trial_mode = True
        st.session_state.competitive_mode = True
        st.session_state.race_mode = False
        if st.button("⏱️ Start Time Trial", type="primary"):
            game.start_time_trial()
            st.session_state.score = 0
            st.session_state.completed_levels = set()
            st.session_state.current_level = 1
            st.session_state.level_attempts = {}
            st.session_state.level_completion_times = {}
            st.success("Time Trial Started! Complete all levels as fast as possible!")
            st.rerun()
    
    elif mode == "👥 Multiplayer Race":
        st.session_state.race_mode = True
        st.session_state.competitive_mode = True
        st.session_state.time_trial_mode = False
        
        race_action = st.radio("", ["🏁 Create Race", "🔗 Join Race"])
        
        if race_action == "🏁 Create Race":
            if st.button("Create New Race", type="primary"):
                session_id = multiplayer.create_race(st.session_state.player_name or "Detective")
                st.session_state.race_session = session_id
                st.success(f"Race created! Code: **{session_id}**")
                st.info("Share this code with friends to join!")
                
                if st.button("Start Race"):
                    multiplayer.start_race(session_id)
                    game.start_time_trial()
                    st.session_state.score = 0
                    st.session_state.completed_levels = set()
                    st.session_state.current_level = 1
                    st.rerun()
        
        else:
            session_code = st.text_input("Enter Race Code:")
            if st.button("Join Race") and session_code:
                if multiplayer.join_race(session_code, st.session_state.player_name or "Detective"):
                    st.session_state.race_session = session_code
                    st.success("Joined race! Waiting for host to start...")
                else:
                    st.error("Race not found!")
        
        # Show race status
        if st.session_state.race_session:
            status = multiplayer.get_race_status(st.session_state.race_session)
            if status:
                st.write("**Race Status:**")
                for player, completed in status['completed'].items():
                    st.write(f"{player}: {completed}/5 levels")
                if status.get('started', False):
                    st.info("🏁 Race in progress!")
    
    else:
        st.session_state.time_trial_mode = False
        st.session_state.competitive_mode = False
        st.session_state.race_mode = False
    
    st.markdown("---")
    
    # Progress tracking
    st.subheader("📊 Your Progress")
    progress = len(st.session_state.completed_levels) / 5
    st.progress(progress)
    st.write(f"**Score:** {st.session_state.score} points")
    st.write(f"**Levels:** {len(st.session_state.completed_levels)}/5")
    
    if st.session_state.current_streak > 0:
        st.markdown(f'<div class="streak-badge">🔥 {st.session_state.current_streak} Level Streak!</div>', 
                   unsafe_allow_html=True)
    
    # Timer display for time trial
    if st.session_state.time_trial_mode and game.session_start_time:
        elapsed = time.time() - game.session_start_time
        st.markdown(f'<div class="timer">⏱️ {elapsed:.1f}s</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Badges
    st.subheader("🏆 Badges")
    if len(st.session_state.completed_levels) >= 1:
        st.success("🔰 Rookie Detective")
    if len(st.session_state.completed_levels) >= 3:
        st.success("⭐ Junior Detective")
    if len(st.session_state.completed_levels) >= 5:
        st.success("🏅 Master Detective")
    
    # Leaderboard
    st.markdown("---")
    st.subheader("🏆 Global Leaderboard")
    
    leaderboard = get_leaderboard(5)
    if not leaderboard.empty:
        for idx, row in leaderboard.iterrows():
            rank_style = ""
            if idx == 0:
                rank_style = "rank-1"
            elif idx == 1:
                rank_style = "rank-2"
            elif idx == 2:
                rank_style = "rank-3"
            
            st.markdown(f"""
            <div class="leaderboard-card {rank_style}">
                <strong>#{idx+1}</strong> {row['player_name']}<br>
                🎯 {row['total_score']} pts | ⭐ {row['completed_levels']} | 🔥 {row['streak_count']}
            </div>
            """, unsafe_allow_html=True)
    
    if st.session_state.player_name:
        rank = get_player_rank(st.session_state.player_name)
        if rank:
            st.write(f"**Your Rank:** #{rank}")
    
    st.markdown("---")
    
    # Database explorer
    with st.expander("📊 Database Explorer"):
        table_info = get_table_info()
        for table_name, info in table_info.items():
            st.write(f"**{table_name.upper()}**")
            st.write(f"Columns: {', '.join(info['columns'][:5])}")
            if len(info['columns']) > 5:
                st.write(f"... and {len(info['columns']) - 5} more")
            st.caption(f"{info['row_count']} rows")
            if st.button(f"Preview {table_name}", key=f"preview_{table_name}"):
                st.dataframe(info['sample'], use_container_width=True)

# Main content area
st.title("🕵️ SQL Detective Academy")

# Mode indicator
if st.session_state.time_trial_mode:
    st.info("⏱️ **TIME TRIAL MODE ACTIVE** - Complete levels as fast as possible for bonus points!")
elif st.session_state.race_mode:
    st.info("🏁 **RACE MODE ACTIVE** - Compete against other detectives!")

# Current level display
level = game.levels[st.session_state.current_level]

st.markdown(f"""
<div class="level-card">
    <h2>🔍 Level {st.session_state.current_level}: {level['name']}</h2>
    <p><strong>Case Brief:</strong> {level['description']}</p>
    <p><strong>Your Mission:</strong> {level['task']}</p>
    <p><strong>SQL Concept:</strong> {level['concept']}</p>
    {f'<p><strong>⏱️ Time Bonus:</strong> Faster completion = more points!</p>' if st.session_state.time_trial_mode else ''}
</div>
""", unsafe_allow_html=True)

# SQL editor area
st.subheader("✍️ Write Your SQL Query")

attempts = st.session_state.level_attempts.get(st.session_state.current_level, 0)
st.caption(f"Attempts: {attempts}")

query = st.text_area(
    "Enter your SQL query below:",
    height=120,
    placeholder="Example: SELECT * FROM cases;",
    key="sql_editor",
    label_visibility="collapsed"
)

# Buttons row
col1, col2, col3, col4 = st.columns(4)

with col1:
    execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)

with col2:
    if st.button("💡 Get Hint", use_container_width=True):
        hint = game.get_next_hint(st.session_state.current_level, query)
        st.info(hint)

with col3:
    if st.button("🔄 Reset Level", use_container_width=True):
        if st.session_state.current_level in st.session_state.completed_levels:
            st.session_state.completed_levels.remove(st.session_state.current_level)
        st.session_state.current_streak = 0
        st.session_state.score = max(0, st.session_state.score - 10)
        st.success("Level reset!")
        st.rerun()

with col4:
    if st.session_state.time_trial_mode and st.session_state.level_completion_times:
        if st.button("⏱️ Best Times", use_container_width=True):
            times_text = "**Your Best Times:**\n"
            for lvl, t in st.session_state.level_completion_times.items():
                times_text += f"Level {lvl}: {t:.1f}s\n"
            st.info(times_text)
