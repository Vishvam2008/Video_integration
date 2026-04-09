import os
import secrets
import logging
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# Try importing the wrapper for mock interviews
try:
    from llm_service_wrapper import analyze_interview_response
except ImportError:
    analyze_interview_response = None
    print("Warning: llm_service_wrapper not found or failed to load. AI analysis will not work.")

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='html', static_url_path='')
CORS(app) # Enable CORS securely

app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Setup logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary to hold session state
sessions = {}

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    # This serves script.js, style.css, etc. directly from html folder
    return app.send_static_file(path)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "production"}), 200

@app.route('/api/start-interview', methods=['POST', 'OPTIONS'])
def start_interview():
    if request.method == 'OPTIONS':
        return make_response('', 200)
    data = request.json or {}
    session_id = data.get('sessionId', f"session_{secrets.token_hex(8)}")
    
    sessions[session_id] = {
        'history': [],
        'current_q_index': 0,
        'total_questions': 5, # configurable
        'scores': [],
        'overall_score': 0
    }
    
    first_question = "Welcome to your mock interview. Could you please introduce yourself and mention your key technical skills?"
    
    logger.info(f"Started new interview session: {session_id}")
    
    return jsonify({
        'sessionId': session_id,
        'question': first_question,
        'progress': 0,
        'totalQuestions': sessions[session_id]['total_questions']
    })

@app.route('/api/analyze-response', methods=['POST', 'OPTIONS'])
def analyze_response():
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    data = request.json or {}
    session_id = data.get('sessionId')
    if not session_id or session_id not in sessions:
        logger.warning(f"Invalid session during analyze_response: {session_id}")
        return jsonify({"error": "Invalid session"}), 400
        
    session = sessions[session_id]
    
    question = data.get('question', '')
    answer = data.get('answerText', '')
    face_detected = data.get('faceDetected', True)
    engagement_level = data.get('engagementLevel', 'active')
    speaking_status = data.get('speakingStatus', 'speaking')
    person_status = data.get('personStatus', 'present')
    
    session['history'].append({"question": question, "answer": answer})
    
    if analyze_interview_response is None:
        analysis = {
            'status': 'partial',
            'feedback': 'Mock feedback (AI system offline). Good effort.',
            'correct_answer': 'A structured response with specific examples.',
            'improvement': 'Be more detailed.',
            'scores': {'confidence': 7, 'communication': 7, 'technical': 7, 'engagement': 8},
            'next_question': 'Can you describe a challenging project you built?',
            'strengths': ['Reasonable fluency'],
            'weaknesses': ['Lacked technical depth'],
            'suggestions': 'Add more technical details.'
        }
    else:
        try:
            analysis = analyze_interview_response(
                question=question,
                answer=answer,
                faceDetected=face_detected,
                engagementLevel=engagement_level,
                speakingStatus=speaking_status,
                personStatus=person_status,
                conversation_history=session['history'][:-1] # Don't pass current Q/A as history yet
            )
        except Exception as e:
            logger.error(f"Error calling analyze_interview_response: {e}")
            return jsonify({"error": "Failed to analyze response"}), 500
    
    if 'scores' in analysis:
        session['scores'].append(analysis['scores'])
    
    session['current_q_index'] += 1
    
    is_final = session['current_q_index'] >= session['total_questions']
    
    response_data = {
        'status': analysis.get('status', 'partial'),
        'feedback': analysis.get('feedback', ''),
        'correct_answer': analysis.get('correct_answer', ''),
        'improvement': analysis.get('improvement', ''),
        'strengths': analysis.get('strengths', []),
        'weaknesses': analysis.get('weaknesses', []),
        'scores': analysis.get('scores', {}),
        'suggestions': analysis.get('suggestions', ''),
        'next_question': analysis.get('next_question', 'Do you have any final thoughts?') if not is_final else '',
        'questionIndex': session['current_q_index'],
        'totalQuestions': session['total_questions'],
        'progress': (session['current_q_index'] / session['total_questions']) * 100,
        'is_final': is_final
    }
    
    return jsonify(response_data)

@app.route('/api/final-report', methods=['POST', 'OPTIONS'])
def final_report():
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    data = request.json or {}
    session_id = data.get('sessionId')
    if not session_id or session_id not in sessions:
        logger.warning(f"Invalid session during final_report: {session_id}")
        return jsonify({"error": "Invalid session"}), 400
        
    session = sessions[session_id]
    
    avg_scores = {"confidence": 0, "communication": 0, "technical": 0, "engagement": 0}
    if session['scores'] and len(session['scores']) > 0:
        for score_dict in session['scores']:
            for k in avg_scores:
                avg_scores[k] += float(score_dict.get(k, 0))
        for k in avg_scores:
            avg_scores[k] = round(avg_scores[k] / len(session['scores']), 1)
            
    # Calculate overall scaled out of 100
    overall = round(sum(avg_scores.values()) / 4 * 10)
    
    if overall >= 80:
        decision = "STRONG HIRE"
    elif overall >= 65:
        decision = "HIRE"
    elif overall >= 50:
        decision = "MODERATE HIRE"
    else:
        decision = "NO HIRE"
        
    return jsonify({
        "overallScore": overall,
        "hireDecision": decision,
        "scores": avg_scores,
        "strengths": ["Completed the AI Mock Interview system test", "Demonstrated clear communication"],
        "weaknesses": ["Consider deepening technical architectures and patterns"],
        "suggestions": "Practice doing more structured technical interviews using the STAR method."
    })

if __name__ == '__main__':
    is_prod = os.environ.get('FLASK_ENV', 'development') == 'production'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    if is_prod:
        try:
            from waitress import serve
            logger.info(f"Starting Waitress production server on {host}:{port}")
            serve(app, host=host, port=port)
        except ImportError:
            logger.error("Waitress is not installed. Please install it using: pip install waitress")
            logger.info("Falling back to Flask development server...")
            app.run(host=host, port=port, debug=False)
    else:
        logger.info(f"Starting Flask development server on {host}:{port}")
        app.run(host=host, port=port, debug=True)
