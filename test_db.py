import sqlite3
import pandas as pd

def test_database():
    try:
        # Try to connect and query
        conn = sqlite3.connect('crime_academy.db')
        cursor = conn.cursor()
        
        # Check if cases table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Database exists!")
            # Query the data
            df = pd.read_sql_query("SELECT * FROM cases", conn)
            print(f"✅ Found {len(df)} cases:")
            print(df.head())
        else:
            print("❌ Database not created properly")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_database()