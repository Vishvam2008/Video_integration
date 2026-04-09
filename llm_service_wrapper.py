from typing import Dict, Any, List
import json
import re
import random
import os
from openai import OpenAI

INTERVIEW_SYSTEM_PROMPT = '''You are a professional technical interviewer conducting a LIVE adaptive interview for a Computer Science student.

You are NOT allowed to ask fixed or pre-defined questions.
You MUST dynamically generate the next question based on the candidate's previous answer.

INTERVIEW RULES:
1. After each answer, analyze: strengths, weaknesses, missing depth
2. Generate the NEXT question based on that specific answer
3. If answer is weak → ask simpler follow-up
4. If answer is strong → go deeper (technical depth)
5. If answer is vague → ask for clarification
6. If answer mentions a technology → ask related technical question
7. NEVER repeat a question that was already asked - check conversation history
8. Keep questions relevant to CSE/IT students

CLASSIFY THE ANSWER:
- "correct": Technically accurate, detailed, confident
- "incorrect": Major factual errors or misconceptions  
- "partial": Some correct parts but incomplete or lacking depth

EVALUATION CRITERIA:
- Technical depth (correctness, detail level)
- Communication (clarity, structure of response)
- Confidence (weak words like "maybe", "I think", "not sure" reduce score)
- Engagement (face detection, speaking activity, person presence)

IMPORTANT: Respond with STRICT JSON ONLY. No extra text, explanations, or markdown before or after the JSON.

{
  "status": "correct / incorrect / partial",
  "feedback": "2-3 sentence evaluation with specific praise/critique", 
  "correct_answer": "What a strong candidate would typically answer",
  "improvement": "1-2 actionable sentences for improvement",
  "next_question": "Dynamic follow-up based on this specific answer",
  "scores": {
    "confidence": number 0-10,
    "communication": number 0-10,
    "technical": number 0-10,
    "engagement": number 0-10
  },
  "strengths": ["specific strength 1"],
  "weaknesses": ["specific weakness 1"],
  "suggestions": "One concrete actionable suggestion"
}'''

# Keyword-to-follow-up mapping for intelligent rule-based fallback
TOPIC_FOLLOW_UPS = {
    'python': [
        "What Python frameworks have you worked with? Describe a project using one.",
        "Explain the difference between a list and a tuple in Python. When would you use each?",
        "How does Python handle memory management and garbage collection?",
        "Can you explain decorators in Python with a practical example?"
    ],
    'java': [
        "Explain the concept of JVM and how Java achieves platform independence.",
        "What is the difference between an abstract class and an interface in Java?",
        "Describe how multithreading works in Java. Have you used it in a project?",
        "Explain the Java Collections Framework. Which data structures have you used most?"
    ],
    'javascript': [
        "Explain event loop in JavaScript. How does it handle async operations?",
        "What is the difference between let, const, and var in JavaScript?",
        "Describe closure in JavaScript with a practical example.",
        "How does React reconciliation (diffing) work?"
    ],
    'react': [
        "Explain React hooks. When would you use useEffect vs useLayoutEffect?",
        "What are React context API and Redux? When to use each?",
        "Describe virtual DOM and how React optimizes re-renders.",
        "How do you handle forms in React? Controlled vs uncontrolled components."
    ],
    'sql': [
        "Write a SQL query to find second highest salary. Explain indexes impact.",
        "Difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN?",
        "Explain normalization forms. When to denormalize?",
        "What are SQL window functions? Give aggregate example."
    ],
    'data structure': [
        "Compare time/space complexity of array vs linked list operations.",
        "When to use hashmap vs treemap? Real project examples?",
        "Implement LRU cache. What eviction policy would you use?",
        "Explain graph traversal: BFS vs DFS, use cases for each."
    ],
    'project': [
        "Can you walk me through a challenging project? What was hardest part?",
        "How did you deploy your project? What CI/CD tools used?",
        "What metrics did your project achieve? How measured success?",
        "If given more time, what features would you add?"
    ],
    'ml': [
        "Explain overfitting. Techniques to prevent it in models?",
        "Difference between bagging and boosting ensemble methods?",
        "How does transformer architecture work for NLP tasks?",
        "What evaluation metrics for classification vs regression?"
    ],
    'system design': [
        "Design URL shortener. What database schema? Rate limiting?",
        "Design notification system. How handle millions per second?",
        "How would you scale a chat application to 1M users?",
        "Explain CAP theorem. Tradeoffs in distributed systems."
    ],
    'default': [
        "Can you walk me through your most challenging project?",
        "What technical skills are you currently learning?",
        "How do you approach debugging complex issues?",
        "Describe a time you optimized code performance."
    ]
}

def _generate_correct_answer(answer_lower: str) -> str:
    """Generate expected correct answer based on keywords."""
    if 'python' in answer_lower:
        return "A strong Python answer mentions specific libraries used (Django/Flask), real project examples, and deployment details."
    elif 'java' in answer_lower:
        return "A strong Java answer discusses OOP principles, collections framework usage, multithreading, or Spring Boot experience."
    elif 'project' in answer_lower:
        return "A strong project answer uses STAR method: Situation/Task you faced, Action taken, Result achieved with metrics."
    elif 'data structure' in answer_lower:
        return "A strong DS answer includes time/space complexity analysis and when to use vs alternatives."
    elif 'sql' in answer_lower:
        return "A strong SQL answer includes JOIN syntax, indexes for performance, and edge case handling."
    else:
        return "A strong answer includes specific technical details, personal project examples, and structured explanation (problem→approach→result)."

