# 📚 AI-Powered Research Agent

An intelligent AI-powered Research Assistant built using **Python Flask**. The application helps researchers, students, and academics perform literature reviews, summarize research papers, generate citations, draft research sections, and organize research projects through an interactive web interface.

---

## 🚀 Features

- 💬 AI Chat Assistant for research-related queries
- 📄 Research Paper Summarization
- 🔍 Literature Search Assistance
- 📚 Automatic Citation Generation (APA, MLA, IEEE, etc.)
- ✍️ Research Paper Section Drafting
- 💡 Research Idea & Hypothesis Generation
- 📂 Research Project Management
- 📝 Notes and Citation Storage
- 🔒 Secure API Key Management using `.env`
- ⚙️ Customizable AI Agent Instructions
- 🌐 REST API built with Flask
- 🎨 Responsive Web Interface

---

## 🛠️ Technologies Used

### Backend
- Python 3.x
- Flask
- Flask-CORS
- python-dotenv

### Frontend
- HTML
- CSS
- JavaScript

### AI Integration
- AI Language Model API

---

## 📁 Project Structure

```
Research-Agent/
│
├── app.py
├── .env
├── requirements.txt
├── templates/
│     └── index.html
├── static/
│     ├── css/
│     ├── js/
│     └── images/
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/research-agent.git

cd research-agent
```

### Create Virtual Environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Configure Environment Variables

Create a `.env` file.

Example:

```env
API_KEY=your_api_key
MODEL_NAME=your_model_name

FLASK_SECRET_KEY=your_secret_key

FLASK_PORT=5000

FLASK_DEBUG=True
```

---

## ▶️ Run the Application

```bash
python app.py
```

The application will start at

```
http://localhost:5000
```

---

## 📌 API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/chat` | Chat with AI |
| POST | `/api/summarize` | Summarize research text |
| POST | `/api/literature_search` | Literature review assistance |
| POST | `/api/generate_citation` | Generate citations |
| GET | `/api/get_citations` | Retrieve saved citations |
| POST | `/api/draft_section` | Draft research paper sections |
| POST | `/api/research_ideas` | Generate research ideas |
| POST | `/api/project` | Create research project |
| GET | `/api/projects` | List projects |
| POST | `/api/project/<id>/note` | Add project notes |
| POST | `/api/clear_history` | Clear chat history |
| GET | `/api/health` | Check application health |

---

## 🎯 How It Works

1. User enters a research-related query.
2. Flask backend processes the request.
3. The AI model generates an intelligent response.
4. The application returns:
   - Research assistance
   - Paper summaries
   - Citations
   - Research ideas
   - Draft sections
5. Chat history and research projects are maintained during the session.

---

## 🔒 Security

- API keys stored securely using `.env`
- Environment validation before startup
- Error handling for invalid API keys
- Session-based chat history
- Safe AI response guidelines

---

## 📈 Future Enhancements

- PDF upload and automatic paper analysis
- Research database integration
- Cloud database support
- User authentication
- Export citations to reference managers
- Voice-enabled research assistant
- Multi-language support
- Mobile application

---

## 👨‍💻 Author

Developed by **Anmol Mehra**

B.Tech Computer Science & Engineering

ITER, Siksha 'O' Anusandhan University

---

## 📄 License

This project is developed for educational and learning purposes.

```
MIT License
```

---

## ⭐ If you like this project

Give this repository a ⭐ on GitHub and feel free to contribute!
