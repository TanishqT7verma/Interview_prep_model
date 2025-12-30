import time
import uuid
import hashlib
import random  # ADD THIS LINE
from datetime import datetime
from typing import List, Dict, Any
from models import InterviewSession, RoundResult, Question
from question_bank import LLMQuestionGenerator
from evaluation import Evaluator
from config import Config

class EnhancedInterviewEngine:
    def __init__(self):
        self.config = Config()
        self.question_generator = LLMQuestionGenerator()
        self.evaluator = Evaluator()
        self.active_sessions = {}
        self.question_history = {}  # session_id -> list of generated questions
        
    def _get_question_hash(self, question_text: str) -> str:
        """Generate hash for question to avoid duplicates"""
        return hashlib.md5(question_text.encode()).hexdigest()[:10]
    
    def start_interview(self, target_role: str, experience_level: str) -> Dict[str, Any]:
        """Start a new interview session"""
        session_id = str(uuid.uuid4())
        
        session = InterviewSession(
            session_id=session_id,
            target_role=target_role,
            experience_level=experience_level,
            start_time=datetime.now(),
            current_round=1
        )
        
        self.active_sessions[session_id] = session
        self.question_history[session_id] = []
        
        # Generate first round questions
        round_questions = self._generate_unique_round_questions(
            1, target_role, experience_level, session_id
        )
        
        return {
            "session_id": session_id,
            "message": f"Interview started for {target_role} ({experience_level})",
            "current_round": 1,
            "total_questions": len(round_questions),
            "questions": round_questions
        }
    
    def _generate_unique_round_questions(self, round_num: int, role: str, 
                                        level: str, session_id: str) -> List[Dict[str, Any]]:
        """Generate unique questions avoiding duplicates in current session"""
        total_questions = self.config.ROUND_SETTINGS[round_num]["total_questions"]
        questions = []
        attempts = 0
        max_attempts = total_questions * 3  # Allow some retries
        
        while len(questions) < total_questions and attempts < max_attempts:
            # Get topics for this role
            topics = self.config.ROLE_TOPICS.get(role, {}).get(level, ["General"])
            topic = random.choice(topics) if topics else "General"
            
            # Generate question
            question = self.question_generator.generate_question(
                round_num, role, level, topic
            )
            
            # Check if similar question already generated
            q_hash = self._get_question_hash(question["text"])
            
            if q_hash not in self.question_history[session_id]:
                questions.append(question)
                self.question_history[session_id].append(q_hash)
            
            attempts += 1
        
        # If we couldn't generate enough unique questions, add fallbacks
        if len(questions) < total_questions:
            needed = total_questions - len(questions)
            for i in range(needed):
                fallback = self._generate_fallback_question(round_num, role, level)
                questions.append(fallback)
        
        return questions
    
    def _generate_fallback_question(self, round_num: int, role: str, level: str) -> Dict[str, Any]:
        """Generate a fallback question when LLM fails"""
        topics = self.config.ROLE_TOPICS.get(role, {}).get(level, ["General"])
        topic = random.choice(topics) if topics else "General"
        
        if round_num == 1:
            q_type = random.choice(["mcq", "one_word"])
            if q_type == "mcq":
                return self.question_generator._create_fallback_mcq(topic, "medium")
            else:
                return self.question_generator._create_fallback_one_word(topic, "medium")
        elif round_num == 2:
            q_type = random.choice(["theory", "code_snippet", "output_prediction", "fill_blank"])
            if q_type == "theory":
                return self.question_generator._create_fallback_theory(topic, "medium")
            elif q_type == "code_snippet":
                return self.question_generator._create_fallback_code_snippet(topic, "medium")
            elif q_type == "output_prediction":
                return self.question_generator._create_fallback_code_snippet(topic, "medium")
            else:
                return self.question_generator._create_fallback_fill_blank(topic, "medium")
        else:
            return self.question_generator._create_fallback_coding_problem(topic, "medium")
    
    def submit_round(self, session_id: str, answers: List[Dict[str, Any]], 
                    time_spent: float) -> Dict[str, Any]:
        """Submit answers for current round and evaluate"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        current_round = session.current_round
        
        # Process questions with answers
        questions = []
        for q_data in answers:
            question = Question(
                id=q_data["question_id"],
                round_number=current_round,
                type=q_data["type"],
                text=q_data["question_text"],
                topic=q_data.get("topic", "Unknown"),
                difficulty=q_data.get("difficulty", "medium"),
                options=q_data.get("options"),
                correct_answer=q_data["correct_answer"],
                user_answer=q_data["user_answer"],
                time_spent=q_data.get("time_spent", 0)
            )
            
            # Evaluate answer (enhanced with LLM for complex questions)
            question.is_correct = self._evaluate_with_llm_if_needed(
                question, q_data["user_answer"]
            )
            questions.append(question)
        
        # Calculate score
        results = self.evaluator.calculate_round_score(questions)
        score = results["score"]
        
        # Create round result
        round_result = RoundResult(
            round_number=current_round,
            score=score,
            total_questions=len(questions),
            correct_answers=results["correct_count"],
            time_spent=time_spent,
            questions=questions,
            passed=score >= self.config.ROUND_SETTINGS[current_round]["passing_score"]
        )
        
        session.completed_rounds.append(round_result)
        
        # Check if passed
        if not round_result.passed:
            session.is_complete = True
            feedback = self.evaluator.generate_feedback(
                session.completed_rounds, 
                failed_round=current_round
            )
            
            return {
                "status": "failed",
                "round": current_round,
                "score": score,
                "passing_score": self.config.ROUND_SETTINGS[current_round]["passing_score"],
                "feedback": feedback.dict(),
                "message": f"Failed Round {current_round}. Score: {score:.1f}%",
                "detailed_analysis": self._generate_llm_feedback(questions, score)
            }
        
        # Check if all rounds completed
        if current_round == 3:
            session.is_complete = True
            feedback = self.evaluator.generate_feedback(session.completed_rounds)
            
            return {
                "status": "completed",
                "round": current_round,
                "score": score,
                "feedback": feedback.dict(),
                "message": "Congratulations! You passed all rounds!",
                "detailed_analysis": self._generate_llm_feedback(questions, score, final=True)
            }
        
        # Move to next round
        session.current_round += 1
        
        # Generate next round questions
        next_questions = self._generate_unique_round_questions(
            session.current_round,
            session.target_role,
            session.experience_level,
            session_id
        )
        
        return {
            "status": "next_round",
            "current_round": session.current_round,
            "previous_score": score,
            "questions": next_questions,
            "message": f"Round {current_round} passed! Moving to Round {session.current_round}"
        }
    
    def _evaluate_with_llm_if_needed(self, question: Question, user_answer: str) -> bool:
        """Use LLM for evaluating complex answers when needed"""
        if question.type in ["mcq", "one_word", "fill_blank", "output_prediction"]:
            # Simple exact or close match
            return self.evaluator.evaluate_answer(question, user_answer)
        
        elif question.type in ["theory", "code_snippet"]:
            # Use LLM for better evaluation
            try:
                prompt = f"""Evaluate if the candidate's answer is correct for this interview question.