def _generate_improvement(word_count: int, weak_word_count: int, tech_score: float) -> str:
    """Targeted improvement advice."""
    if word_count < 15:
        return "Expand answers to 4-5 sentences with concrete examples from projects or coursework."
    if weak_word_count >= 2:
        return "Build confidence: replace 'I think/maybe' with direct statements like 'This approach works because...'."
    if tech_score < 4:
        return "Deepen technical knowledge - practice implementing concepts in small projects."
    return "Use STAR method (Situation, Task, Action, Result) for behavioral questions to sound more structured."

def _generate_adaptive_question(question: str, answer: str, conversation_history: list = None) -> str:
    """Generate adaptive follow-up based on answer keywords."""
    answer_lower = answer.lower()
    
    # Check history to avoid repetition
    asked_questions = [qa['question'] for qa in (conversation_history or [])]
    
    for topic, questions in TOPIC_FOLLOW_UPS.items():
        if topic in answer_lower:
            for q in questions:
                if q not in asked_questions:
                    return q
            break
    
    # Default fallback
    return random.choice(TOPIC_FOLLOW_UPS['default'])

def _rule_based_fallback(question: str, answer: str, faceDetected: bool, engagementLevel: str, speakingStatus: str, personStatus: str = 'present', conversation_history: list = None) -> Dict[str, Any]:
    """Smart rule-based fallback with structured JSON."""
    words = len(answer.split())
    answer_lower = answer.lower()
    conf = min(10, max(1, words * 0.3))
    comm = min(10, max(1, words * 0.25))
    tech = min(10, max(1, words * 0.4))
    
    # Engagement
    eng = 10 if (personStatus == 'present' and faceDetected and engagementLevel == 'active') else 3
    
    feedback = ""
    strengths = []
    weaknesses = []
    
    weak_words = ['maybe', 'i think', 'not sure']
    weak_count = sum(1 for w in weak_words if w in answer_lower)
    
    status = "incorrect" if tech < 4 else "correct" if tech > 8 else "partial"
    
    if words < 15:
        feedback = "Brief answer. Add more details."
        weaknesses.append("Too short")
    elif words > 100:
        feedback = "Good length but stay more focused."
        weaknesses.append("Too verbose")
    else:
        feedback = "Good attempt. Consider adding specific examples."
        strengths.append("Adequate length")
    
    if weak_count > 0:
        conf -= weak_count * 1.5
        weaknesses.append("Hesitant language")
    
    next_question = _generate_adaptive_question(question, answer, conversation_history)
    
    return {
        "status": status,
        "feedback": feedback,
        "correct_answer": _generate_correct_answer(answer_lower),
        "improvement": _generate_improvement(words, weak_count, tech),
        "next_question": next_question,
        "scores": {
            "confidence": round(conf, 1),
            "communication": round(comm, 1),
            "technical": round(tech, 1),
            "engagement": round(eng, 1)
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": "Practice more detailed responses with concrete examples."
    }

def analyze_interview_response(question: str, answer: str, faceDetected: bool, engagementLevel: str, speakingStatus: str, personStatus: str = 'present', conversation_history: list = None) -> Dict[str, Any]:
    """Analyze interview response using Groq API with adaptive question generation, fallback to rules."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("GROQ_API_KEY missing - using rule-based fallback")
            return _rule_based_fallback(question, answer, faceDetected, engagementLevel, speakingStatus, personStatus, conversation_history)
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Build context from conversation history
        history_context = ""
        if conversation_history:
            history_context = "\\n\\nPrevious conversation (NEVER repeat these questions):\\n"
            for i, qa in enumerate(conversation_history[-5:], 1):
                history_context += f"Q{i}: {qa['question'][:80]}...\\nA{i}: {qa['answer'][:100]}...\\n"
        
        prompt = f"""Question: {question}

Answer: {answer}

Additional context:
Face: {faceDetected}, Engagement: {engagementLevel}, Speaking: {speakingStatus}, Person: {personStatus}
{history_context}

Analyze this specific answer and respond with STRICT JSON ONLY."""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": INTERVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        text = response.choices[0].message.content.strip()
        
        # Robust JSON extraction (handle extra text)
        json_match = re.search(r'\\{.*\\}', text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
        
        if json_match:
            try:
                result = json.loads(json_match.group())
                # Ensure ALL required fields with safe defaults
                result.setdefault("status", "partial")
                result.setdefault("feedback", "Unable to fully evaluate this response.")
                result.setdefault("correct_answer", "A strong answer includes technical details and examples.")
                result.setdefault("improvement", "Provide more specific examples from your experience.")
                result.setdefault("next_question", "Tell me more about your technical experience.")
                result.setdefault("scores", {})
                for key in ["confidence", "communication", "technical", "engagement"]:
                    result["scores"].setdefault(key, 5.0)
                result["scores"] = {k: max(0, min(10, float(v))) for k,v in result["scores"].items()}
                result.setdefault("strengths", [])
                result.setdefault("weaknesses", [])
                result.setdefault("suggestions", "Practice with more detailed examples.")
                return result
            except json.JSONDecodeError:
                print("JSON parse failed - using fallback")
                pass
        
        print("Groq response invalid - using fallback")
        return _rule_based_fallback(question, answer, faceDetected, engagementLevel, speakingStatus, personStatus, conversation_history)
        
    except Exception as e:
        print(f"Groq error: {e} - using fallback")
        return _rule_based_fallback(question, answer, faceDetected, engagementLevel, speakingStatus, personStatus, conversation_history)

