# Video Integration - AI Mock Interview Platform 🚀

Full-stack AI-powered mock interview system with camera detection, real-time analysis, and hiring recommendations.

## 🎯 Features
- 🎥 Real-time face/engagement detection
- 🗣️ Voice-to-text transcription
- 🤖 Groq AI-powered interview analysis
- 📊 Instant feedback & scores
- 📈 Final hireability report
- ✅ Production-ready Flask + Waitress deployment

## 🏗️ Architecture
```
html/           # Frontend (vanilla JS + camera)
├── index.html
├── script.js
└── style.css

app.py          # Flask API + static serving
requirements.txt
llm_service_wrapper.py  # AI interview engine
groq_llm_backend.py     # Dataset analysis
```

## 🚀 Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:** (copy `.env.example` → `.env`)
```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY
```

3. **Run development server:**
```bash
python app.py
```

4. **Open browser:** `http://localhost:5000`

## ☁️ Render Deployment (Production)

### Manual Dashboard Setup:
1. **Build Command:** `pip install -r requirements.txt`
2. **Start Command:** `waitress-serve --host=0.0.0.0 --port=$PORT app:app`
3. **Environment Variables:**
   ```
   FLASK_ENV=production
   FLASK_SECRET_KEY=your-64-char-secret
   GROQ_API_KEY=your-groq-key
   ```

### Automated Git Deploys:
Connect Git repo → use `render.yaml`

### Verify Deployment:
```
https://your-service.onrender.com/api/health
→ Should return: {"status": "healthy", "service": "production"}
```

## 🔧 API Endpoints

| Method | Endpoint              | Description                  |
|--------|-----------------------|------------------------------|
| GET    | `/api/health`         | Health check                 |
| POST   | `/api/start-interview`| Initialize interview session |
| POST   | `/api/analyze-response`| AI analysis of answer       |
| POST   | `/api/final-report`   | Generate final score report  |

## 🧪 Testing

**Local Production Test:**
```bash
# Terminal 1
FLASK_ENV=production python app.py

# Test endpoints
curl http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/start-interview
```

## 🔍 Troubleshooting Render "Backend Deactivated"

1. **Check Logs:** Render dashboard → Logs tab
2. **Common fixes:**
   - Missing `GROQ_API_KEY` → AI fails silently
   - Wrong Start Command → Use Procfile or `waitress-serve`
   - Port binding → Must use `$PORT`
3. **Health Check:** `/api/health` must return 200 JSON

## 📊 Status Check

✅ **Code:** All routes, CORS, static serving, production server  
✅ **Local:** Full workflow working  
🔄 **Render:** Check dashboard logs & redeploy  

## 📝 License
MIT - Deploy freely!

