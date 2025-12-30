# evaluation.py - UPDATED VERSION
import re
from typing import List, Dict, Any
from models import Question, RoundResult, Feedback, AnswerReview

class Evaluator:
    @staticmethod
    def evaluate_answer(question: Question, user_answer: str) -> bool:
        """Evaluate if user answer is correct"""
        if question.type in ["mcq", "one_word", "fill_blank"]:
            # Exact match for simple types
            return user_answer.strip().lower() == question.correct_answer.lower()
        
        elif question.type == "output_prediction":
            # Remove whitespace and compare
            user_clean = re.sub(r'\s+', '', user_answer)
            correct_clean = re.sub(r'\s+', '', question.correct_answer)
            return user_clean == correct_clean
        
        elif question.type in ["theory", "code_snippet"]:
            # For theory questions, check keywords
            correct_lower = question.correct_answer.lower()
            user_lower = user_answer.lower()
            
            # Check if key terms are present
            key_terms = set(correct_lower.split()[:5])
            user_terms = set(user_lower.split())
            
            matches = len(key_terms.intersection(user_terms))
            return matches / len(key_terms) >= 0.6 if key_terms else False
        
        else:  # coding_problem
            return len(user_answer.strip()) > 20
    
    @staticmethod
    def calculate_round_score(questions: List[Question]) -> Dict[str, Any]:
        """Calculate score for a round"""
        correct_count = sum(1 for q in questions if q.is_correct)
        total = len(questions)
        score = (correct_count / total) * 100 if total > 0 else 0
        
        # Analyze topics
        topic_performance = {}
        for q in questions:
            topic = q.topic
            if topic not in topic_performance:
                topic_performance[topic] = {"total": 0, "correct": 0}
            topic_performance[topic]["total"] += 1
            if q.is_correct:
                topic_performance[topic]["correct"] += 1
        
        # Find strongest and weakest topics
        topic_scores = {}
        for topic, stats in topic_performance.items():
            topic_scores[topic] = (stats["correct"] / stats["total"]) * 100
        
        strongest = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        weakest = sorted(topic_scores.items(), key=lambda x: x[1])[:3]
        
        return {
            "score": round(score, 2),
            "correct_count": correct_count,
            "total": total,
            "strongest_topics": [t[0] for t in strongest],
            "weakest_topics": [t[0] for t in weakest]
        }
    
    @staticmethod
    def generate_feedback(round_results: List[RoundResult], failed_round: int = None) -> Feedback:
        """Generate feedback with correct answers"""
        if failed_round is not None:
            failed_result = round_results[-1]
            
            topic_stats = {}
            correct_answers_list = []  # NEW: Store correct answers for display
            
            for q in failed_result.questions:
                topic = q.topic
                if topic not in topic_stats:
                    topic_stats[topic] = {"total": 0, "correct": 0}
                topic_stats[topic]["total"] += 1
                if q.is_correct:
                    topic_stats[topic]["correct"] += 1
                
                # ADDED: Create AnswerReview for each question
                answer_review = AnswerReview(
                    question=q.text,
                    user_answer=q.user_answer or "No answer",
                    correct_answer=q.correct_answer,
                    topic=q.topic,
                    is_correct=q.is_correct or False
                )
                correct_answers_list.append(answer_review)
            
            topic_scores = {topic: (stats["correct"]/stats["total"])*100 
                          for topic, stats in topic_stats.items()}
            
            strongest = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            weakest = sorted(topic_scores.items(), key=lambda x: x[1])[:3]
            
            recommendations = []
            for topic, score in weakest:
                if score < 50:
                    recommendations.append(f"Focus on {topic} fundamentals")
                elif score < 70:
                    recommendations.append(f"Practice more {topic} problems")
            
            return Feedback(
                score=failed_result.score,
                strongest_topics=[t[0] for t in strongest],
                weakest_topics=[t[0] for t in weakest],
                correct_answers=correct_answers_list,  # ADDED THIS
                recommendations=recommendations,
                time_spent={f"round_{failed_round}": failed_result.time_spent}
            )
        
        else:
            total_score = sum(r.score * r.total_questions for r in round_results)
            total_questions = sum(r.total_questions for r in round_results)
            overall_score = total_score / total_questions
            
            all_topics = {}
            correct_answers_list = []  # NEW: For completed interview
            
            for result in round_results:
                for q in result.questions:
                    topic = q.topic
                    if topic not in all_topics:
                        all_topics[topic] = {"total": 0, "correct": 0}
                    all_topics[topic]["total"] += 1
                    if q.is_correct:
                        all_topics[topic]["correct"] += 1
                    
                    # ADDED: For completed interview, include all questions
                    answer_review = AnswerReview(
                        question=q.text,
                        user_answer=q.user_answer or "No answer",
                        correct_answer=q.correct_answer,
                        topic=q.topic,
                        is_correct=q.is_correct or False
                    )
                    correct_answers_list.append(answer_review)
            
            topic_scores = {topic: (stats["correct"]/stats["total"])*100 
                          for topic, stats in all_topics.items()}
            
            strongest = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            weakest = sorted(topic_scores.items(), key=lambda x: x[1])[:3]
            
            recommendations = [
                f"Your strongest area is {strongest[0][0] if strongest else 'multiple areas'}",
                f"Consider practicing {weakest[0][0] if weakest else 'various topics'}"
            ]
            
            time_spent = {f"round_{i+1}": r.time_spent for i, r in enumerate(round_results)}
            time_spent["total"] = sum(r.time_spent for r in round_results)
            
            return Feedback(
                score=round(overall_score, 2),
                strongest_topics=[t[0] for t in strongest],
                weakest_topics=[t[0] for t in weakest],
                correct_answers=correct_answers_list,  # ADDED THIS
                recommendations=recommendations,
                time_spent=time_spent
            )