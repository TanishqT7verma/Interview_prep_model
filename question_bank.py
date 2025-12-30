# question_bank.py
import random
import uuid
import json
import requests
from typing import List, Dict, Any
from config import Config

class LLMQuestionGenerator:
    def __init__(self):
        self.config = Config()
        self.generated_questions = set()  # Track question hashes
        
    def _call_deepseek(self, prompt: str, system_prompt: str = None) -> str:
        """Call DeepSeek R1 via Ollama API"""
        try:
            payload = {
                "model": self.config.OLLAMA_MODEL,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.config.OLLAMA_API_BASE}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"API call failed: {response.status_code}")
                
        except Exception as e:
            print(f"Error calling DeepSeek: {e}")
            # Fallback to predefined questions
            return ""
    
    def generate_question(self, round_num: int, role: str, level: str, 
                         topic: str = None) -> Dict[str, Any]:
        """Generate a unique question using DeepSeek"""
        
        # If no topic provided, select one based on role and level
        if not topic:
            topics = self.config.ROLE_TOPICS.get(role, {}).get(level, ["General"])
            topic = random.choice(topics)
        
        # Determine difficulty based on round and level
        if round_num == 1:
            difficulty = random.choice(["easy", "medium"])
        elif round_num == 2:
            difficulty = random.choice(["medium", "hard"])
        else:  # round 3
            difficulty = "medium" if len(self.generated_questions) % 3 == 0 else "hard"
        
        # Generate question based on round type
        if round_num == 1:
            question_type = random.choice(["mcq", "one_word"])
            return self._generate_round1_question(role, level, topic, difficulty, question_type)
        elif round_num == 2:
            question_type = random.choice(["theory", "code_snippet", "output_prediction", "fill_blank"])
            return self._generate_round2_question(role, level, topic, difficulty, question_type)
        else:  # round 3
            return self._generate_round3_question(role, level, topic, difficulty)
    
    def _generate_round1_question(self, role: str, level: str, topic: str, 
                                 difficulty: str, q_type: str) -> Dict[str, Any]:
        """Generate Round 1 question using LLM"""
        
        if q_type == "mcq":
            prompt = f"""Generate a {difficulty} level Multiple Choice Question (MCQ) for a {level} level {role} position.
Topic: {topic}

Format requirements:
1. Question should test practical knowledge
2. Provide 4 options (A, B, C, D)
3. Mark the correct answer clearly
4. Make it unique and interview-relevant

Example format:
Question: What is the time complexity of quicksort in average case?
Options: A) O(n log n), B) O(n²), C) O(log n), D) O(n)
Correct Answer: A

Now generate a new question:"""
            
            response = self._call_deepseek(
                prompt,
                system_prompt="You are a technical interviewer creating screening questions. Be concise and accurate."
            )
            
            # Parse the response
            return self._parse_mcq_response(response, topic, difficulty)
            
        else:  # one_word
            prompt = f"""Generate a {difficulty} level one-word answer question for a {level} level {role} position.
Topic: {topic}

Format requirements:
1. Question should require a single word or short phrase answer
2. Make it technical and specific
3. Provide the correct answer
4. Make it unique and interview-relevant

Example format:
Question: Which Python keyword is used to define a function?
Correct Answer: def

Now generate a new question:"""
            
            response = self._call_deepseek(
                prompt,
                system_prompt="You are a technical interviewer creating screening questions."
            )
            
            return self._parse_one_word_response(response, topic, difficulty)
    
    def _generate_round2_question(self, role: str, level: str, topic: str,
                                 difficulty: str, q_type: str) -> Dict[str, Any]:
        """Generate Round 2 question using LLM"""
        
        if q_type == "theory":
            prompt = f"""Generate a {difficulty} level theory question for a {level} level {role} position.
Topic: {topic}

Format requirements:
1. Ask for explanation of a concept
2. Question should test deep understanding
3. Provide a concise but complete correct answer
4. Make it unique and challenging

Example format:
Question: Explain the CAP theorem and its implications for distributed systems.
Correct Answer: CAP theorem states that a distributed system can only guarantee two out of three: Consistency, Availability, Partition Tolerance. It forces trade-offs in system design.

Now generate a new question:"""
            
            response = self._call_deepseek(prompt)
            return self._parse_theory_response(response, topic, difficulty)
            
        elif q_type == "code_snippet":
            prompt = f"""Generate a {difficulty} level code snippet question for a {level} level {role} position.
Topic: {topic}
Programming Language: Python (unless specified otherwise by role)

Format requirements:
1. Provide a code snippet with an interesting behavior
2. Ask what the output will be
3. Provide the correct output with explanation
4. Make it test debugging skills

Example format:
Question: What is the output of this Python code?
Code: 
def func(x, y=[]):
    y.append(x)
    return y

print(func(1))
print(func(2))
Correct Answer: [1] [1, 2] because default arguments are evaluated only once when function is defined.

Now generate a new question:"""
            
            response = self._call_deepseek(prompt)
            return self._parse_code_snippet_response(response, topic, difficulty)
            
        elif q_type == "output_prediction":
            prompt = f"""Generate a {difficulty} level output prediction question for a {level} level {role} position.
Topic: {topic}
Programming Language: Python (unless role-specific)

Format requirements:
1. Provide a short code snippet (3-5 lines)
2. Ask to predict the output
3. Provide the exact output
4. Make it test language-specific knowledge

Now generate a new question:"""
            
            response = self._call_deepseek(prompt)
            return self._parse_output_prediction_response(response, topic, difficulty)
            
        else:  # fill_blank
            prompt = f"""Generate a {difficulty} level fill-in-the-blank question for a {level} level {role} position.
Topic: {topic}
Programming Language: Python (unless role-specific)

Format requirements:
1. Provide code with one or two blanks (_____)
2. Ask what should fill the blank(s)
3. Provide the correct answer
4. Make it test syntax or API knowledge

Example format:
Question: Fill in the blank to open a file for reading:
file = open('data.txt', '_____')
Correct Answer: 'r'

Now generate a new question:"""
            
            response = self._call_deepseek(prompt)
            return self._parse_fill_blank_response(response, topic, difficulty)
    
    def _generate_round3_question(self, role: str, level: str, topic: str,
                                 difficulty: str) -> Dict[str, Any]:
        """Generate Round 3 coding problem using LLM"""
        
        if len(self.generated_questions) % 3 == 0:  # First in round 3 is easy
            difficulty = "easy"
        else:
            difficulty = "medium"
        
        prompt = f"""Generate a {difficulty} level LeetCode-style coding problem for a {level} level {role} position.
Topic: {topic}
Programming Language: Python

Format requirements:
1. Describe a clear problem statement
2. Include input/output examples
3. Mention constraints
4. Provide an optimal solution in Python
5. Make it interview-appropriate

Example format:
Question: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
Example: nums = [2,7,11,15], target = 9 → Output: [0,1]
Constraints: Each input has exactly one solution, cannot use same element twice.

Correct Answer (Python solution):
def twoSum(nums, target):
    hashmap = {{}}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in hashmap:
            return [hashmap[complement], i]
        hashmap[num] = i
    return []

Now generate a new unique coding problem:"""
        
        response = self._call_deepseek(prompt)
        return self._parse_coding_problem_response(response, topic, difficulty)
    
    def _parse_mcq_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for MCQ"""
        try:
            lines = response.strip().split('\n')
            question = ""
            options = []
            correct_answer = ""
            
            for line in lines:
                if line.startswith('Question:') or line.startswith('Q:'):
                    question = line.split(':', 1)[1].strip()
                elif line.startswith('Options:'):
                    # Parse options
                    opts_text = line.split(':', 1)[1].strip()
                    options = [opt.strip() for opt in opts_text.split(',')]
                elif line.startswith('Correct Answer:'):
                    correct_answer = line.split(':', 1)[1].strip()
                elif line.strip() and '?' in line and not question:
                    question = line.strip()
                elif len(line.strip()) > 1 and line.strip()[1] == ')' and len(options) < 4:
                    options.append(line.strip())
            
            # If parsing failed, create fallback
            if not question:
                question = response.split('\n')[0].strip()
                options = ["Option A", "Option B", "Option C", "Option D"]
                correct_answer = "Option A"
            
            return {
                "id": f"mcq_{uuid.uuid4().hex[:8]}",
                "type": "mcq",
                "text": question,
                "topic": topic,
                "difficulty": difficulty,
                "options": options[:4],  # Ensure exactly 4 options
                "correct_answer": correct_answer
            }
            
        except Exception as e:
            print(f"Error parsing MCQ: {e}")
            return self._create_fallback_mcq(topic, difficulty)
    
    def _parse_one_word_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for one-word question"""
        try:
            lines = response.strip().split('\n')
            question = ""
            answer = ""
            
            for line in lines:
                if line.startswith('Question:') or line.startswith('Q:'):
                    question = line.split(':', 1)[1].strip()
                elif line.startswith('Correct Answer:'):
                    answer = line.split(':', 1)[1].strip()
                elif '?' in line and not question:
                    question = line.strip()
                elif line.strip() and not answer and len(line.split()) < 5:
                    answer = line.strip()
            
            if not question:
                question = response.split('\n')[0].strip()
                answer = "Python"  # Fallback answer
            
            return {
                "id": f"one_{uuid.uuid4().hex[:8]}",
                "type": "one_word",
                "text": question,
                "topic": topic,
                "difficulty": difficulty,
                "correct_answer": answer
            }
            
        except Exception as e:
            print(f"Error parsing one-word: {e}")
            return self._create_fallback_one_word(topic, difficulty)
    
    def _parse_theory_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for theory question"""
        try:
            # Split question and answer
            parts = response.split('Correct Answer:', 1)
            if len(parts) == 2:
                question = parts[0].replace('Question:', '').strip()
                answer = parts[1].strip()
            else:
                # Try different parsing
                lines = response.strip().split('\n')
                question = lines[0] if lines else "Explain a concept"
                answer = "\n".join(lines[1:]) if len(lines) > 1 else "Detailed explanation"
            
            return {
                "id": f"theory_{uuid.uuid4().hex[:8]}",
                "type": "theory",
                "text": question,
                "topic": topic,
                "difficulty": difficulty,
                "correct_answer": answer[:500]  # Limit answer length
            }
            
        except Exception as e:
            print(f"Error parsing theory: {e}")
            return self._create_fallback_theory(topic, difficulty)
    
    def _parse_code_snippet_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for code snippet question"""
        try:
            # Extract code between backticks
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
            
            if code_blocks:
                code = code_blocks[0]
            else:
                # Try to find indented code
                lines = response.strip().split('\n')
                code_lines = [line for line in lines if line.startswith((' ', '\t'))]
                code = '\n'.join(code_lines) if code_lines else "print('Hello World')"
            
            # Find question
            question_match = re.search(r'Question:(.*?)(?:\n|$)', response)
            question = question_match.group(1).strip() if question_match else "What is the output of this code?"
            
            # Find answer
            answer_match = re.search(r'Correct Answer:(.*?)(?:\n|$)', response, re.DOTALL)
            answer = answer_match.group(1).strip() if answer_match else "Output would be..."
            
            return {
                "id": f"code_{uuid.uuid4().hex[:8]}",
                "type": "code_snippet",
                "text": f"{question}\n\n```python\n{code}\n```",
                "topic": topic,
                "difficulty": difficulty,
                "correct_answer": answer
            }
            
        except Exception as e:
            print(f"Error parsing code snippet: {e}")
            return self._create_fallback_code_snippet(topic, difficulty)
    
    def _parse_output_prediction_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for output prediction"""
        return self._parse_code_snippet_response(response, topic, difficulty)
    
    def _parse_fill_blank_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for fill-in-blank"""
        try:
            lines = response.strip().split('\n')
            question = ""
            answer = ""
            
            for line in lines:
                if '_____' in line or 'blank' in line.lower():
                    question = line.strip()
                elif line.startswith('Correct Answer:'):
                    answer = line.split(':', 1)[1].strip()
                elif line.strip() and not answer:
                    answer = line.strip()
            
            if not question:
                question = lines[0] if lines else "Fill in the blank: _____"
            
            return {
                "id": f"fill_{uuid.uuid4().hex[:8]}",
                "type": "fill_blank",
                "text": question,
                "topic": topic,
                "difficulty": difficulty,
                "correct_answer": answer
            }
            
        except Exception as e:
            print(f"Error parsing fill blank: {e}")
            return self._create_fallback_fill_blank(topic, difficulty)
    
    def _parse_coding_problem_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response for coding problem"""
        try:
            # Split into problem and solution
            parts = response.split('Correct Answer:', 1)
            
            if len(parts) == 2:
                problem = parts[0].strip()
                solution = parts[1].strip()
            else:
                # Try to find solution in code blocks
                import re
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
                if code_blocks:
                    solution = code_blocks[-1]
                    problem = response.replace(f'```\n{solution}\n```', '').strip()
                else:
                    problem = response
                    solution = "# Solution would be implemented here"
            
            return {
                "id": f"coding_{uuid.uuid4().hex[:8]}",
                "type": "coding_problem",
                "text": problem,
                "topic": topic,
                "difficulty": difficulty,
                "correct_answer": solution
            }
            
        except Exception as e:
            print(f"Error parsing coding problem: {e}")
            return self._create_fallback_coding_problem(topic, difficulty)
    
    # Fallback question generators
    def _create_fallback_mcq(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Create fallback MCQ"""
        fallbacks = {
            "Python": {
                "text": f"What is the time complexity of accessing an element in a Python dictionary?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
                "answer": "O(1)"
            },
            "SQL": {
                "text": "Which SQL command is used to remove a table from database?",
                "options": ["DELETE", "REMOVE", "DROP", "TRUNCATE"],
                "answer": "DROP"
            }
        }
        
        fb = fallbacks.get(topic, fallbacks["Python"])
        return {
            "id": f"fb_mcq_{uuid.uuid4().hex[:8]}",
            "type": "mcq",
            "text": fb["text"],
            "topic": topic,
            "difficulty": difficulty,
            "options": fb["options"],
            "correct_answer": fb["answer"]
        }
    
    def _create_fallback_one_word(self, topic: str, difficulty: str) -> Dict[str, Any]:
        return {
            "id": f"fb_one_{uuid.uuid4().hex[:8]}",
            "type": "one_word",
            "text": f"Name a key concept in {topic}",
            "topic": topic,
            "difficulty": difficulty,
            "correct_answer": "Concept"
        }
    
    def _create_fallback_theory(self, topic: str, difficulty: str) -> Dict[str, Any]:
        return {
            "id": f"fb_theory_{uuid.uuid4().hex[:8]}",
            "type": "theory",
            "text": f"Explain the importance of {topic} in software development",
            "topic": topic,
            "difficulty": difficulty,
            "correct_answer": f"{topic} is important because..."
        }
    
    def _create_fallback_code_snippet(self, topic: str, difficulty: str) -> Dict[str, Any]:
        return {
            "id": f"fb_code_{uuid.uuid4().hex[:8]}",
            "type": "code_snippet",
            "text": f"What is the output?\n\n```python\nprint(2 + 2 * 2)\n```",
            "topic": topic,
            "difficulty": difficulty,
            "correct_answer": "6"
        }
    
    def _create_fallback_fill_blank(self, topic: str, difficulty: str) -> Dict[str, Any]:
        return {
            "id": f"fb_fill_{uuid.uuid4().hex[:8]}",
            "type": "fill_blank",
            "text": f"To create a class in Python, use: class MyClass: _____",
            "topic": topic,
            "difficulty": difficulty,
            "correct_answer": "pass"
        }
    
    def _create_fallback_coding_problem(self, topic: str, difficulty: str) -> Dict[str, Any]:
        return {
            "id": f"fb_coding_{uuid.uuid4().hex[:8]}",
            "type": "coding_problem",
            "text": f"Write a function to check if a string is a palindrome",
            "topic": topic,
            "difficulty": difficulty,
            "correct_answer": "def is_palindrome(s):\n    return s == s[::-1]"
        }