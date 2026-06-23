# Team Collaboration Log

| Member | Task | Description | Decisions Made | Date |
| :--- | :--- | :--- | :--- | :--- |
| Mohith | Backend & Security Architecture | Built the core Flask server (`app.py`), RBAC security (`auth.py`), and PDF parsing logic. | Chose in-memory JSON storage for user credentials and Werkzeug PBKDF2 hashing over a heavy SQL setup to ensure a lightweight prototype. | 22/06/2026 |
| Mohith | Frontend Development | Built the Vanilla JS client, markdown rendering, and CSS styling. | Used `credentials: "include"` in JS fetch calls to ensure proper session cookie transmission, fixing context loss. | 22/06/2026 |
| [Partner Name / Mohith] | GenAI API & Benchmarking | Implemented `models.py` with Groq, Gemini, and Mistral. Built the `/compare` route. | Built a multi-model abstraction layer to benchmark response times simultaneously instead of locking into one provider. | 23/06/2026 |
