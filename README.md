#  Assignment 1-Task4 
Course: Big Data Analytics
Task: Build an interactive web application that teaches SQL concepts
Submission: Demo video + pdf report+ README with design choices and SQL concepts

Name: Nechi Berhe Weldu
ID:850164070

 # What I Built
SQL Detective Academy is a gamified web application that teaches absolute beginners how to write SQL queries. Instead of boring tutorials, users play as detectives solving crimes by writing real SQL queries against a crime database.

# How It Works
User enters a detective name (e.g., "Nechi Berhe")
User reads a case brief with a specific mission
User writes a SQL query in the editor
System executes the query against a real SQLite database
System validates the result against expected outcomes
User earns points and progresses to harder levels
The application has 5 progressive levels that teach core SQL concepts in a logical order, plus multiplayer features for competitive learning.

# Game Modes
Mode	Description
Solo Mode:	Learn at your own pace through 5 detective levels
Race Mode: Compete against a friend to solve all levels first
Query Guessing Game:	Write a secret query; others guess what it returns
# SQL Concepts Covered
Level	Concept	SQL Syntax	Real Detective Application
1	Basic SELECT	SELECT * FROM cases;	View all case files
2	Filtering with WHERE	WHERE solved = 0 AND crime_type = 'Murder'	Find active murder cases
3	Sorting and Limiting	ORDER BY date_opened DESC LIMIT 3	Prioritize most urgent cases
4	Aggregation with GROUP BY	GROUP BY crime_type, COUNT(*)	Analyze crime statistics
5	Joining Tables	JOIN evidence ON cases	Connect evidence to cases
Each level builds on the previous one, creating a natural learning progression from simple retrieval to complex multi-table queries.

# Technology Choices & Rationale
Why These Technologies?
Technology	Why I Chose It
Streamlit:Fastest way to build data apps. No front-end JavaScript required. Built-in widgets (buttons, text areas, dataframes) saved weeks of development time.
SQLite3:	Zero-configuration embedded database. No separate server needed. Perfect for educational tools where users just need to run the app.
Pandas:	Makes SQL query results display beautifully as interactive tables. Handles data validation logic cleanly.
Python:	Easy for beginners to understand if they want to modify the code. Large ecosystem of libraries.

Conclusion: Streamlit + SQLite3 was the right choice for rapid development of an interactive educational tool.

# Challenges Encountered & Solutions
Challenge 1: Real-time Race Updates
Problem: When Player 1 started the race, Player 2's screen still showed "Waiting for host..." because Streamlit sessions don't automatically communicate.

Solution: I implemented a shared SQLite database that stores race status (waiting or racing). Player 2's page auto-refreshes every 3 seconds to check the database. When it sees status='racing', it shows the game.

Challenge 2: Progress Not Updating for Both Players
Problem: When Player 1 completed Level 2, Player 2 still saw "1/5" for Player 1's progress.
Solution: I call update_race_progress() immediately after each level completion, saving to the database. Both players' pages auto-refresh every 5 seconds to fetch the latest progress.

Challenge 3: Validating User Queries
Problem: How do I check if a user's query is "correct" when there are multiple valid SQL approaches?
Solution: I validate based on results, not query text. For each level, I check:

Row count matches expected

Specific columns exist

Data values are correct (e.g., all priority='High' for Level 3)

This allows multiple correct solutions (e.g., SELECT * FROM cases vs SELECT case_id, case_name FROM cases both work for Level 1).


# What This Platform Teaches
Core SQL Skills
Reading data (SELECT) - The most common SQL operation
Filtering data (WHERE) - Finding specific information
Sorting data (ORDER BY) - Organizing results meaningfully
Limiting results (LIMIT) - Focusing on top priorities
Grouping data (GROUP BY) - Creating summaries and statistics
Joining tables (JOIN) - Connecting related information

Learning Design Principles
Principle	How It's Implemented
Progressive Difficulty	Each level adds one new concept
Immediate Feedback	Query results show instantly
Specific Hints	Not just "wrong" - tells you what to fix
Gamification	Points, badges, and competitive modes
Real Database	Not just syntax - real data interaction
# Project Structure

sql-detective-academy/
├── app.py                 # Main Streamlit application (all UI and game logic)
├── multiplayer.py         # Race mode and guessing game functions
├── ai_hints.py            # AI-powered hint generation (optional)
├── requirements.txt       # Python dependencies
├── crime_academy.db       # SQLite database (auto-generated)
└── README.md              # This file
💻 Installation & Running Locally

# Clone the repository
git clone https://github.com/yourusername/sql-detective-academy.git
cd sql-detective-academy

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
🔗 Live Demo
URL: https://sqldetectiveacademy-nb.streamlit.app/

The app is deployed on Streamlit Cloud and accessible to anyone with the link.