Question: {question.text}
Correct Answer: {question.correct_answer}
Candidate's Answer: {user_answer}

Evaluate on a scale of 0-100 where:
- 0-49: Incorrect or very incomplete
- 50-69: Partially correct but missing key points
- 70-100: Correct or mostly correct with minor omissions

Return only the numerical score (0-100)."""
                
                response = self.question_generator._call_deepseek(prompt)
                score = int(response.strip())
                return score >= 70  # Consider correct if 70% or above
                
            except:
                # Fallback to basic evaluation
                return self.evaluator.evaluate_answer(question, user_answer)
        
        else:  # coding_problem
            # For coding problems, check if solution is plausible
            return len(user_answer.strip()) > 30  # Basic check
    
    def _generate_llm_feedback(self, questions: List[Question], score: float, 
                              final: bool = False) -> str:
        """Generate detailed feedback using LLM"""
        try:
            incorrect_questions = [q for q in questions if not q.is_correct]
            
            if not incorrect_questions:
                return "Excellent performance! All answers were correct or near-perfect."
            
            # Create summary of mistakes
            mistakes_summary = "\n".join([
                f"- Q: {q.text[:100]}... | Your answer: {q.user_answer[:50]}... | Expected: {q.correct_answer[:50]}..."
                for q in incorrect_questions[:3]  # Limit to 3 for brevity
            ])
            
            prompt = f"""As an experienced technical interviewer, provide constructive feedback for a candidate.

Overall Score: {score}%
Number of incorrect answers: {len(incorrect_questions)} out of {len(questions)}

Key mistakes made:
{mistakes_summary}

Provide concise feedback (3-4 sentences) focusing on:
1. What they did well
2. Main areas for improvement
3. Specific study recommendations
4. Encouragement for next steps

Format as a helpful, professional interviewer."""
            
            feedback = self.question_generator._call_deepseek(prompt)
            return feedback
            
        except Exception as e:
            return f"Detailed analysis could not be generated. Error: {str(e)}"
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of interview session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "target_role": session.target_role,
            "experience_level": session.experience_level,
            "current_round": session.current_round,
            "is_complete": session.is_complete,
            "completed_rounds": len(session.completed_rounds),
            "start_time": session.start_time.isoformat()
        }
