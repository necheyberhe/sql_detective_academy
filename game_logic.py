import pandas as pd
import time
import hashlib
from database import execute_query

class SQLGame:
    def __init__(self):
        self.levels = {
            1: {
                'name': 'The First Clue',
                'description': 'Learn to view all case files',
                'task': 'Show all cases from the cases table',
                'expected_query': 'SELECT * FROM cases',
                'validation': 'count_rows',
                'hint': 'Use SELECT * FROM cases to see all columns and rows',
                'concept': 'Basic SELECT statements',
                'success_message': 'Great detective! You\'ve accessed the case files.'
            },
            2: {
                'name': 'Following the Evidence',
                'description': 'Filter cases to find specific crimes',
                'task': 'Find all unsolved murder cases',
                'expected_query': "SELECT * FROM cases WHERE solved = 0 AND crime_type = 'Murder'",
                'validation': 'specific_filter',
                'hint': 'Use WHERE to filter solved = 0 and crime_type = "Murder"',
                'concept': 'WHERE clause for filtering',
                'success_message': 'Excellent! You\'ve identified the active murder cases.'
            },
            3: {
                'name': 'Prioritizing Cases',
                'description': 'Sort and limit results to focus on top priorities',
                'task': 'Find the 3 most recent high-priority cases',
                'expected_query': "SELECT * FROM cases WHERE priority = 'High' ORDER BY date_opened DESC LIMIT 3",
                'validation': 'order_limit',
                'hint': 'Use ORDER BY date_opened DESC and LIMIT 3, with WHERE priority = "High"',
                'concept': 'ORDER BY and LIMIT',
                'success_message': 'Perfect prioritization! These cases need immediate attention.'
            },
            4: {
                'name': 'Crime Statistics',
                'description': 'Analyze crime patterns with aggregation',
                'task': 'Count how many cases of each crime type exist',
                'expected_query': 'SELECT crime_type, COUNT(*) as case_count FROM cases GROUP BY crime_type',
                'validation': 'aggregation',
                'hint': 'Use GROUP BY crime_type and COUNT(*) to count cases per type',
                'concept': 'GROUP BY and aggregations',
                'success_message': 'You\'re thinking like a data analyst! These statistics reveal patterns.'
            },
            5: {
                'name': 'Connecting the Dots',
                'description': 'Combine evidence with case information',
                'task': 'List all evidence with their corresponding case names',
                'expected_query': 'SELECT e.description as evidence, c.case_name, e.evidence_type FROM evidence e JOIN cases c ON e.case_id = c.case_id',
                'validation': 'join',
                'hint': 'Use JOIN to connect evidence table with cases table using case_id',
                'concept': 'JOIN operations',
                'success_message': 'Master detective! You\'ve connected evidence to cases perfectly.'
            }
        }
        self.session_start_time = None
        self.level_start_time = None
        
    def start_time_trial(self):
        """Start a timed challenge"""
        self.session_start_time = time.time()
        self.level_start_time = time.time()
        
    def end_level_timer(self):
        """End timing for current level"""
        if self.level_start_time:
            completion_time = time.time() - self.level_start_time
            self.level_start_time = time.time()
            return completion_time
        return None
    
    def calculate_bonus_points(self, completion_time, attempts, streak):
        """Calculate bonus points based on performance"""
        base_points = 20
        
        # Time bonus (faster = more points)
        time_bonus = max(0, 10 - (completion_time / 10))
        
        # Attempt bonus (fewer attempts = more points)
        attempt_bonus = max(0, 5 - attempts)
        
        # Streak bonus
        streak_bonus = min(10, streak * 2)
        
        total_bonus = time_bonus + attempt_bonus + streak_bonus
        return base_points + int(total_bonus)
    
    def validate_query(self, user_query, level_num):
        """Validate user query against expected results"""
        level = self.levels[level_num]
        
        # Execute user query
        user_result, error = execute_query(user_query)
        if error:
            return False, self.get_friendly_error(error), user_result
        
        # Execute expected query
        expected_result, _ = execute_query(level['expected_query'])
        
        if expected_result is None:
            return False, "Expected query failed. Please contact support.", user_result
        
        # Validate based on level requirements
        if level['validation'] == 'count_rows':
            if user_result is not None and len(user_result) == len(expected_result):
                return True, level['success_message'], user_result
            else:
                return False, f"Your query returned {len(user_result) if user_result is not None else 0} rows, but we expected {len(expected_result)} rows. {level['hint']}", user_result
        
        elif level['validation'] == 'specific_filter':
            if user_result is not None and len(user_result) > 0:
                if 'solved' in user_result.columns and 'crime_type' in user_result.columns:
                    if all(user_result['solved'] == 0) and all(user_result['crime_type'] == 'Murder'):
                        return True, level['success_message'], user_result
            return False, f"Your query didn't return the correct filtered results. Make sure to filter for unsolved (solved = 0) murder cases. {level['hint']}", user_result
        
        elif level['validation'] == 'order_limit':
            if user_result is not None and len(user_result) <= 3:
                if 'date_opened' in user_result.columns:
                    dates = pd.to_datetime(user_result['date_opened'])
                    if dates.is_monotonic_decreasing:
                        return True, level['success_message'], user_result
            return False, f"Check your query: you need High priority cases, ordered by date (newest first), limited to 3 results. {level['hint']}", user_result
        
        elif level['validation'] == 'aggregation':
            if user_result is not None and 'crime_type' in user_result.columns and 'case_count' in user_result.columns:
                expected_counts = expected_result.set_index('crime_type')['case_count']
                for crime in user_result['crime_type']:
                    if crime in expected_counts.index:
                        user_count = user_result[user_result['crime_type'] == crime]['case_count'].values[0]
                        if user_count != expected_counts[crime]:
                            return False, f"Count for {crime} is incorrect. {level['hint']}", user_result
                return True, level['success_message'], user_result
            return False, f"Your query should use GROUP BY crime_type and COUNT(*). {level['hint']}", user_result
        
        elif level['validation'] == 'join':
            if user_result is not None and len(user_result) > 0:
                if 'evidence' in user_query.lower() and 'cases' in user_query.lower() and 'join' in user_query.lower():
                    return True, level['success_message'], user_result
            return False, f"Make sure to JOIN evidence with cases using the case_id. {level['hint']}", user_result
        
        return False, "Try again! Check your query carefully.", user_result
    
    def get_friendly_error(self, error):
        """Convert SQL errors to friendly hints"""
        error_lower = error.lower()
        
        if "no such column" in error_lower:
            return "🔍 Column name error! Check your spelling. Use the 'View Tables' button to see correct column names."
        elif "no such table" in error_lower:
            return "📁 Table doesn't exist! Use the 'View Tables' button to see available tables."
        elif "syntax error" in error_lower:
            return "📝 SQL syntax error! Check your spelling and punctuation. Remember keywords like SELECT, FROM, WHERE."
        elif "near" in error_lower:
            return "💡 Syntax issue! Check for missing commas, quotes, or parentheses."
        else:
            return f"❌ Error: {error}\n💡 Tip: Check your SQL syntax and column names."
    
    def get_next_hint(self, level_num, user_query):
        """Provide progressive hints based on user's query"""
        hints = {
            1: [
                "Start with: SELECT * FROM cases",
                "Remember to capitalize SQL keywords",
                "All columns are shown with *"
            ],
            2: [
                "Use WHERE to filter rows",
                "Combine conditions with AND",
                "Check: solved = 0 AND crime_type = 'Murder'"
            ],
            3: [
                "Start with WHERE priority = 'High'",
                "Add ORDER BY date_opened DESC",
                "Finish with LIMIT 3"
            ],
            4: [
                "Use GROUP BY crime_type",
                "Add COUNT(*) to count rows per group",
                "Name the count column with AS"
            ],
            5: [
                "Use JOIN to combine tables",
                "Connect evidence.case_id = cases.case_id",
                "SELECT columns from both tables"
            ]
        }
        
        if level_num in hints:
            return hints[level_num][0]
        return "Check your query structure and try again!"

