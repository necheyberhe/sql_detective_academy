"""
AI-Powered Hints Module for SQL Detective Academy
Uses OpenAI GPT to generate personalized hints for incorrect SQL queries
"""

import openai
import os
from typing import Optional, Dict, Any

class AIHintGenerator:
    """Generate personalized hints using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI hint generator"""
        if api_key:
            openai.api_key = api_key
        else:
            # Try to get from environment variable
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
        
        self.enabled = bool(openai.api_key)
    
    def generate_hint(self, 
                      user_query: str, 
                      level_num: int, 
                      level_info: Dict[str, Any],
                      error: Optional[str] = None,
                      result_info: Optional[Dict] = None) -> str:
        """
        Generate a personalized hint for the user's incorrect query
        
        Args:
            user_query: The user's SQL query
            level_num: Current level number
            level_info: Dictionary with level details
            error: SQL error message if any
            result_info: Info about the query results (rows returned, etc.)
        
        Returns:
            Personalized hint string
        """
        
        if not self.enabled:
            return self._fallback_hint(level_num, user_query, error)
        
        # Build context for the AI
        context = self._build_context(user_query, level_num, level_info, error, result_info)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a friendly SQL tutor helping a detective student learn SQL through a crime-solving game. 
                        Your hints should be:
                        1. Encouraging and supportive
                        2. Specific to the user's mistake
                        3. Detective-themed (use words like "clue", "evidence", "case", etc.)
                        4. Educational - explain the concept briefly
                        5. Short and actionable (2-3 sentences maximum)
                        
                        Never give the full answer directly. Guide them to discover it themselves."""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=150,
                temperature=0.7,
                presence_penalty=0.5,
                frequency_penalty=0.3
            )
            
            hint = response.choices[0].message.content.strip()
            return f"🤖 AI Detective Suggests: {hint}"
            
        except Exception as e:
            print(f"AI hint generation failed: {e}")
            return self._fallback_hint(level_num, user_query, error)
    
    def _build_context(self, user_query: str, level_num: int, 
                       level_info: Dict, error: Optional[str],
                       result_info: Optional[Dict]) -> str:
        """Build the context string for the AI"""
        
        context = f"""
        Student is learning SQL through a detective game.
        
        Level {level_num}: {level_info['name']}
        Mission: {level_info['task']}
        SQL Concept: {level_info['concept']}
        
        Student's Query:
        {user_query}
        
        """
        
        if error:
            context += f"""
            Error Message:
            {error}
            
            This is a syntax or database error. Help them fix it.
            """
        elif result_info:
            context += f"""
            Query executed but results are incorrect.
            Expected: {result_info.get('expected', 'specific results')}
            Got: {result_info.get('actual', 'different results')}
            
            The query runs but doesn't solve the case correctly.
            """
        else:
            context += """
            The query executed but didn't produce the correct results for solving the case.
            """
        
        context += """
        
        Provide a helpful, detective-themed hint to guide them toward the correct solution.
        """
        
        return context
    
    def _fallback_hint(self, level_num: int, user_query: str, error: Optional[str] = None) -> str:
        """Provide fallback hints when AI is unavailable"""
        
        level_hints = {
            1: "🔍 Start with: SELECT * FROM cases to see all case files.",
            2: "🔍 Use WHERE to filter: solved = 0 AND crime_type = 'Murder'",
            3: "🔍 Filter High priority, then ORDER BY date_opened DESC, then LIMIT 3",
            4: "🔍 Use GROUP BY crime_type and COUNT(*) to count cases",
            5: "🔍 Use JOIN to connect evidence and cases tables with case_id"
        }
        
        if error:
            if "no such column" in error.lower():
                return "🔍 Column name error! Check the 'Database Explorer' in sidebar for correct column names."
            elif "no such table" in error.lower():
                return "📁 Table doesn't exist! Available tables: cases, evidence, suspects"
            elif "syntax error" in error.lower():
                return "📝 SQL syntax error! Check spelling, quotes, and commas."
            else:
                return f"❌ Error: {error[:100]}... Check your syntax!"
        
        return level_hints.get(level_num, "🔍 Check your query against the mission requirements!")

# Optional: Use free alternative (Gemini API) if OpenAI key not available
class FreeAIFallback:
    """Fallback to free AI options or local rules"""
    
    @staticmethod
    def get_hint(level_num: int, error_type: str = None) -> str:
        """Simple rule-based hints when no API key is available"""
        
        hints = {
            1: {
                'syntax': "Start with SELECT, then *, then FROM cases",
                'logic': "Use SELECT * FROM cases to view all case files",
                'common': "Remember to end with a semicolon ;"
            },
            2: {
                'syntax': "Use WHERE clause with AND to combine conditions",
                'logic': "Filter for unsolved (solved = 0) murder cases",
                'common': "Use single quotes around text: 'Murder'"
            },
            3: {
                'syntax': "ORDER BY sorts, LIMIT restricts rows",
                'logic': "Filter high priority, sort newest first, limit to 3",
                'common': "DESC shows newest first"
            },
            4: {
                'syntax': "GROUP BY groups rows, COUNT(*) counts them",
                'logic': "Group by crime_type and count cases per type",
                'common': "Use AS to name the count column"
            },
            5: {
                'syntax': "JOIN connects tables ON matching columns",
                'logic': "Join evidence with cases using case_id",
                'common': "Use table aliases (e, c) for shorter queries"
            }
        }
        
        level_hint = hints.get(level_num, hints[1])
        
        if error_type == 'syntax':
            return f"💡 Syntax Tip: {level_hint['syntax']}"
        elif error_type == 'logic':
            return f"💡 Logic Tip: {level_hint['logic']}"
        else:
            return f"💡 Hint: {level_hint['logic']}\n\nCommon issue: {level_hint['common']}"