"""
Career Profile Evaluation - Python Backend with AI Mock Interview
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from datetime import datetime
import os
from llm_service_wrapper import analyze_interview_response
import random

# Serve frontend from html/ directory
app = Flask(__name__, static_folder='html', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('html', 'index.html')

# Storage for profiles (unchanged)
PROFILES_DIR = 'submitted_profiles'
if not os.path.exists(PROFILES_DIR):
    os.makedirs(PROFILES_DIR)

# Interview configuration — first question only (rest are adaptive)
FIRST_QUESTION = "Tell me about yourself and your background."
DEFAULT_TOTAL_QUESTIONS = 10

# Session state (in-memory for demo)
sessions = {}

def get_or_create_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            'question_index': 0,
            'scores': {'confidence': [], 'communication': [], 'technical': [], 'engagement': []},
            'answers': [],
'conversation_history': [],
            'asked_questions': [],
            'total_questions': DEFAULT_TOTAL_QUESTIONS
        }
    return sessions[session_id]

def compute_final_scores(session):
    scores = session['scores']
    final = {}
    for category, values in scores.items():
        final[category] = round(sum(values)/len(values), 1) if values else 5.0
    
    # Weighted overall (0-10 scale *10 for %)
    weights = {'confidence': 0.25, 'communication': 0.25, 'technical': 0.35, 'engagement': 0.15}
    overall = sum(final[k] * w for k, w in weights.items()) * 10
    final['overall'] = round(overall, 1)
    return final

def get_hire_decision(overall_score):
    if overall_score >= 85:
        return "Strong Hire"
    elif overall_score >= 70:
        return "Moderate Hire"
    else:
        return "Needs Improvement"

# Existing profile functions (unchanged)
def analyze_profile(profile):
    personal_info = profile.get('personalInfo', {})
    projects = profile.get('projects', [])
    cgpa = float(personal_info.get('currentCGPA', 0))
    project_count = len(projects)
    skills_avg = calculate_skills_average(personal_info)
    hireability_score = calculate_hireability(cgpa, project_count, skills_avg)
    
    analysis = {
        'hirabilityScore': hireability_score,
        'domainFit': personal_info.get('domains', ['General'])[0] if personal_info.get('domains') else 'General',
        'recommendedRoles': generate_role_recommendations(personal_info),
        'strengths': identify_strengths(personal_info),
        'areasForImprovement': identify_improvements(personal_info),
        'nextSteps': generate_next_steps(personal_info)
    }
    return analysis

def calculate_skills_average(personal_info):
    skills = [float(personal_info.get(k, 3)) for k in ['dsa', 'webDev', 'mlAi', 'dbms', 'os', 'networking']]
    return sum(skills) / len(skills)

def calculate_hireability(cgpa, projects, skills):
    score = min(30, (cgpa / 10) * 30) + min(35, (projects / 5) * 35) + min(35, (skills / 5) * 35)
    return round(score, 1)

def generate_role_recommendations(personal_info):
    domains = personal_info.get('domains', [])
    roles = {
        'SDE': ['Software Engineer', 'Full Stack Developer', 'Backend Engineer'],
        'AI/ML': ['Machine Learning Engineer', 'AI Researcher', 'Data Scientist'],
        'Data Science': ['Data Scientist', 'Analytics Engineer', 'Business Analyst'],
        'Cybersecurity': ['Security Engineer', 'Penetration Tester', 'Security Analyst'],
        'Full Stack': ['Full Stack Developer', 'Web Developer', 'Frontend Engineer'],
        'DevOps': ['DevOps Engineer', 'Cloud Engineer', 'Infrastructure Engineer']
    }
    recommended = []
    for domain in domains:
        if domain in roles:
            recommended.extend(roles[domain])
    return list(set(recommended))[:5]

def identify_strengths(personal_info):
    strengths = []
    cgpa = float(personal_info.get('currentCGPA', 0))
    if cgpa >= 8.5: strengths.append('High CGPA')
    for skill in ['dsa', 'webDev', 'mlAi']:
        if float(personal_info.get(skill, 0)) >= 4: strengths.append(f'Strong {skill} skills')
    if personal_info.get('linkedinUrl'): strengths.append('Professional online presence')
    return strengths

def identify_improvements(personal_info):
    improvements = []
    cgpa = float(personal_info.get('currentCGPA', 0))
    if cgpa < 7.0: improvements.append(f'Improve academic performance (Current: {cgpa})')
    for skill in ['dsa', 'webDev', 'mlAi', 'dbms']:
        if float(personal_info.get(skill, 0)) <= 2: improvements.append(f'Build {skill} skills')
    if not personal_info.get('githubUrl'): improvements.append('Create GitHub portfolio')
    return improvements

def generate_next_steps(personal_info):
    return [
        'Complete 100+ LeetCode problems',
        'Build 2-3 real-world projects',
        'Contribute to open-source projects',
        'Network with industry professionals',
        'Prepare for technical interviews'
    ]

# Existing unchanged endpoints
@app.route('/api/submit-profile', methods=['POST'])
def submit_profile():
    try:
        data = request.get_json()
        if not data or 'personalInfo' not in data:
            return jsonify({'error': 'Missing personalInfo'}), 400
        
        personal_info = data['personalInfo']
        full_name = personal_info.get('fullName', 'Unknown')
        email = personal_info.get('email', 'Unknown')
        
        profile = {
            'timestamp': datetime.now().isoformat(),
            'personalInfo': personal_info,
            'projects': data.get('projects', []),
            'internships': data.get('internships', []),
            'semesters': data.get('semesters', []),
            'companies': data.get('companies', [])
        }
        
        filename = f"{PROFILES_DIR}/{email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(profile, f, indent=2)
        
        analysis = analyze_profile(profile)
        return jsonify({
            'success': True,
            'message': f'Profile submitted successfully for {full_name}',
            'email': email,
            'analysis': analysis,
            'profileId': filename
        }), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-profile', methods=['POST'])
def analyze_profile_endpoint():
    try:
        data = request.get_json()
        analysis = analyze_profile(data)
        return jsonify(analysis), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Backend is running with AI Interview!'}), 200

@app.route('/api/profiles', methods=['GET'])
def get_all_profiles():
    profiles = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(PROFILES_DIR, filename), 'r') as f:
                profiles.append(json.load(f))
    return jsonify({'profiles': profiles, 'count': len(profiles)}), 200

# Enhanced Interview Endpoints
@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    data = request.get_json(silent=True) or {}
    session_id = data.get('sessionId', f'session_{int(datetime.now().timestamp())}')
    session = get_or_create_session(session_id)
    
    # Always start with the intro question
    question = FIRST_QUESTION
    return jsonify({
        'success': True,
        'sessionId': session_id,
        'questionIndex': session['question_index'],
        'question': question,
        'totalQuestions': session['total_questions'],
        'progress': round((session['question_index'] / session['total_questions']) * 100, 1)
    }), 200

@app.route('/api/analyze-response', methods=['POST'])
def analyze_response():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        answer_text = data.get('answerText', '').strip()
        if len(answer_text) < 5:
            return jsonify({'success': False, 'error': 'Answer too short (min 5 chars)'}), 400
        question_index = data.get('questionIndex', 0)
        current_question = data.get('question', 'Unknown question')
        face_detected = data.get('faceDetected', True)
        engagement_level = data.get('engagementLevel', 'active')
        speaking_status = data.get('speakingStatus', 'silent')
        person_status = data.get('personStatus', 'present')
        
        if not session_id:
            return jsonify({'error': 'Missing sessionId'}), 400
        
        session = get_or_create_session(session_id)
        
        # Build conversation history for adaptive question generation
        conversation_history = session.get('conversation_history', [])
        
        # LLM analysis with conversation context for adaptive questions
        llm_result = analyze_interview_response(
            current_question, answer_text,
            face_detected, engagement_level, speaking_status,
            person_status, conversation_history
        )
        
        # ANTI-REPETITION: Regenerate if duplicate question
        max_retries = 2
        retry_count = 0
        while retry_count < max_retries:
            next_question_candidate = llm_result.get('next_question', 'Tell me more.')
            if next_question_candidate not in session.get('asked_questions', []):
                break
            # Regenerate
            print(f"Regenerating question (duplicate detected): {next_question_candidate}")
            llm_result = analyze_interview_response(
                current_question, answer_text,
                face_detected, engagement_level, speaking_status,
                person_status, conversation_history
            )
            retry_count += 1
        else:
            # Fallback generic questions
            generic_fallbacks = [
                "Can you walk me through a challenging project?",
                "What technical skills are you currently learning?",
                "How do you approach debugging complex issues?"
            ]
            next_question_candidate = random.choice(generic_fallbacks)
        
        llm_result['next_question'] = next_question_candidate
        session['asked_questions'].append(next_question_candidate)
        
        # If person was absent, penalize engagement and add feedback
        if person_status == 'absent':
            llm_result['scores']['engagement'] = max(0, llm_result['scores']['engagement'] - 3)
            if 'You were not visible' not in llm_result.get('feedback', ''):
                llm_result['feedback'] = llm_result.get('feedback', '') + ' Warning: You were not visible during the interview. Maintain presence.'
            if 'Not visible on camera' not in str(llm_result.get('weaknesses', [])):
                llm_result.setdefault('weaknesses', []).append('Not visible on camera during response')
        
        # Accumulate scores
        for cat in ['confidence', 'communication', 'technical', 'engagement']:
            session['scores'][cat].append(llm_result['scores'][cat])
        
        # Store answer and conversation history for adaptive questions
        session['answers'].append(answer_text)
        session['conversation_history'].append({
            'question': current_question,
            'answer': answer_text
        })
        # Add current question to asked_questions
        session['asked_questions'].append(current_question)
        session['question_index'] += 1
        
        # next_question already handled above with anti-repetition
        answers_given = len(session['answers'])
        if answers_given >= session['total_questions']:
            next_question = None
        else:
            next_question = llm_result['next_question']
        
        response = {
            'success': True,
            'sessionId': session_id,
            'questionIndex': session['question_index'],
            'feedback': llm_result['feedback'],
            'next_question': next_question,
            'scores': llm_result['scores'],
            'strengths': llm_result.get('strengths', []),
            'weaknesses': llm_result.get('weaknesses', []),
            'suggestions': llm_result.get('suggestions', 'Practice more.'),
            'progress': round((answers_given / session['total_questions']) * 100, 1),
            'is_final': next_question is None
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Analyze error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/final-report', methods=['POST'])
def final_report():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = sessions[session_id]
        final_scores = compute_final_scores(session)
        hire_decision = get_hire_decision(final_scores['overall'])
        
        report = {
            'success': True,
            'sessionId': session_id,
            'finalReport': True,
            'scores': final_scores,
            'overallScore': final_scores['overall'],
            'hireDecision': hire_decision,
            'strengths': session.get('strengths', []),
            'weaknesses': session.get('weaknesses', []),
            'suggestions': "Review your performance and practice weak areas.",
            'questionCount': len(session['answers']),
            'avgAnswerLength': round(sum(len(a.split()) for a in session['answers'])/len(session['answers']), 1) if session['answers'] else 0
        }
        
        return jsonify(report), 200
        
    except Exception as e:
        print(f"Final report error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("AI Mock Interview Backend Ready!")
    print("Open http://localhost:5000 in your browser")
    print("Set GROQ_API_KEY for LLM (optional - rule-based fallback works)")
    app.run(debug=True, port=5000)
