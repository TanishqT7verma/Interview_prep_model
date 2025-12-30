# frontend.py (enhanced)
import gradio as gr
import requests
import json
import time
from datetime import datetime

class EnhancedInterviewFrontend:
    def __init__(self):
        self.current_session = None
        self.current_round = 1
        self.start_time = None
        self.questions = []
        self.answer_widgets = []
        
    def create_question_ui(self, questions):
        """Dynamically create UI elements for each question"""
        with gr.Column():
            for i, q in enumerate(questions, 1):
                gr.Markdown(f"### Question {i}")
                gr.Markdown(f"**Topic:** {q.get('topic', 'General')} | **Difficulty:** {q.get('difficulty', 'Medium')}")
                gr.Markdown(q['text'])
                
                if q['type'] == 'mcq' and q.get('options'):
                    options = q['options']
                    answer_input = gr.Radio(
                        choices=options,
                        label=f"Select answer for Question {i}",
                        elem_id=f"q{i}_answer"
                    )
                elif q['type'] == 'coding_problem':
                    answer_input = gr.Code(
                        language="python",
                        label=f"Write your solution for Question {i}",
                        lines=10,
                        elem_id=f"q{i}_code"
                    )
                else:
                    answer_input = gr.Textbox(
                        label=f"Answer for Question {i}",
                        elem_id=f"q{i}_answer"
                    )
                
                self.answer_widgets.append({
                    "id": q["id"],
                    "widget": answer_input,
                    "type": q["type"]
                })
        
        return self.answer_widgets