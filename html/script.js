// API Configuration
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = isLocal ? "http://localhost:5000/api" : "/api";

// State Management (Interview only)


// Interview state
let interviewSessionId = null;
let interviewActive = false;
let interviewProgress = 0;
let recognition = null;
let isListening = false;
let cameraStream = null;
let audioStream = null;
let audioContext = null;
let analyser = null;
let speakingActivity = false;
let facePresence = true;
let engagementActive = true;
let lastInteraction = Date.now();
let faceInterval = null;
let speechInterval = null;
let mirrorModeEnabled = false;

// FEATURE 1: Person absence detection state
let personPresent = false;
let previousFrame = null;
let absenceDetectionInterval = null;
let detectedPersonCount = 0;

// FEATURE 3: TTS state
let ttsEnabled = true;
let dictatedTranscript = '';
let dictationBaseText = '';

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    attachEventListeners();
    initSpeechRecognition();
});



// ==================== FIXED Speech Recognition ====================
function initSpeechRecognition() {
    const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechAPI) {
        alert("⚠ Your browser does not support voice input. Please use Chrome.");
        showNotification("⚠ Your browser does not support voice input. Please use Chrome.", 'error');
        return;
    }
    
    recognition = new SpeechAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isListening = true;
        updateVoiceButtonsUI(true);
        const listeningIndicator = document.getElementById('listeningIndicator');
        if (listeningIndicator) listeningIndicator.textContent = '🎤 Listening (speak continuously)...';
        
        const answerEl = document.getElementById('answerText');
        dictationBaseText = answerEl ? answerEl.value : '';
        if (dictationBaseText.length > 0 && !dictationBaseText.endsWith(' ')) {
            dictationBaseText += ' ';
        }
    };

    recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        const answerEl = document.getElementById('answerText');
        if (answerEl) {
            if (finalTranscript) {
                dictationBaseText += finalTranscript + ' ';
            }
            answerEl.value = dictationBaseText + interimTranscript;
            checkSubmitButtonState();
        }
        
        const listeningIndicator = document.getElementById('listeningIndicator');
        if (listeningIndicator) listeningIndicator.textContent = `🎤 Hearing: "${interimTranscript || finalTranscript}"`;
        engagementActive = true;
        lastInteraction = Date.now();
    };

    recognition.onerror = (event) => {
        console.error("Speech error:", event.error);
        const ind = document.getElementById('listeningIndicator');
        
        if (event.error === "not-allowed") {
            alert("Microphone permission denied. Please allow microphone access.");
            if (ind) ind.textContent = "❌ Permission denied";
        } else if (event.error === "no-speech") {
            // Do not alert on no-speech when continuous is true
            if (ind) ind.textContent = "🔇 No speech detected";
        } else if (event.error === "audio-capture") {
            alert("Microphone not found. Check your device.");
            if (ind) ind.textContent = "🎤 Mic unavailable";
        } else {
            if (ind) ind.textContent = `❌ Error: ${event.error}`;
        }
        isListening = false;
        updateVoiceButtonsUI(false);
    };

    recognition.onend = () => {
        isListening = false;
        updateVoiceButtonsUI(false);
        const ind = document.getElementById('listeningIndicator');
        if (ind) ind.textContent = '';
    };
}



function stopListening() {
    isListening = false;
    if (recognition) {
        try { recognition.stop(); } catch(e) {}
    }
    stopMicrophone();
    updateVoiceButtonsUI(false);
    const listeningIndicator = document.getElementById('listeningIndicator');
    if (listeningIndicator) listeningIndicator.textContent = '';
}

function updateVoiceButtonsUI(listening) {
    const micBtn = document.getElementById('micToggleBtn');
    const voiceBtn = document.getElementById('voiceBtn');

    if (micBtn) {
        micBtn.textContent = listening ? '🎤 Listening...' : '🎤 Voice Input';
        micBtn.classList.toggle('listening', listening);
    }
    if (voiceBtn) {
        voiceBtn.textContent = listening ? '🎤 Listening...' : '🎤 Voice Answer';
        voiceBtn.classList.toggle('listening', listening);
    }
}

function checkSubmitButtonState() {
    const submitBtn = document.getElementById('submitAnswerBtn');
    const answerEl = document.getElementById('answerText');
    if (submitBtn && answerEl) {
        submitBtn.disabled = !interviewActive || answerEl.value.trim().length === 0;
    }
}

