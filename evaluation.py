import re
import requests
from typing import List, Dict, Any
from models import Question, RoundResult, Feedback

# =========================
# OLLAMA / DEEPSEEK CONFIG
# =========================
OLLAMA_URL = "http://192.168.1.252:11434"
MODEL_NAME = "deepseek-r1:32b"


# =========================
# AI EVALUATION FUNCTION
# =========================
def evaluate_with_llm(question: Question, user_answer: str) -> bool:
    """
    Uses DeepSeek to evaluate correctness of an answer.
    Works for one-word, fill-blank, theory, and code explanations.
    """

    # ---- SAFE QUESTION TEXT EXTRACTION ----
    question_text = (
        getattr(question, "question_text", None)
        or getattr(question, "question", None)
        or getattr(question, "text", None)
        or getattr(question, "prompt", None)
        or "Question text not available"
    )

    prompt = f"""
You are an exam evaluator.

Question:
{question_text}

Expected Answer:
{question.correct_answer}

User Answer:
{user_answer}

Task:
Decide whether the user answer is correct.
Consider synonyms, abbreviations, and equivalent meanings.
Respond with ONLY one word: YES or NO.
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        result = response.json().get("response", "").strip().upper()
        return result == "YES"

    except Exception as e:
        print("LLM evaluation failed:", e)
        return False


# =========================
# EVALUATOR CLASS
# =========================
class Evaluator:

    @staticmethod
    def evaluate_answer(question: Question, user_answer: str) -> bool:
        """
        Determines whether a user's answer is correct.
        """

        if not user_answer or not user_answer.strip():
            return False

        # ---------- MCQ (STRICT) ----------
        if question.type == "mcq":
            return user_answer.strip().lower() == question.correct_answer.lower()

        # ---------- ONE WORD / FILL BLANK ----------
        elif question.type in ["one_word", "fill_blank"]:
            # First try exact match
            if user_answer.strip().lower() == question.correct_answer.lower():
                return True

            # Fallback to DeepSeek AI
            return evaluate_with_llm(question, user_answer)

        # ---------- OUTPUT PREDICTION ----------
        elif question.type == "output_prediction":
            user_clean = re.sub(r"\s+", "", user_answer)
            correct_clean = re.sub(r"\s+", "", question.correct_answer)
            return user_clean == correct_clean

        # ---------- THEORY / CODE EXPLANATION ----------
        elif question.type in ["theory", "code_snippet"]:
            return evaluate_with_llm(question, user_answer)

        # ---------- CODING PROBLEM (BASIC PLACEHOLDER) ----------
        elif question.type == "coding_problem":
            return len(user_answer.strip()) > 20

        return False


    # =========================
    # ROUND SCORE CALCULATION
    # =========================
    @staticmethod
    def calculate_round_score(questions: List[Question]) -> Dict[str, Any]:
        correct_count = sum(1 for q in questions if q.is_correct)
        total = len(questions)
        score = (correct_count / total) * 100 if total > 0 else 0

        topic_performance = {}
        for q in questions:
            topic = q.topic
            topic_performance.setdefault(topic, {"total": 0, "correct": 0})
            topic_performance[topic]["total"] += 1
            if q.is_correct:
                topic_performance[topic]["correct"] += 1

        topic_scores = {
            topic: (stats["correct"] / stats["total"]) * 100
            for topic, stats in topic_performance.items()
        }

        strongest = sorted(topic_scores, key=topic_scores.get, reverse=True)[:3]
        weakest = sorted(topic_scores, key=topic_scores.get)[:3]

        return {
            "score": round(score, 2),
            "correct_count": correct_count,
            "total": total,
            "strongest_topics": strongest,
            "weakest_topics": weakest
        }


    # =========================
    # FEEDBACK GENERATION
    # =========================
    @staticmethod
    def generate_feedback(
        round_results: List[RoundResult],
        failed_round: int = None
    ) -> Feedback:

        if failed_round is not None:
            failed = round_results[-1]

            topic_stats = {}
            for q in failed.questions:
                topic_stats.setdefault(q.topic, {"total": 0, "correct": 0})
                topic_stats[q.topic]["total"] += 1
                if q.is_correct:
                    topic_stats[q.topic]["correct"] += 1

            topic_scores = {
                topic: (s["correct"] / s["total"]) * 100
                for topic, s in topic_stats.items()
            }

            strongest = sorted(topic_scores, key=topic_scores.get, reverse=True)[:3]
            weakest = sorted(topic_scores, key=topic_scores.get)[:3]

            recommendations = []
            for topic in weakest:
                if topic_scores[topic] < 50:
                    recommendations.append(f"Focus on {topic} fundamentals")
                elif topic_scores[topic] < 70:
                    recommendations.append(f"Practice more {topic} problems")

            return Feedback(
                score=failed.score,
                strongest_topics=strongest,
                weakest_topics=weakest,
                recommendations=recommendations,
                time_spent={f"round_{failed_round}": failed.time_spent}
            )

        # -------- OVERALL FEEDBACK --------
        total_score = sum(r.score * r.total_questions for r in round_results)
        total_questions = sum(r.total_questions for r in round_results)
        overall_score = total_score / total_questions if total_questions else 0

        all_topics = {}
        for r in round_results:
            for q in r.questions:
                all_topics.setdefault(q.topic, {"total": 0, "correct": 0})
                all_topics[q.topic]["total"] += 1
                if q.is_correct:
                    all_topics[q.topic]["correct"] += 1

        topic_scores = {
            topic: (s["correct"] / s["total"]) * 100
            for topic, s in all_topics.items()
        }

        strongest = sorted(topic_scores, key=topic_scores.get, reverse=True)[:3]
        weakest = sorted(topic_scores, key=topic_scores.get)[:3]

        time_spent = {f"round_{i+1}": r.time_spent for i, r in enumerate(round_results)}
        time_spent["total"] = sum(r.time_spent for r in round_results)

        return Feedback(
            score=round(overall_score, 2),
            strongest_topics=strongest,
            weakest_topics=weakest,
            recommendations=[
                f"Your strongest area is {strongest[0] if strongest else 'multiple areas'}",
                f"Consider practicing {weakest[0] if weakest else 'various topics'}"
            ],
            time_spent=time_spent

