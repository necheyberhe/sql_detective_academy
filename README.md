# 🕵️ SQL Detective Academy

An interactive, gamified web application that teaches SQL fundamentals through detective-themed challenges and competitive multiplayer modes.

---

## 🎮 Live Demo

[Play SQL Detective Academy](https://your-streamlit-app-url.streamlit.app) *(Replace with your deployed URL)*

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [SQL Concepts Taught](#sql-concepts-taught)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [How to Play](#how-to-play)
- [Game Modes](#game-modes)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Assignment Compliance](#assignment-compliance)

---

## 🎯 Overview

SQL Detective Academy transforms SQL learning into an exciting detective adventure. Players solve crimes by writing real SQL queries against a preloaded crime database. The game features 5 progressive levels, multiple game modes, and a detective theme that makes learning engaging and memorable.

**Target Audience:** Absolute beginners who have never written a SQL query before.

---

## ✨ Features

### Core Platform (Task 4.1)

| Feature | Description |
|---------|-------------|
| ✅ **Real SQLite Database** | Preloaded with crime cases and evidence data |
| ✅ **Interactive SQL Editor** | Write and execute real SQL queries |
| ✅ **5 Progressive Levels** | SELECT → WHERE → ORDER BY/LIMIT → GROUP BY → JOIN |
| ✅ **Smart Validation** | Checks query results against expected outcomes |
| ✅ **Helpful Feedback** | Specific hints, not just "incorrect" |
| ✅ **Progress Tracking** | Visual progress bar, badges, and score system |

### Creative Features (Task 4.2)

| Feature | Description |
|---------|-------------|
| 🏆 **Detective Theme** | Solve crimes, collect evidence, catch criminals |
| 🏁 **Multiplayer Race Mode** | Compete against friends to solve all 5 levels first |
| 🎭 **Query Guessing Game** | One player writes a query, another guesses what it returns |
| 🎖️ **Badge System** | Earn ranks: Rookie → Junior → Master Detective |
| 💡 **Smart Hints** | Context-aware hints based on your mistakes |

---

## 📚 SQL Concepts Taught

| Level | Concept | Learning Objective |
|-------|---------|-------------------|
| 1 | `SELECT *` | Retrieve all data from a table |
| 2 | `WHERE` with `AND` | Filter rows based on conditions |
| 3 | `ORDER BY` + `LIMIT` | Sort results and limit rows |
| 4 | `GROUP BY` + `COUNT(*)` | Aggregate data and create summaries |
| 5 | `JOIN` (INNER JOIN) | Combine data from multiple tables |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.9+** | Core programming language |
| **Streamlit** | Web app framework and UI |
| **SQLite3** | Embedded database |
| **Pandas** | Query result handling and data manipulation |
| **SQL** | Query language for challenges |

---

## 💻 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/sql-detective-academy.git
cd sql-detective-academy

### Step 2: Install Dependencies
pip install -r requirements.txt
pip install streamlit pandas
### Step 3: Run the Application
streamlit run app.py
### How to Play
Getting Started
Enter your detective name (e.g., "Sherlock Holmes")

Choose a game mode from the sidebar

Read the case brief and mission objective

Write a SQL query in the editor

Click Execute to run your query

Get feedback and try again if needed

Earn points and badges as you progress
### Level Progression
Level 1: The First Clue
├── Task: Show all cases
├── SQL: SELECT * FROM cases;
└── Success: Access all case files

Level 2: Following the Evidence
├── Task: Find unsolved murder cases
├── SQL: WHERE solved = 0 AND crime_type = 'Murder'
└── Success: Identify active murder cases

Level 3: Prioritizing Cases
├── Task: Find 3 most recent high-priority cases
├── SQL: ORDER BY date_opened DESC LIMIT 3
└── Success: Focus on urgent cases

Level 4: Crime Statistics
├── Task: Count cases by crime type
├── SQL: GROUP BY crime_type, COUNT(*)
└── Success: Reveal crime patterns

Level 5: Connecting the Dots
├── Task: List evidence with case names
├── SQL: JOIN evidence ON cases
└── Success: Master Detective!

### Game Modes
🎯 Solo Mode
Learn at your own pace. Complete all 5 levels, earn points, and unlock badges. Perfect for beginners.

🏁 Race Mode
Compete against another player in real-time:

Create a Race - Get a unique race code

Share the code with your opponent

Race to complete all 5 levels

First to finish wins!

🎭 Query Guessing Game
Test your SQL understanding:

Writer Mode: Write a secret SQL query

Guesser Mode: See row count, columns, and sample data
📁 Project Structure

sql-detective-academy/
├── app.py                 # Main Streamlit application
├── multiplayer.py         # Multiplayer race & guessing game logic
├── requirements.txt       # Python dependencies
├── crime_academy.db       # SQLite database (auto-generated on first run)
└── README.md             # This file