// ==================== FEATURE 3: Text-to-Speech (AI Speaks) ====================
function speakText(text, onEnd = null) {
    if (!ttsEnabled || !window.speechSynthesis) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    if (onEnd) utterance.onend = onEnd;

    // Small delay to ensure cancel completes
    setTimeout(() => {
        window.speechSynthesis.speak(utterance);
    }, 100);
}

function speakQuestion(questionText) {
    speakText(questionText);
}

function speakFeedback(feedbackText) {
    // Speak a shortened version to avoid very long TTS
    const shortened = feedbackText.length > 300 ? feedbackText.substring(0, 300) + '...' : feedbackText;
    speakText(shortened);
}

function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const btn = document.getElementById('ttsToggleBtn');
    if (btn) {
        btn.textContent = ttsEnabled ? '🔊 AI Voice ON' : '🔇 AI Voice OFF';
        btn.classList.toggle('active', ttsEnabled);
    }
    if (!ttsEnabled) {
        window.speechSynthesis?.cancel();
    }
    showNotification(ttsEnabled ? '🔊 AI will read questions aloud' : '🔇 AI voice muted', 'info');
}

// ==================== Theme Management ====================
function loadTheme() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeToggle();
    }
}

document.getElementById('themeToggle')?.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    updateThemeToggle();
});

function updateThemeToggle() {
    const icon = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = icon;
}



// ==================== Event Listeners ====================
function attachEventListeners() {
    // Interview Controls
    document.getElementById('startCameraBtn')?.addEventListener('click', startCamera);
    document.getElementById('micToggleBtn')?.addEventListener('click', toggleVoiceInput);
    document.getElementById('startInterviewBtn')?.addEventListener('click', startInterview);
    document.getElementById('submitAnswerBtn')?.addEventListener('click', submitAnswer);
    document.getElementById('mirrorModeBtn')?.addEventListener('click', toggleMirrorMode);
    document.getElementById('answerText')?.addEventListener('input', updateEngagement);
    document.getElementById('voiceBtn')?.addEventListener('click', toggleVoiceInput);
    document.getElementById('ttsToggleBtn')?.addEventListener('click', toggleTTS);

    // Enable submit when typing
    document.getElementById('answerText')?.addEventListener('input', checkSubmitButtonState);
    
    // ANTI-CHEAT: Disable copy/paste/cut/right-click
    const answerEl = document.getElementById('answerText');
    if (answerEl) {
        ['paste', 'copy', 'cut'].forEach(event => {
            answerEl.addEventListener(event, e => e.preventDefault());
        });
        document.addEventListener('contextmenu', e => {
            if (e.target === answerEl || answerEl.contains(e.target)) e.preventDefault();
        });
        
        // Suspicious input detection (fast typing)
        let typingStart = 0;
        let lastLength = 0;
        answerEl.addEventListener('input', () => {
            const now = Date.now();
            const currentLength = answerEl.value.length;
            if (now - typingStart < 1000 && currentLength - lastLength > 20) {
                showNotification('⚠ Suspicious input detected. Please answer manually.', 'error');
                answerEl.value = answerEl.value.substring(0, lastLength); // Revert
            }
            typingStart = now;
            lastLength = currentLength;
            updateEngagement();
            checkSubmitButtonState();
        });
    }
}

function updateEngagement() {
    engagementActive = true;
    lastInteraction = Date.now();
}

// ==================== FEATURE 1: Person Absence Detection ====================
function startPersonDetection() {
    if (absenceDetectionInterval) clearInterval(absenceDetectionInterval);
    previousFrame = null;

    absenceDetectionInterval = setInterval(() => {
        const result = detectPersonPresence();
        personPresent = result.present;
        detectedPersonCount = result.count || 0;
        facePresence = personPresent;
        engagementActive = personPresent ? engagementActive : false;
        updateStatusChips();
    }, 1500);
}

