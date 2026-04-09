// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State Management
let currentStep = 1;
const totalSteps = 6;
const formData = {};
const projects = [];
const internships = [];
const semesters = [];
let companies = [];

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    loadFormData();
    attachEventListeners();
    initializeStepNavigation();
    loadTheme();
});

// ==================== Theme Management ====================
function loadTheme() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeToggle();
    }
}

document.getElementById('themeToggle').addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    updateThemeToggle();
});

function updateThemeToggle() {
    const icon = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    document.getElementById('themeToggle').textContent = icon;
}

// ==================== Form Data Management ====================
function saveFormData() {
    const form = document.getElementById('mainForm');
    const formValue = new FormData(form);
    
    // Collect all form fields
    for (let [key, value] of formValue.entries()) {
        if (key === 'domains' || key === 'cloudPlatforms') {
            if (!formData[key]) formData[key] = [];
            if (!formData[key].includes(value)) {
                formData[key].push(value);
            }
        } else {
            formData[key] = value;
        }
    }
    
    // Save to localStorage
    localStorage.setItem('careerFormData', JSON.stringify(formData));
}

function loadFormData() {
    const saved = localStorage.getItem('careerFormData');
    if (saved) {
        Object.assign(formData, JSON.parse(saved));
        loadFormToUI();
    }
}

function loadFormToUI() {
    Object.keys(formData).forEach(key => {
        const element = document.querySelector(`[name="${key}"]`);
        if (element) {
            if (element.type === 'checkbox' || element.type === 'radio') {
                element.checked = formData[key] === true || formData[key] === element.value;
            } else {
                element.value = formData[key];
            }
        }
    });
}

// ==================== Event Listeners ====================
function attachEventListeners() {
    // Backlogs Toggle
    document.getElementById('backlogs').addEventListener('change', (e) => {
        const count = document.getElementById('backlogsCount');
        const label = document.getElementById('backlogsLabel');
        animateToggle(e.target, label);
        if (e.target.checked) {
            count.style.display = 'block';
            label.textContent = 'Yes';
        } else {
            count.style.display = 'none';
            label.textContent = 'No';
        }
    });

    // Salary Slider
    document.querySelector('[name="expectedSalary"]').addEventListener('input', (e) => {
        animateSliderValue('salaryValue', e.target.value);
    });

    // Skill Sliders
    document.querySelectorAll('.skill-slider').forEach(slider => {
        slider.addEventListener('input', (e) => {
            const id = e.target.name + 'Value';
            animateSliderValue(id, e.target.value);
        });
    });

    // Aim Word Counter
    document.querySelector('[name="aim"]').addEventListener('input', (e) => {
        const words = e.target.value.trim().split(/\s+/).filter(w => w).length;
        document.getElementById('aimCount').textContent = words;
    });

    // Tags Input for Companies
    document.getElementById('companiesInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.target.value.trim()) {
            e.preventDefault();
            companies.push(e.target.value.trim());
            renderCompanyTags();
            e.target.value = '';
        }
    });

    // Add Project Button
    document.getElementById('addProjectBtn').addEventListener('click', addProject);

    // Add Internship Button
    document.getElementById('addInternshipBtn').addEventListener('click', addInternship);

    // Add Semester Button
    document.getElementById('addSemesterBtn').addEventListener('click', addSemester);

    // Resume Upload
    document.getElementById('resumeUpload').addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            document.getElementById('resumeFileName').innerHTML = `
                <div style="color: var(--success); font-size: 12px; margin-top: 8px; animation: slideDown 0.3s ease;">
                    ✓ ${e.target.files[0].name} uploaded
                </div>
            `;
        }
    });

    // Step Navigation Buttons
    document.getElementById('prevBtn').addEventListener('click', () => {
        if (currentStep > 1) showStep(currentStep - 1);
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        if (currentStep < totalSteps) {
            showStep(currentStep + 1);
        } else {
            submitForm();
        }
    });
}

// ==================== Step Navigation ====================
function initializeStepNavigation() {
    document.querySelectorAll('.step-item').forEach(item => {
        item.addEventListener('click', () => {
            const step = parseInt(item.dataset.step);
            showStep(step);
        });
    });
}

