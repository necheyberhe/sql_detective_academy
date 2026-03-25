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
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
    }
    .hint-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ffc107;
    }
    .level-complete {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
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
        st.session_state.player_name = st.text_input("Enter your detective name:", 
                                                      placeholder="Sherlock Holmes")
    
    if st.session_state.player_name:
        st.success(f"Welcome, {st.session_state.player_name}!")
    
    st.markdown("---")
    
    # Competitive mode selection
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
            st.success("Time Trial Started! Complete all levels as fast as possible!")
            st.rerun()
    
    elif mode == "👥 Multiplayer Race":
        st.session_state.race_mode = True
        st.session_state.competitive_mode = True
        st.session_state.time_trial_mode = False
        
        race_action = st.radio("", ["🏁 Create Race", "🔗 Join Race"])
        
        if race_action == "🏁 Create Race":
            if st.button("Create New Race", type="primary"):
                session_id = multiplayer.create_race(st.session_state.player_name)
                st.session_state.race_session = session_id
                st.success(f"Race created! Code: **{session_id}**")
                st.info("Share this code with friends to join!")
                
                if st.button("Start Race"):
                    multiplayer.start_race(session_id)
                    game.start_time_trial()
                    st.rerun()
        
        else:
            session_code = st.text_input("Enter Race Code:")
            if st.button("Join Race") and session_code:
                if multiplayer.join_race(session_code, st.session_state.player_name):
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
                if status['started']:
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
        st.markdown(f'<div class="timer">{elapsed:.1f}s</div>', unsafe_allow_html=True)
    
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
            st.write(f"Columns: {', '.join(info['columns'][:5])}...")
            st.caption(f"{info['row_count']} rows")
            if st.button(f"Preview", key=f"preview_{table_name}"):
                st.dataframe(info['sample'])

# Main content
st.title("🕵️ SQL Detective Academy")

# Mode indicator
if st.session_state.time_trial_mode:
    st.info("⏱️ **TIME TRIAL MODE ACTIVE** - Complete levels as fast as possible for bonus points!")
elif st.session_state.race_mode:
    st.info("🏁 **RACE MODE ACTIVE** - Compete against other detectives!")

# Current level display
level = game.levels[st.session_state.current_level]

st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 1rem; color: white; margin: 1rem 0;">
    <h2>🔍 Level {st.session_state.current_level}: {level['name']}</h2>
    <p><strong>Case Brief:</strong> {level['description']}</p>
    <p><strong>Your Mission:</strong> {level['task']}</p>
    <p><strong>SQL Concept:</strong> {level['concept']}</p>
    {f'<p><strong>⏱️ Time Bonus:</strong> Faster completion = more points!</p>' if st.session_state.time_trial_mode else ''}
</div>
""", unsafe_allow_html=True)

# SQL editor
col_left, col_right = st.columns([3, 1])

with col_left:
    st.subheader("✍️ Write Your SQL Query")
    
    attempts = st.session_state.level_attempts.get(st.session_state.current_level, 0)
    st.caption(f"Attempts: {attempts}")
    
    query = st.text_area(
        "Enter your SQL query below:",
        height=150,
        placeholder="Example: SELECT * FROM cases;",
        key="sql_editor",
        label_visibility="collapsed"
    )
    
    col_buttons = st.columns(4)
    with col_buttons[0]:
        execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)
    with col_buttons[1]:
        if st.button("💡 Get Hint", use_container_width=True):
            hint = game.get_next_hint(st.session_state.current_level, query)
            st.info(hint)
    with col_buttons[2]:
        if st.button("🔄 Reset Level", use_container_width=True):
            if st.session_state.current_level in st.session_state.completed_levels:
                st.session_state.completed_levels.remove(st.session_state.current_level)
            st.session_state.current_streak = 0
            st.session_state.score = max(0, st.session_state.score - 10)
            st.success("Level reset!")
            st.rerun()
    with col_buttons[3]:
        if st.session_state.time_trial_mode and st.button("⏱️ Best Times", use_container_width=True):
            if st.session_state.level_completion_times:
                st.write("**Your Best Times:**")
                for lvl, t in st.session_state.level_completion_times.items():
                    st.write(f"Level {lvl}: {t:.1f}s")

with col_right:
    st.subheader("📖 SQL Reference")
    with st.expander("Basic Commands"):
        st.markdown("""
        - **SELECT** - Choose columns
        - **FROM** - Specify table
        - **WHERE** - Filter rows
        - **ORDER BY** - Sort results
        - **LIMIT** - Limit rows
        - **GROUP BY** - Group rows
        - **JOIN** - Combine tables
        """)

# Execute query
if execute_button and query:
    attempts = st.session_state.level_attempts.get(st.session_state.current_level, 0) + 1
    st.session_state.level_attempts[st.session_state.current_level] = attempts
    
    with st.spinner("Executing query..."):
        result, error = execute_query(query)
        
        if error:
            st.error(error)
        else:
            st.session_state.query_history.append({
                'query': query,
                'timestamp': time.time(),
                'level': st.session_state.current_level,
                'attempts': attempts
            })
            
            st.subheader("📊 Query Results")
            if not result.empty:
                st.dataframe(result, use_container_width=True)
                st.caption(f"Returned {len(result)} rows")
            else:
                st.info("Query executed successfully but returned no results.")
            
            if st.session_state.current_level not in st.session_state.completed_levels:
                is_correct, feedback, validated_result = game.validate_query(query, st.session_state.current_level)
                
                if is_correct:
                    completion_time = game.end_level_timer() if st.session_state.time_trial_mode else None
                    
                    if st.session_state.time_trial_mode and completion_time:
                        bonus_points = game.calculate_bonus_points(
                            completion_time, attempts, st.session_state.current_streak
                        )
                        st.session_state.score += bonus_points
                        
                        if st.session_state.current_level not in st.session_state.level_completion_times:
                            st.session_state.level_completion_times[st.session_state.current_level] = completion_time
                        else:
                            st.session_state.level_completion_times[st.session_state.current_level] = min(
                                st.session_state.level_completion_times[st.session_state.current_level],
                                completion_time
                            )
                        
                        feedback = f"{feedback} 🎯 Time: {completion_time:.1f}s | Bonus: +{bonus_points - 20}!"
                    else:
                        st.session_state.score += 20
                    
                    st.session_state.current_streak += 1
                    st.session_state.completed_levels.add(st.session_state.current_level)
                    
                    if st.session_state.player_name:
                        save_score_to_leaderboard(
                            st.session_state.player_name,
                            st.session_state.score,
                            st.session_state.current_level,
                            completion_time or 0,
                            attempts
                        )
                    
                    if st.session_state.race_mode and st.session_state.race_session:
                        race_result = multiplayer.complete_level(
                            st.session_state.race_session,
                            st.session_state.player_name,
                            st.session_state.current_level,
                            completion_time or 0
                        )
                        if race_result['finished']:
                            st.success(f"🏆 RACE FINISHED! You placed #{race_result['rank']}!")
                            st.balloons()
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>🎉 Case Solved!</h3>
                        <p>{feedback}</p>
                        <p>✨ Score: {st.session_state.score} | 🔥 Streak: {st.session_state.current_streak}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.session_state.current_level < 5:
                        st.session_state.current_level += 1
                        st.balloons()
                        st.success("🎉 Level Complete! Moving to next challenge...")
                        time.sleep(2)
                        st.rerun()
                    else:
                        total_time = time.time() - game.session_start_time if st.session_state.time_trial_mode else None
                        st.markdown(f"""
                        <div class="success-box">
                            <h2>🏆 CONGRATULATIONS, MASTER DETECTIVE!</h2>
                            <p>Final Score: {st.session_state.score} points</p>
                            {f'<p>Total Time: {total_time:.1f} seconds</p>' if total_time else ''}
                            <p>Final Streak: {st.session_state.current_streak}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                else:
                    if st.session_state.current_streak > 0:
                        st.session_state.current_streak = 0
                        st.warning("💔 Streak broken! Try again to rebuild it.")
                    
                    st.markdown(f"""
                    <div class="hint-box">
                        <h3>⚠️ Not Quite Right</h3>
                        <p>{feedback}</p>
                        <p>💡 Attempts: {attempts}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if attempts > 2:
                        st.info("💡 Check the 'Database Explorer' to see table structures!")
                    if attempts > 4:
                        with st.expander("🔍 Show Expected Query"):
                            st.code(level['expected_query'], language='sql')
            else:
                st.info("✅ Level already completed! Move to next level or replay for practice.")

# Level progress visualization
st.markdown("---")
st.subheader("🎯 Case Files Progress")

cols = st.columns(5)
for i in range(1, 6):
    with cols[i-1]:
        if i in st.session_state.completed_levels:
            time_taken = st.session_state.level_completion_times.get(i, None)
            time_text = f"⏱️ {time_taken:.1f}s" if time_taken else ""
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="background-color: #28a745; border-radius: 50%; width: 50px; height: 50px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 24px;">✓</span>
                </div>
                <p><strong>Level {i}</strong><br>{time_text}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="background-color: #6c757d; border-radius: 50%; width: 50px; height: 50px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 24px;">{i}</span>
                </div>
                <p><strong>Level {i}</strong></p>
            </div>
            """, unsafe_allow_html=True)

# Competitive statistics
if st.session_state.competitive_mode and st.session_state.level_completion_times:
    st.markdown("---")
    st.subheader("📊 Performance Stats")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_time = sum(st.session_state.level_completion_times.values())
        st.metric("Total Time", f"{total_time:.1f}s")
    with col2:
        total_attempts = sum(st.session_state.level_attempts.values())
        st.metric("Total Attempts", total_attempts)
    with col3:
        avg_time = total_time / len(st.session_state.level_completion_times)
        st.metric("Avg Level Time", f"{avg_time:.1f}s")

# Query history
with st.expander("📜 Query History"):
    if st.session_state.query_history:
        for q in reversed(st.session_state.query_history[-5:]):
            st.code(q['query'], language='sql')
            st.caption(f"Level {q['level']} - Attempt {q['attempts']}")
            st.markdown("---")
    else:
        st.info("No queries executed yet.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🕵️ SQL Detective Academy - Learn SQL by solving crimes!</p>
    <p>🏆 Compete on leaderboard | ⏱️ Beat your best times | 👥 Race against friends</p>
</div>
""", unsafe_allow_html=True)