function detectPersonPresence() {
    const video = document.getElementById('cameraPreview');
    if (!video || !video.videoWidth || !video.videoHeight) {
        return { present: false, count: 0, reason: 'no-stream' };
    }

    const canvas = document.createElement('canvas');
    const size = 100;
    canvas.width = size; canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, size, size);
    const imageData = ctx.getImageData(0, 0, size, size);
    const data = imageData.data;
    const totalPixels = size * size;

    // Brightness check
    let totalBrightness = 0;
    for (let i = 0; i < data.length; i += 4) totalBrightness += (data[i] + data[i+1] + data[i+2]) / 3;
    const avgBrightness = totalBrightness / totalPixels;
    if (avgBrightness < 15) return { present: false, count: 0, reason: 'too-dark' };

    // Color variance
    let sR = 0, sG = 0, sB = 0, sR2 = 0, sG2 = 0, sB2 = 0;
    for (let i = 0; i < data.length; i += 4) {
        sR += data[i]; sG += data[i+1]; sB += data[i+2];
        sR2 += data[i]*data[i]; sG2 += data[i+1]*data[i+1]; sB2 += data[i+2]*data[i+2];
    }
    const vR = (sR2/totalPixels) - Math.pow(sR/totalPixels, 2);
    const vG = (sG2/totalPixels) - Math.pow(sG/totalPixels, 2);
    const vB = (sB2/totalPixels) - Math.pow(sB/totalPixels, 2);
    const colorVariance = vR + vG + vB;
    if (colorVariance < 50) return { present: false, count: 0, reason: 'blank' };

    // Skin-tone grid for multi-person detection
    const gridN = 10;
    const cellW = size / gridN, cellH = size / gridN;
    const skinGrid = [];
    for (let gy = 0; gy < gridN; gy++) {
        for (let gx = 0; gx < gridN; gx++) {
            let cellSkin = 0, cellTotal = 0;
            for (let y = Math.floor(gy*cellH); y < Math.floor((gy+1)*cellH); y++) {
                for (let x = Math.floor(gx*cellW); x < Math.floor((gx+1)*cellW); x++) {
                    const idx = (y * size + x) * 4;
                    const r = data[idx], g = data[idx+1], b = data[idx+2];
                    const yy = 0.299*r + 0.587*g + 0.114*b;
                    const cb = 128 - 0.169*r - 0.331*g + 0.5*b;
                    const cr = 128 + 0.5*r - 0.419*g - 0.081*b;
                    if (cb >= 77 && cb <= 127 && cr >= 133 && cr <= 173 && yy > 80) cellSkin++;
                    cellTotal++;
                }
            }
            skinGrid.push(cellTotal > 0 ? cellSkin / cellTotal : 0);
        }
    }

    // Flood-fill to find distinct skin clusters
    const vis = new Set();
    const clusters = [];
    for (let i = 0; i < gridN * gridN; i++) {
        if (!vis.has(i) && skinGrid[i] >= 0.3) {
            const stack = [i]; let sz = 0;
            while (stack.length > 0) {
                const ci = stack.pop();
                if (vis.has(ci) || skinGrid[ci] < 0.3) continue;
                vis.add(ci); sz++;
                const cx = ci % gridN, cy = Math.floor(ci / gridN);
                if (cx > 0) stack.push(ci - 1);
                if (cx < gridN-1) stack.push(ci + 1);
                if (cy > 0) stack.push(ci - gridN);
                if (cy < gridN-1) stack.push(ci + gridN);
            }
            if (sz >= 3) clusters.push(sz);
        }
    }

    // Motion detection
    let motionDetected = true;
    const currentFrame = new Uint8Array(data.length);
    currentFrame.set(data);
    if (previousFrame) {
        let diffSum = 0;
        for (let i = 0; i < data.length; i += 4) diffSum += Math.abs(currentFrame[i] - previousFrame[i]);
        motionDetected = (diffSum / totalPixels) > 2;
    }
    previousFrame = currentFrame;

    const totalSkinCells = skinGrid.filter(c => c >= 0.3).length;
    const hasSignal = totalSkinCells > 3 || (motionDetected && colorVariance > 200);
    const personCount = hasSignal ? Math.max(1, clusters.length) : 0;

    return { present: hasSignal, count: personCount };
}



// ==================== Interview Functions ====================
async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('cameraPreview');
        if (video) {
            video.srcObject = cameraStream;
            video.style.transform = 'scaleX(1)';
            video.play();
        }

        facePresence = true;
        personPresent = true;
        const statusEl = document.getElementById('cameraStatus');
        if (statusEl) statusEl.textContent = '✅ Camera active';

        const startBtn = document.getElementById('startInterviewBtn');
        if (startBtn) startBtn.disabled = false;

        // FEATURE 1: Start person absence detection
        startPersonDetection();
        showNotification('📹 Camera ready! Person detection active.', 'success');
    } catch (err) {
        console.error('Camera error:', err);
        showNotification('Camera error: ' + err.message, 'error');
    }
}