function showStep(step) {
    if (step < 1 || step > totalSteps) return;
    saveFormData();
    
    // Fade out current step
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.step-item').forEach(s => s.classList.remove('active'));
    
    const targetStep = document.querySelector(`.form-step[data-step="${step}"]`);
    const targetNav = document.querySelector(`.step-item[data-step="${step}"]`);
    if (!targetStep || !targetNav) return;
    
    // Fade in new step
    targetStep.classList.add('active');
    targetNav.classList.add('active');
    
    // Update progress bar
    const progress = (step / totalSteps) * 100;
    animateProgressBar(progress);
    
    // Update buttons
    document.getElementById('prevBtn').style.display = step === 1 ? 'none' : 'flex';
    document.getElementById('nextBtn').textContent = step === totalSteps ? '📊 Submit & Analyze' : 'Next →';
    
    currentStep = step;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==================== Dynamic Components ====================
function addProject() {
    const id = Math.random().toString(36).substr(2, 9);
    projects.push({ id });
    renderProjects();
}

function renderProjects() {
    const list = document.getElementById('projectsList');
    list.innerHTML = '';
    
    projects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
            <div class="project-card-header">
                <strong>Project ${index + 1}</strong>
                <button type="button" class="btn btn-danger btn-small" onclick="removeProject(${index})">Delete</button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Project Title</label>
                    <input type="text" placeholder="E.g., E-commerce Platform">
                </div>
                <div class="form-group">
                    <label>Domain</label>
                    <select>
                        <option>Web Development</option>
                        <option>ML/AI</option>
                        <option>Mobile App</option>
                        <option>Data Science</option>
                    </select>
                </div>
            </div>
            <div class="form-group form-row full">
                <label>Tech Stack (comma separated)</label>
                <input type="text" placeholder="React, Node.js, MongoDB">
            </div>
            <div class="form-group form-row full">
                <label>Description (max 100 words)</label>
                <textarea maxlength="100" placeholder="Brief project description"></textarea>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>GitHub Link</label>
                    <input type="url" placeholder="https://github.com/...">
                </div>
                <div class="form-group">
                    <label>Live Link</label>
                    <input type="url" placeholder="https://...">
                </div>
            </div>
            <div class="form-group">
                <label>Complexity</label>
                <select>
                    <option>Beginner</option>
                    <option>Intermediate</option>
                    <option>Advanced</option>
                </select>
            </div>
        `;
        list.appendChild(card);
    });
}

function removeProject(index) {
    projects.splice(index, 1);
    renderProjects();
}

function addInternship() {
    const id = Math.random().toString(36).substr(2, 9);
    internships.push({ id });
    renderInternships();
}

function renderInternships() {
    const list = document.getElementById('internshipsList');
    list.innerHTML = '';
    
    internships.forEach((internship, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
            <div class="project-card-header">
                <strong>Internship ${index + 1}</strong>
                <button type="button" class="btn btn-danger btn-small" onclick="removeInternship(${index})">Delete</button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Company Name</label>
                    <input type="text" placeholder="E.g., Google, Microsoft">
                </div>
                <div class="form-group">
                    <label>Role</label>
                    <input type="text" placeholder="E.g., SDE Intern, Data Analyst">
                </div>
            </div>
            <div class="form-group">
                <label>Duration</label>
                <input type="text" placeholder="E.g., 3 months (Jan - Mar 2024)">
            </div>
        `;
        list.appendChild(card);
    });
}

function removeInternship(index) {
    internships.splice(index, 1);
    renderInternships();
}

function addSemester() {
    const id = Math.random().toString(36).substr(2, 9);
    semesters.push({ id });
    renderSemesters();
}

function renderSemesters() {
    const list = document.getElementById('semestersList');
    list.innerHTML = '';
    
    semesters.forEach((semester, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
            <div class="project-card-header">
                <strong>Semester ${index + 1}</strong>
                <button type="button" class="btn btn-danger btn-small" onclick="removeSemester(${index})">Delete</button>
            </div>
            <div class="form-group">
                <label>SGPA</label>
                <input type="number" min="0" max="10" step="0.01" placeholder="E.g., 8.5">
            </div>
        `;
        list.appendChild(card);
    });
}

function removeSemester(index) {
    semesters.splice(index, 1);
    renderSemesters();
}

function renderCompanyTags() {
    const container = document.getElementById('companiesTags');
    const input = document.getElementById('companiesInput');
    container.innerHTML = '';
    
    companies.forEach((company, index) => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            ${company}
            <span class="tag-remove" onclick="removeCompany(${index})">×</span>
        `;
        container.appendChild(tag);
    });
    
    container.appendChild(input);
}

function removeCompany(index) {
    companies.splice(index, 1);
    renderCompanyTags();
}

// ==================== Animation Utilities ====================
function animateSliderValue(elementId, value) {
    const element = document.getElementById(elementId);
    element.textContent = value;
}

function animateProgressBar(progress) {
    const progressBar = document.getElementById('progressBarInner');
    progressBar.style.width = progress + '%';
}

function animateToggle(element, label) {
    element.parentElement.style.animation = 'spin 0.4s ease';
}

// ==================== Form Submission ====================
async function submitForm() {
    // Validate form
    if (!validateForm()) {
        showNotification('Please fill all required fields', 'error');
        return;
    }

    // Show loading state
    const submitBtn = document.getElementById('nextBtn');
    const originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<span class="loading"></span> Analyzing...';
    submitBtn.disabled = true;

    try {
        // Save final data
        saveFormData();
        
        // Prepare data for backend
        const payload = {
            personalInfo: formData,
            projects: projects,
            internships: internships,
            semesters: semesters,
            companies: companies
        };

        // Send to Python backend
        const response = await fetch(`${API_BASE_URL}/submit-profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            showNotification('✅ Profile submitted successfully!', 'success');
            console.log('Backend Response:', result);
            
            // Optional: Redirect to results page or show analysis
            setTimeout(() => {
                // window.location.href = '/results.html';
                alert('Form submitted to Python backend!\nCheck console for response.');
            }, 1500);
        } else {
            showNotification('Error submitting form', 'error');
        }
    } catch (error) {
        console.error('Submission Error:', error);
        showNotification('Error connecting to server. Form saved locally.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function validateForm() {
    const required = ['fullName', 'email', 'phone', 'collegeName', 'degree', 'branch'];
    for (let field of required) {
        if (!formData[field]) {
            return false;
        }
    }
    return true;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = type === 'error' ? 'error-message' : 'success-message';
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '300px';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== Keyboard Shortcuts ====================
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        submitForm();
    }
    if (e.key === 'ArrowRight' && currentStep < totalSteps) {
        showStep(currentStep + 1);
    }
    if (e.key === 'ArrowLeft' && currentStep > 1) {
        showStep(currentStep - 1);
    }
});
