# config.py (updated)
import os
from typing import Dict, Any

class Config:
    OLLAMA_API_BASE = "http://192.168.1.252:11434"
    OLLAMA_MODEL = "deepseek-r1:32b"
    API_TIMEOUT = 500  # Should be 120 seconds
    
    # Interview settings
    ROUND_SETTINGS = {
        1: {"total_questions": 20, "passing_score": 70, "time_limit": 600},  # 10 minutes
        2: {"total_questions": 15, "passing_score": 70, "time_limit": 900},  # 15 minutes
        3: {"total_questions": 3, "passing_score": 0, "time_limit": 1800}    # 30 minutes
    }
    
    # Question generation settings
    MAX_QUESTION_GENERATION_ATTEMPTS = 5
    ENABLE_LLM_EVALUATION = True
    
    # Role-specific topics (expanded)
    ROLE_TOPICS = {
        "Software Engineer": {
            "entry": ["Python Basics", "OOP Concepts", "Data Structures", 
                     "Algorithms", "SQL Fundamentals", "Git & Version Control",
                     "Debugging", "Testing Basics", "Web Basics"],
            "mid": ["System Design", "API Design", "Testing Strategies", 
                   "Concurrency", "Database Design", "Cloud Basics",
                   "Microservices", "Performance Optimization"],
            "senior": ["Software Architecture", "Scalability", "Distributed Systems",
                      "Cloud Architecture", "Technical Leadership", "Mentoring",
                      "Code Review Best Practices", "DevOps", "Security"]
        },
        "Data Scientist": {
            "entry": ["Python for Data Science", "Statistics Fundamentals", 
                     "Pandas & NumPy", "Data Visualization", "ML Basics",
                     "SQL for Analysis", "Data Cleaning"],
            "mid": ["Feature Engineering", "Model Evaluation", "Deep Learning Basics",
                   "SQL Advanced", "A/B Testing", "Time Series Analysis",
                   "Model Deployment"],
            "senior": ["MLOps", "Experiment Design", "Big Data Technologies",
                      "Production ML Systems", "Team Leadership", "Stakeholder Management",
                      "Advanced Statistics"]
        },
        # ... (other roles similar)
    }
    
    # Difficulty progression
    DIFFICULTY_PROGRESSION = {
        "entry": {"round1": ["easy", "medium"], 
                 "round2": ["medium"], 
                 "round3": ["easy", "medium"]},
        "mid": {"round1": ["medium"], 
               "round2": ["medium", "hard"], 
               "round3": ["medium"]},
        "senior": {"round1": ["medium", "hard"], 
                  "round2": ["hard"], 
                  "round3": ["medium", "hard"]}
    }