function toggleMirrorMode() {
    mirrorModeEnabled = !mirrorModeEnabled;
    const video = document.getElementById('cameraPreview');
    if (video) video.style.transform = mirrorModeEnabled ? 'scaleX(-1)' : 'scaleX(1)';
    const btn = document.getElementById('mirrorModeBtn');
    if (btn) btn.textContent = mirrorModeEnabled ? 'Mirror ON' : 'Mirror OFF';
}



async function toggleMicrophone() {
    if (audioStream) { stopMicrophone(); return; }
    try {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(audioStream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        speechInterval = setInterval(checkSpeechActivity, 200);
        const statusEl = document.getElementById('cameraStatus');
        if (statusEl) statusEl.textContent = '✅ Mic active';
    } catch (err) {
        showNotification('Mic error: ' + err.message, 'error');
    }
}

function stopMicrophone() {
    if (audioStream) audioStream.getTracks().forEach(t => t.stop());
    if (audioContext) { try { audioContext.close(); } catch(e) {} }
    if (speechInterval) clearInterval(speechInterval);
    speakingActivity = false;
    audioStream = null; audioContext = null; analyser = null;
}

function checkSpeechActivity() {
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    speakingActivity = Math.max(...data) > 30;
    updateStatusChips();
}

function toggleVoiceInput() {
    if (isListening) {
        stopListening();
        return;
    }
    
    if (!recognition) {
        initSpeechRecognition();
        showNotification('⚠️ Voice init failed', 'error');
        return;
    }
    
    // Strict user gesture requirement
    try {
        recognition.start();
    } catch (error) {
        console.error('Voice start error:', error);
        showNotification(`Mic error: ${error.message}`, 'error');
    }
}



function updateVoiceButtonsUI(listening) {
    const micBtn = document.getElementById('micToggleBtn');
    const voiceBtn = document.getElementById('voiceBtn');

    if (micBtn) {
        micBtn.textContent = listening ? '🎤 Listening...' : '🎤 Voice Input';
        micBtn.classList.toggle('listening', listening);
    }
    if (voiceBtn) {
        voiceBtn.textContent = listening ? '🎤 Listening...' : '🎤 Voice Answer';
        voiceBtn.classList.toggle('listening', listening);
    }
}

// ==================== Status Chips (ENHANCED with Person Status) ====================
function updateStatusChips() {
    const faceEl = document.getElementById('faceStatus');
    const engEl = document.getElementById('engagementStatus');
    const speechEl = document.getElementById('speechStatus');
    const personEl = document.getElementById('personStatus');

    // Person status chip with multi-person detection
    if (personEl) {
        if (detectedPersonCount === 0 || !personPresent) {
            personEl.textContent = '\ud83e\uddd1 Person: \u274c Absent';
            personEl.className = 'status-chip person-absent';
        } else if (detectedPersonCount > 1) {
            personEl.textContent = '\ud83e\uddd1 Person: \u26a0\ufe0f Multiple (' + detectedPersonCount + ')';
            personEl.className = 'status-chip person-absent';
        } else {
            personEl.textContent = '\ud83e\uddd1 Person: \u2705 Single Person';
            personEl.className = 'status-chip person-present';
        }
    }

    if (faceEl) {
        if (facePresence) {
            faceEl.textContent = '👤 Face: ✅ Detected';
            faceEl.className = 'status-chip status-positive';
        } else {
            faceEl.textContent = '👤 Face: ❌ Not Found';
            faceEl.className = 'status-chip status-negative';
        }
    }

    if (engEl) {
        const active = engagementActive && personPresent;
        engEl.textContent = `💡 Engagement: ${active ? 'Active' : 'Low'}`;
        engEl.className = `status-chip ${active ? 'status-positive' : 'status-negative'}`;
    }

    if (speechEl) {
        speechEl.textContent = `🎙️ Voice: ${speakingActivity ? 'Active' : 'Silent'}`;
        speechEl.className = `status-chip ${speakingActivity ? 'status-positive' : ''}`;
    }

    if (Date.now() - lastInteraction > 5000) engagementActive = false;
}

// ==================== Interview Flow ====================
async function startInterview() {
    if (!cameraStream) return showNotification('Start camera first', 'error');

    showLoader(true);
    try {
        const res = await fetch(`${API_BASE_URL}/start-interview`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sessionId: interviewSessionId || `session_${Date.now()}`})
        });
        let data;
        try {
            data = await res.json();
        } catch (e) {
            throw new Error('Invalid JSON from start-interview');
        }
        interviewSessionId = data.sessionId;
        interviewProgress = data.progress || 0;

        const questionEl = document.getElementById('interviewQuestion');
        if (questionEl) questionEl.textContent = data.question;

        const progressEl = document.getElementById('interviewProgress');
        if (progressEl) progressEl.textContent = `Q1/${data.totalQuestions}`;

        const progressBar = document.getElementById('interviewProgressBar');
        if (progressBar) progressBar.style.width = `${data.progress}%`;

        const pctEl = document.getElementById('interviewProgressPct');
        if (pctEl) pctEl.textContent = `${Math.round(data.progress)}%`;

        interviewActive = true;

        const submitBtn = document.getElementById('submitAnswerBtn');
        if (submitBtn) submitBtn.disabled = false;

        showNotification('🚀 Interview started! Answer clearly.', 'success');

        // FEATURE 3: AI reads the first question aloud
        speakQuestion(data.question);

    } catch (err) {
        console.error('Start interview error:', err);
        showNotification('Backend error. Is server running?', 'error');
    }
    showLoader(false);
}

