import streamlit as st
import pandas as pd
import time
from database import (create_database, execute_query, get_table_info, 
                      save_score_to_leaderboard, get_leaderboard, get_player_rank)
from game_logic import SQLGame

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
    .result-table {
        margin-top: 1rem;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        overflow: auto;
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
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'player_name' not in st.session_state:
        st.session_state.player_name = ""
    if 'time_trial_mode' not in st.session_state:
        st.session_state.time_trial_mode = False
    if 'level_attempts' not in st.session_state:
        st.session_state.level_attempts = {}
    if 'level_completion_times' not in st.session_state:
        st.session_state.level_completion_times = {}
    if 'current_streak' not in st.session_state:
        st.session_state.current_streak = 0

# Initialize
create_database()
game = SQLGame()
init_session_state()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995571.png", width=80)
    st.title("🕵️ SQL Academy")
    
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
    st.subheader("🏆 Game Mode")
    mode = st.radio(
        "Choose your mode:",
        ["🎯 Solo Mode", "⏱️ Time Trial"],
        label_visibility="collapsed"
    )
    
    if mode == "⏱️ Time Trial":
        st.session_state.time_trial_mode = True
        if st.button("⏱️ Start Time Trial", type="primary"):
            game.start_time_trial()
            st.session_state.score = 0
            st.session_state.completed_levels = set()
            st.session_state.current_level = 1
            st.session_state.level_attempts = {}
            st.session_state.level_completion_times = {}
            st.success("Time Trial Started! Complete all levels as fast as possible!")
            st.rerun()
    else:
        st.session_state.time_trial_mode = False
    
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
    value="SELECT * FROM cases;",  # Default value for testing
    placeholder="Example: SELECT * FROM cases;",
    key="sql_editor",
    label_visibility="collapsed"
)

# Buttons row
col1, col2, col3 = st.columns(3)

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

# SQL Reference
with st.expander("📖 SQL Reference - Click to expand"):
    st.markdown("""
    ### Basic SQL Commands
    
    **SELECT** - Retrieve data from a table
    ```sql
    SELECT * FROM cases;  -- Select all columns
    SELECT case_name, crime_type FROM cases;  -- Select specific columns
    SELECT * FROM cases WHERE solved = 0;
    SELECT * FROM cases WHERE priority = 'High' AND crime_type = 'Murder';
    SELECT * FROM cases ORDER BY date_opened DESC;
    SELECT * FROM cases ORDER BY priority ASC; 
    SELECT * FROM cases LIMIT 3;
    SELECT crime_type, COUNT(*) FROM cases GROUP BY crime_type;
     SELECT * FROM evidence JOIN cases ON evidence.case_id = cases.case_id;
                """)                                                          