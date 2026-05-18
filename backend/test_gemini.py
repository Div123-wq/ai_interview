import sys; sys.path.append('.')
from services.ai_engine import _call
prompt = """You are an expert interviewer at a top tech company.
Generate exactly 5 interview questions for a intermediate-level Software Engineer position.
Interview type: technical.

Rules:
- Technical: coding, system design, domain knowledge
- Behavioral: STAR-method situational questions
- Mixed: alternate between technical and behavioral
- Increase difficulty progressively

Return ONLY a valid JSON array (no extra text):
[
  {"question": "...", "type": "technical", "hint": "Key points to cover: ..."}
]"""
res = _call(prompt, json_output=False)
open('gemini_out.txt', 'w', encoding='utf-8').write(res)