async function submitAnswer() {
    if (!interviewActive) return showNotification('Start interview first', 'error');

    const answerEl = document.getElementById('answerText');
    const answer = answerEl ? answerEl.value.trim() : '';
    if (!answer || answer.length < 5) return showNotification('Answer too short (min 5 chars)', 'error');

    // Stop listening while processing
    if (isListening) stopListening();

    const submitBtn = document.getElementById('submitAnswerBtn');
    showLoader(true, 'submitAnswerBtn');
    lastInteraction = Date.now();

    const currentQuestionEl = document.getElementById('interviewQuestion');
    const payload = {
        sessionId: interviewSessionId,
        questionIndex: interviewProgress,
        question: currentQuestionEl ? currentQuestionEl.textContent : '',
        answerText: answer,
        faceDetected: facePresence,
        engagementLevel: engagementActive ? 'active' : 'low',
        speakingStatus: speakingActivity ? 'speaking' : 'silent',
        // FEATURE 1: Send person status to backend
        personStatus: personPresent ? 'present' : 'absent'
    };

    try {
        const res = await fetch(`${API_BASE_URL}/analyze-response`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        let result;
        try {
            result = await res.json();
        } catch (e) {
            throw new Error('Invalid JSON from analyze-response');
        }

        if (answerEl) answerEl.value = '';
        displayFullFeedback(result);

        // FEATURE 3: AI reads the feedback aloud
        if (result.feedback) speakFeedback(result.feedback);

        if (result.is_final) {
            try {
                const finalRes = await fetch(`${API_BASE_URL}/final-report`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sessionId: interviewSessionId})
                });
                let finalData;
                try {
                    finalData = await finalRes.json();
                } catch (e) {
                    console.error('Final report JSON error:', e);
                    showNotification('Final report invalid', 'error');
                    return;
                }
                showFinalReport(finalData);
            } catch (finalErr) {
                console.error('Final report error:', finalErr);
                showNotification('Could not load final report', 'error');
            }
            interviewActive = false;
        } else {
            interviewProgress = result.questionIndex;
            const questionEl = document.getElementById('interviewQuestion');
            if (questionEl) questionEl.textContent = result.next_question;

            const progressEl = document.getElementById('interviewProgress');
            if (progressEl) progressEl.textContent = `Q${result.questionIndex + 1}/${result.totalQuestions || 10}`;

            const progressBar = document.getElementById('interviewProgressBar');
            if (progressBar) progressBar.style.width = `${result.progress}%`;

            const pctEl = document.getElementById('interviewProgressPct');
            if (pctEl) pctEl.textContent = `${Math.round(result.progress)}%`;

            // FEATURE 3: AI reads the next question aloud
            if (result.next_question) {
                // Wait a beat after feedback before reading the next question
                setTimeout(() => speakQuestion(result.next_question), 1500);
            }
        }
    } catch (err) {
        showNotification('Analysis error. Check console.', 'error');
        console.error('Submit answer error:', err);
    } finally {
        showLoader(false, 'submitAnswerBtn');
    }
}

