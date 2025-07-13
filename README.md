# 📈 Personalized Skill Growth Tracker

> An intelligent, modular, and gamified platform designed to help users track, manage, and grow their skills with personalized recommendations powered by AI.

## 🌟 Overview

The **Personalized Skill Growth Tracker** is a smart, offline-first application built using Python and Streamlit that helps users:
- Track their skill development journey
- Get personalized AI-based skill recommendations
- Access curated learning resources from platforms like YouTube, Coursera, etc.
- Maintain progress journals and study notes
- Set daily goals and earn achievement badges

All data is stored privately per user using SQLite and JSON — no skill-sharing between users!

---

## 🛠 Tech Stack

| Layer         | Technology                                                                 |
|--------------|-----------------------------------------------------------------------------|
| Frontend     | Streamlit                                                                   |
| Backend      | Python, SQLite, JSON                                                         |
| AI/ML        | Scikit-learn, Transformers, TensorFlow, Mistral-7B (for AI assistant)        |
| Visualization| Plotly, Chart.js, D3.js                                                      |
| APIs         | YouTube, Coursera, Khan Academy, Udemy, edX, OpenCourseWare, W3Schools       |
| Auth         | bcrypt for password hashing                                                  |
| Infra        | Google Cloud (planned)                                                       |

---

## ✨ Features

- 🔐 **User Authentication** – Secure Signup/Login with hashed passwords
- 🧠 **AI Assistant** – Skill path generator + Q&A using Mistral-7B
- 🧾 **Dashboard** – Visual progress, categorized skills, and user-specific stats
- 🛠️ **Skill Manager** – Add/view/update/delete skills
- ⏱️ **Study Timer** – Tracks hours and rewards badges for consistency
- 📘 **Journal & Notes** – For writing goals, reflections, or task updates
- 🎯 **Daily Goals** – Set, track, and achieve daily targets
- 📚 **Learning Resources** – Fetched via API (YouTube, Coursera, etc.)
- 📊 **Visual Analytics** – Interactive charts using Plotly

---

## 🧩 Project Structure

📁 personalized-skill-growth-tracker/
├── app.py # Main Streamlit interface
├── ai_assistant.py # Handles AI functionality
├── database.py # SQLite + JSON data handling
├── skills.py # Skill logic & tracking
├── visualizations.py # Charting and graphing
├── utils/
│ ├── auth.py # Authentication and hashing
│ └── google_api.py # External study resource API handlers

> ⚠️ You need to create a `.env` file and add your API key:
MY_API_KEY=your_api_key_here

---

## 🚀 How to Run

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/personalized-skill-growth-tracker.git
   cd personalized-skill-growth-tracker
2. Install dependencies
   ```bash
   pip install -r requirements.txt
3. Run the app
   ```bash
   streamlit run app.py
