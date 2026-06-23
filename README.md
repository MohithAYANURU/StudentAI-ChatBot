# StudentOS: AI ChatBot for CS Students

A specialized, context-aware AI assistant designed specifically for Computer Science students navigating the French engineering system. StudentOS bridges the gap between general-purpose LLMs and university career portals by offering direct PDF CV parsing, local internship targeting, and active-recall exam coaching.

## Core Features

* **4 Specialized Modes:**
  * **Concept Explainer:** Tailors CS concept explanations to beginner, intermediate, or advanced levels with Python code examples.
  * **Exam Coach:** Generates active-recall quizzes based on student notes.
  * **CV Reviewer:** Extracts text directly from uploaded PDFs to provide structured, tech-focused resume feedback.
  * **Internship Finder:** Maps student profiles to French tech internship platforms (JobTeaser, Welcome to the Jungle) for mandatory 6-month *stages*.
* **Multi-Model Benchmarking:** A dedicated `/compare` route that abstracts API calls to simultaneously query **Groq (Llama 3.1)**, **Gemini 2.0 Flash**, and **Mistral Small**, comparing response times and reasoning quality in real-time.
* **Secure Authentication & RBAC:** Features a custom-built Role-Based Access Control system intercepting unauthenticated requests, with PBKDF2 password hashing via `werkzeug.security`.
* **Data Privacy Wipers:** Implements a strict `/reset` endpoint that completely flushes the Flask session state, ensuring user chat logs and extracted PDF data are destroyed from server memory.

## Tech Stack

* **Backend:** Python, Flask, PyPDF (Document Extraction), Werkzeug (Security)
* **Frontend:** Vanilla JavaScript, HTML5, CSS3 (Monochromatic High-Contrast UI)
* **AI Integration:** Groq API, Google Generative AI SDK, Mistral AI SDK
* **State Management:** Secure HTTP-only Flask Session Cookies (`credentials: "include"`)




## Obtain Developer API Keys
To run the AI models, you must create free developer accounts and generate API keys from the following providers:

# Groq: Create an account at console.groq.com

# Gemini: Create an account at aistudio.google.com

# Mistral: Create an account at console.mistral.ai


## Local Setup Instructions

### 1. Backend Initialization
Ensure you have Python 3 installed, then set up your environment:

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
#copy the environment variables 
cp .env.example .env

# Install dependencies
pip install -r requirements.txt


 # Start the Flask server:
 python app.py

 # open the index.html