// ==================== Feedback Display ====================
function displayFullFeedback(result) {
    const feedbackEl = document.getElementById('feedbackContent');
    if (!feedbackEl) return;

let statusIcon = '';
    if (result.status === 'correct') statusIcon = '✔';
    else if (result.status === 'incorrect') statusIcon = '❌';
    else if (result.status === 'partial') statusIcon = '⚠';
    
    let html = `
        <div class="status-display" style="font-size: 2em; text-align: center; margin: 10px 0;">
            ${statusIcon} <strong>${result.status?.toUpperCase() || 'PARTIAL'}</strong>
        </div>
        <div class="feedback-item"><strong>Feedback:</strong> ${result.feedback || 'N/A'}</div>
        ${result.correct_answer ? `<div class="feedback-item"><strong>Correct Answer:</strong> ${result.correct_answer}</div>` : ''}
        ${result.improvement ? `<div class="feedback-item improvement"><strong>Improvement:</strong> ${result.improvement}</div>` : ''}
        ${result.strengths?.length ? `<div class="feedback-list"><strong>Strengths:</strong><ul>${result.strengths.map(s => `<li>${s}</li>`).join('')}</ul></div>` : ''}
        ${result.weaknesses?.length ? `<div class="feedback-list"><strong>Weaknesses:</strong><ul>${result.weaknesses.map(w => `<li>${w}</li>`).join('')}</ul></div>` : ''}
        <div class="score-bars">
            <div>Confidence: ${result.scores?.confidence || 0}/10</div>
            <div>Technical: ${result.scores?.technical || 0}/10</div>
            <div>Engagement: ${result.scores?.engagement || 0}/10</div>
        </div>
        <div class="suggestion">${result.suggestions || ''}</div>
    `;
    feedbackEl.innerHTML = html;

    const scoreSection = document.getElementById('scoreSection');
    if (scoreSection) {
        scoreSection.style.display = 'block';
        updateScoreBar('confScore', result.scores?.confidence || 0);
        updateScoreBar('techScore', result.scores?.technical || 0);
        updateScoreBar('engScore', result.scores?.engagement || 0);
    }
}

function updateScoreBar(id, score) {
    const el = document.getElementById(id);
    if (el) {
        el.setAttribute('data-score', score);
        el.style.background = `linear-gradient(90deg, var(--success) ${score * 10}%, var(--border) ${score * 10}%)`;
    }
}

function showFinalReport(data) {
    const feedbackEl = document.getElementById('feedbackContent');
    const questionEl = document.getElementById('interviewQuestion');

    if (questionEl) questionEl.textContent = '🎉 Interview Complete!';
    if (!feedbackEl) return;

    const score = data.overallScore || 0;
    const hire = data.hireDecision || 'N/A';

    feedbackEl.innerHTML = `
        <div class="final-score" style="font-size: 3em; text-align: center; margin: 20px 0;">
            ${score}/100
        </div>
        <div class="hire-badge" style="font-size: 1.5em; text-align: center; padding: 10px; border-radius: 8px; margin: 10px 0;">
            ${hire}
        </div>
        <div><strong>Scores:</strong></div>
        <div class="score-bars">
            <div>Confidence: ${data.scores?.confidence || 0}</div>
            <div>Communication: ${data.scores?.communication || 0}</div>
            <div>Technical: ${data.scores?.technical || 0}</div>
            <div>Engagement: ${data.scores?.engagement || 0}</div>
        </div>
        ${data.strengths?.length ? `<div class="feedback-list"><strong>Strengths:</strong><ul>${data.strengths.map(s => `<li>${s}</li>`).join('')}</ul></div>` : ''}
        ${data.weaknesses?.length ? `<div class="feedback-list"><strong>Areas to Improve:</strong><ul>${data.weaknesses.map(w => `<li>${w}</li>`).join('')}</ul></div>` : ''}
        <div class="suggestion"><strong>Next Steps:</strong> ${data.suggestions || ''}</div>
    `;

    // FEATURE 3: Speak final result
    speakText(`Interview complete! Your final score is ${score} out of 100. Decision: ${hire}`);
    showNotification(`Final Score: ${score} - ${hire}`, 'success');
}

// ==================== UI Helpers ====================
function showLoader(show = false, buttonId = null) {
    if (buttonId) {
        const btn = document.getElementById(buttonId);
        if (btn) {
            if (show) {
                btn.disabled = true;
                btn.innerHTML = '<span class="loader"></span> Analyzing...';
            } else {
                btn.disabled = false;
                btn.innerHTML = '📤 Submit & Get Feedback';
            }
        }
    }
}

function updateProgressBar(progress) {
    const bar = document.getElementById('interviewProgressBar');
    if (bar) bar.style.width = `${progress}%`;
}



function showNotification(msg, type = 'info') {
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = msg;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 4000);
}

function validateForm() { return true; }
