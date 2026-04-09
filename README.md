<<<<<<< HEAD
# Career Profile Evaluation Platform

A modern, fully-featured multi-step form for student career profile evaluation with separate frontend and Python backend.

## 📁 Project Structure

```
dronacharya/
├── html/
│   ├── index.html          # Main form UI
│   └── style.css           # Styling with animations
├── script.js               # Frontend logic & animations
├── backend.py              # Python Flask backend
├── requirements.txt        # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Frontend Setup

1. **Open the form** - Simply open `html/index.html` in a web browser
2. **No build needed** - Pure HTML/CSS/JavaScript

### Backend Setup (Optional)

To enable backend functionality for form submission:

1. **Install Python dependencies:**
```bash
pip install flask flask-cors
```

2. **Run the backend:**
```bash
python backend.py
```

The backend will start on `http://localhost:5000`

3. **The frontend will now send data to the backend on form submission**

## 🎨 Features

### Frontend (HTML/CSS/JavaScript)
- ✅ **7-step multi-step form** - Organized student profile evaluation
- ✅ **Smooth animations** - All transitions handled by JavaScript & CSS
- ✅ **Dark/Light mode** - Theme toggle with localStorage persistence
- ✅ **Progress tracking** - Visual progress bar and sidebar navigation
- ✅ **Form validation** - Required fields and email validation
- ✅ **Local storage** - Auto-save progress between sessions
- ✅ **Responsive design** - Mobile and desktop friendly
- ✅ **File upload** - Resume upload support
- ✅ **Dynamic fields** - Add projects, internships, semesters
- ✅ **Tag inputs** - Add preferred companies

### Backend (Python Flask)
- ✅ **Form submission handling** - Receives and processes JSON data
- ✅ **Profile analysis** - Generates hireability scores and recommendations
- ✅ **Data persistence** - Stores submissions as JSON files
- ✅ **CORS enabled** - Frontend can communicate freely
- ✅ **Error handling** - Proper HTTP status codes and error messages

## 📋 Form Sections

1. **Personal & Academic Profile** - Name, email, college, degree, CGPA, scores
2. **Career Goal (AIM)** - Career objective, domains, companies, salary, timeline
3. **Skills & Tools** - Technical skills, programming languages, tools, coding profiles
4. **Projects & Experience** - Add projects, internships, certifications
5. **Academic Performance** - Semester SGPA, subject marks, attendance
6. **Resume & Profiles** - Resume upload, LinkedIn, portfolio
7. **Preferences & Constraints** - Location, startups, risk appetite, studies plans

## 🔌 API Endpoints

### Submit Profile
**POST** `/api/submit-profile`

Request body:
```json
{
  "personalInfo": {...},
  "projects": [...],
  "internships": [...],
  "semesters": [...],
  "companies": [...]
}
```

Response:
```json
{
  "success": true,
  "message": "Profile submitted successfully",
  "analysis": {
    "hirabilityScore": 75.5,
    "recommendedRoles": [...],
    "strengths": [...],
    "areasForImprovement": [...]
  }
}
```

### Health Check
**GET** `/api/health`

### Get All Profiles
**GET** `/api/profiles`

## 🎯 How to Connect Frontend to Backend

The frontend automatically sends data to the backend when you click "Submit & Analyze" on step 7.

**The JavaScript code handles this in `script.js`:**
```javascript
const API_BASE_URL = 'http://localhost:5000/api';

async function submitForm() {
  const payload = {
    personalInfo: formData,
    projects: projects,
    internships: internships,
    semesters: semesters,
    companies: companies
  };

  const response = await fetch(`${API_BASE_URL}/submit-profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}
```

## 💾 Data Storage

- **Frontend**: LocalStorage (browser) - Form progress
- **Backend**: JSON files in `submitted_profiles/` directory

## 🛠️ Customization

### Add New Fields
1. Edit `html/index.html` - Add input field
2. Edit `html/style.css` - Style if needed
3. Edit `script.js` - Add form handler if needed
4. Edit `backend.py` - Process new data

### Extend Backend Analysis
Edit the `analyze_profile()` function in `backend.py` to add:
- AI/ML-based recommendations
- Database integration
- Email notifications
- Resume parsing

## 🎨 Animation Details

All animations are handled by CSS and JavaScript:
- **Fade In/Up** - Form steps appear smoothly
- **Slide Right** - Active step indicator
- **Pulse** - Slider value updates
- **Shake** - Error messages
- **Spin** - Toggle switches
- **Pop** - Form groups appear

## 📱 Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## 🔐 Security Notes

- For production, add:
  - Input validation on backend
  - HTTPS encryption
  - Database instead of file storage
  - Authentication/Authorization
  - Rate limiting
  - Input sanitization

## 🚦 Running Everything Together

Open two terminals:

**Terminal 1 - Backend:**
```bash
python backend.py
```

**Terminal 2 - Serve Frontend:**
```bash
# Option 1: Using http-server (Node.js)
npx http-server

# Option 2: Using Python
python -m http.server 8000
```

Then open: `http://localhost:8000/html/index.html`

## 📞 API Test Example

```bash
curl -X POST http://localhost:5000/api/submit-profile \
  -H "Content-Type: application/json" \
  -d '{
    "personalInfo": {
      "fullName": "John Doe",
      "email": "john@example.com",
      "currentCGPA": 8.5
    }
  }'
```

## 📝 License

Open source - feel free to modify and use!

## 🎓 Next Steps

1. Start the backend: `python backend.py`
2. Open the frontend and fill the form
3. Click Submit to send data to backend
4. Backend processes and saves the profile
5. Extend with your own AI/ML analysis

Happy coding! 🚀
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

