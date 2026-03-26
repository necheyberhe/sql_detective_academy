import streamlit as st
import pandas as pd
import sqlite3
import time

# ============ DATABASE SETUP ============
def create_database():
    """Create and populate the database"""
    conn = sqlite3.connect('crime_academy.db')
    cursor = conn.cursor()
    
    # Create cases table
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
    
    # Create evidence table for JOIN exercises
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id INTEGER PRIMARY KEY,
        case_id INTEGER,
        description TEXT,
        evidence_type TEXT,
        collected_date DATE
    )
    ''')
    
    # Check if cases data exists
    cursor.execute("SELECT COUNT(*) FROM cases")
    if cursor.fetchone()[0] == 0:
        # Insert sample cases data
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
        
        # Insert evidence data
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
    """Execute SQL query and return results"""
    try:
        conn = sqlite3.connect('crime_academy.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

# ============ LEVELS DEFINITION ============
levels = {
    1: {
        'name': 'The First Clue',
        'description': 'Learn to view all case files',
        'task': 'Show all cases from the cases table',
        'expected_rows': 8,
        'validation': 'count_rows',
        'hint': 'Use SELECT * FROM cases to see all columns and rows',
        'concept': 'Basic SELECT statements',
        'success': 'Great detective! You\'ve accessed the case files.'
    },
    2: {
        'name': 'Following the Evidence',
        'description': 'Filter cases to find specific crimes',
        'task': 'Find all unsolved murder cases',
        'expected_crime': 'Murder',
        'expected_solved': 0,
        'validation': 'filter',
        'hint': 'Use WHERE to filter solved = 0 and crime_type = "Murder"',
        'concept': 'WHERE clause for filtering',
        'success': 'Excellent! You\'ve identified the active murder cases.'
    },
    3: {
        'name': 'Prioritizing Cases',
        'description': 'Sort and limit results to focus on top priorities',
        'task': 'Find the 3 most recent high-priority cases',
        'expected_count': 3,
        'validation': 'order_limit',
        'hint': 'Use ORDER BY date_opened DESC and LIMIT 3, with WHERE priority = "High"',
        'concept': 'ORDER BY and LIMIT',
        'success': 'Perfect prioritization! These cases need immediate attention.'
    },
    4: {
        'name': 'Crime Statistics',
        'description': 'Analyze crime patterns with aggregation',
        'task': 'Count how many cases of each crime type exist',
        'validation': 'aggregation',
        'hint': 'Use GROUP BY crime_type and COUNT(*) to count cases per type',
        'concept': 'GROUP BY and aggregations',
        'success': 'You\'re thinking like a data analyst! These statistics reveal patterns.'
    },
    5: {
        'name': 'Connecting the Dots',
        'description': 'Combine evidence with case information',
        'task': 'List all evidence with their corresponding case names',
        'validation': 'join',
        'hint': 'Use JOIN to connect evidence table with cases table using case_id',
        'concept': 'JOIN operations',
        'success': 'Master detective! You\'ve connected evidence to cases perfectly.'
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

# Initialize database
create_database()

# ============ PAGE CONFIG ============
st.set_page_config(page_title="SQL Detective Academy", page_icon="🕵️", layout="wide")

# ============ IMPROVED VALIDATION FUNCTION ============
def validate_level(level_num, result, query):
    """Validate if the query result matches level requirements"""
    level = levels[level_num]
    
    if result.empty:
        return False, "Query returned no results. Try again!"
    
    # Level 1: SELECT * FROM cases
    if level_num == 1:
        if len(result) == 8:
            return True, level['success']
        else:
            return False, f"Expected 8 cases, but got {len(result)}. {level['hint']}"
    
    # Level 2: WHERE solved = 0 AND crime_type = 'Murder'
    elif level_num == 2:
        # Check if result has the right columns
        if 'solved' in result.columns and 'crime_type' in result.columns:
            # Check if all rows are unsolved murder cases
            if len(result) > 0:
                all_unsolved = all(result['solved'] == 0)
                all_murder = all(result['crime_type'] == 'Murder')
                if all_unsolved and all_murder:
                    return True, level['success']
        return False, f"Make sure to filter for unsolved (solved = 0) murder cases. {level['hint']}"
    
    # Level 3: WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3
    elif level_num == 3:
        # Check row count
        if len(result) <= 3:
            # Check if all are high priority
            if 'priority' in result.columns and all(result['priority'] == 'High'):
                # Check if sorted by date descending
                if 'date_opened' in result.columns:
                    dates = pd.to_datetime(result['date_opened'])
                    if dates.is_monotonic_decreasing:
                        return True, level['success']
        return False, f"Need High priority cases, ordered by date (newest first), limited to 3. {level['hint']}"
    
    # Level 4: GROUP BY with aggregation
    elif level_num == 4:
        # Check if query uses GROUP BY and has count column
        if 'crime_type' in result.columns:
            # Check if there's a count column (could be named count, case_count, etc)
            count_cols = [col for col in result.columns if 'count' in col.lower() or col == 'COUNT(*)']
            if count_cols:
                return True, level['success']
        return False, f"Use GROUP BY crime_type and COUNT(*) to count cases per type. {level['hint']}"
    
    # Level 5: JOIN operation
    elif level_num == 5:
        # Check if result has evidence and case name
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
    st.markdown("### 📚 Database Preview")
    try:
        conn = sqlite3.connect('crime_academy.db')
        preview = pd.read_sql_query("SELECT * FROM cases LIMIT 3", conn)
        st.dataframe(preview, use_container_width=True)
        st.caption("Cases table (first 3 rows)")
        conn.close()
    except:
        pass

# ============ MAIN CONTENT ============
st.title("🕵️ SQL Detective Academy")

# Check if all levels are completed
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
    
    st.markdown("### 🏅 Badges Earned:")
    st.success("🔰 Rookie Detective")
    st.success("⭐ Junior Detective")
    st.success("🏅 Master Detective")
    
    if st.button("🎮 Play Again", type="primary", use_container_width=True):
        st.session_state.completed_levels = set()
        st.session_state.current_level = 1
        st.session_state.score = 0
        st.session_state.level_attempts = {}
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Case Files Progress")
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i-1]:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="background-color: #28a745; border-radius: 50%; width: 60px; height: 60px; 
                            margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 28px;">✓</span>
                </div>
                <p><strong>Level {i}</strong><br>✅ Completed</p>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ============ CURRENT LEVEL DISPLAY ============
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

# ============ SQL INPUT AREA ============
st.markdown("### ✍️ Write Your SQL Query")

attempts = st.session_state.level_attempts.get(current_level, 0)
st.caption(f"Attempts: {attempts}")

default_queries = {
    1: "SELECT * FROM cases;",
    2: "SELECT * FROM cases WHERE solved = 0 AND crime_type = 'Murder';",
    3: "SELECT * FROM cases WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3;",
    4: "SELECT crime_type, COUNT(*) as case_count FROM cases GROUP BY crime_type;",
    5: "SELECT e.description as evidence, c.case_name FROM evidence e JOIN cases c ON e.case_id = c.case_id;"
}

query = st.text_area(
    "Enter your SQL query:",
    height=100,
    value=default_queries.get(current_level, ""),
    key="sql_input"
)

# ============ BUTTONS ============
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
                        
                        # Check if level not completed yet
                        if current_level not in st.session_state.completed_levels:
                            is_correct, feedback = validate_level(current_level, result, query)
                            
                            if is_correct:
                                # Add points
                                st.session_state.score += 20
                                st.session_state.completed_levels.add(current_level)
                                st.balloons()
                                st.success(f"🎉 {feedback} +20 points!")
                                
                                # Auto-advance to next level
                                if current_level < 5:
                                    st.session_state.current_level += 1
                                    st.info(f"Moving to Level {st.session_state.current_level}...")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    # All levels complete
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
        st.info(f"💡 Hint: {level['hint']}")

with col3:
    if st.button("🔄 Reset Level", use_container_width=True):
        if current_level in st.session_state.completed_levels:
            st.session_state.completed_levels.remove(current_level)
            st.session_state.score = max(0, st.session_state.score - 20)
        st.success(f"Level {current_level} reset! Try again.")
        time.sleep(1)
        st.rerun()

# ============ PROGRESS VISUALIZATION ============
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

# ============ DYNAMIC FOOTER ============
st.markdown("---")

# Dynamic footer based on current level
current_level = st.session_state.current_level
completed_count = len(st.session_state.completed_levels)

if completed_count == 5:
    footer_text = """
    <div style="text-align: center; color: #666;">
        <p>🏆 MASTER DETECTIVE! You've mastered all SQL concepts! 🏆</p>
        <p>🎉 Congratulations on completing SQL Detective Academy! 🎉</p>
        <p>💡 Click "Play Again" to test your skills once more!</p>
    </div>
    """
else:
    level_tips = {
        1: {
            'tip': '💡 Type: <code>SELECT * FROM cases;</code> and click Execute to view all case files!',
            'concept': 'SELECT retrieves all columns and rows from a table'
        },
        2: {
            'tip': '💡 Type: <code>SELECT * FROM cases WHERE solved = 0 AND crime_type = \'Murder\';</code>',
            'concept': 'WHERE filters rows based on conditions. Use AND to combine multiple filters!'
        },
        3: {
            'tip': '💡 Type: <code>SELECT * FROM cases WHERE priority = \'High\' ORDER BY date_opened DESC LIMIT 3;</code>',
            'concept': 'ORDER BY sorts results, LIMIT restricts number of rows returned!'
        },
        4: {
            'tip': '💡 Type: <code>SELECT crime_type, COUNT(*) as case_count FROM cases GROUP BY crime_type;</code>',
            'concept': 'GROUP BY groups rows, COUNT(*) counts items in each group!'
        },
        5: {
            'tip': '💡 Type: <code>SELECT e.description as evidence, c.case_name FROM evidence e JOIN cases c ON e.case_id = c.case_id;</code>',
            'concept': 'JOIN combines tables based on related columns (case_id)!'
        }
    }
    
    tip = level_tips.get(current_level, level_tips[1])
    
    footer_text = f"""
    <div style="text-align: center; color: #666;">
        <p>🕵️ SQL Detective Academy - Learn SQL by solving crimes!</p>
        <p><strong>Level {current_level} Tip:</strong> {tip['concept']}</p>
        <p>{tip['tip']}</p>
        <p>🏆 Complete all 5 levels to become a Master Detective! | Current: {completed_count}/5</p>
    </div>
    """

st.markdown(footer_text, unsafe_allow_html=True)