class MultiplayerRace:
    """Handle multiplayer racing mode"""
    def __init__(self):
        self.sessions = {}
        
    def create_race(self, host_name):
        """Create a new race session"""
        session_id = f"RACE_{hashlib.md5(str(time.time()).encode()).hexdigest()[:4].upper()}"
        self.sessions[session_id] = {
            'host': host_name,
            'players': [host_name],
            'current_level': 1,
            'completed': {host_name: set()},
            'start_time': None,
            'status': 'waiting'
        }
        return session_id
    
    def join_race(self, session_id, player_name):
        """Join an existing race"""
        if session_id in self.sessions:
            if player_name not in self.sessions[session_id]['players']:
                self.sessions[session_id]['players'].append(player_name)
                self.sessions[session_id]['completed'][player_name] = set()
                return True
        return False
    
    def start_race(self, session_id):
        """Start the race"""
        if session_id in self.sessions:
            self.sessions[session_id]['start_time'] = time.time()
            self.sessions[session_id]['status'] = 'racing'
            return True
        return False
    
    def complete_level(self, session_id, player_name, level_num, completion_time):
        """Record level completion in race"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if player_name not in session['completed']:
                session['completed'][player_name] = set()
            session['completed'][player_name].add(level_num)
            
            if len(session['completed'][player_name]) >= 5:
                total_time = time.time() - session['start_time']
                return {
                    'finished': True,
                    'total_time': total_time,
                    'rank': self.get_race_rank(session_id, total_time)
                }
        return {'finished': False}
    
    def get_race_rank(self, session_id, player_time):
        """Get player's rank in the race"""
        if session_id in self.sessions:
            return 1
        return 1
    
    def get_race_status(self, session_id):
        """Get current race status"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                'status': session['status'],
                'players': session['players'],
                'completed': {p: len(c) for p, c in session['completed'].items()},
                'started': session['start_time'] is not None
            }
        return None