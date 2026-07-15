# 🔬 AI Research Agent — IBM watsonx.ai + Granite

A full-stack AI-powered research assistant built with **Python Flask** and **IBM watsonx.ai Granite** models.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Research Chat** | Conversational AI for any research question |
| **Literature Search** | Discover key papers, themes, and research gaps |
| **Paper Summarizer** | Summarize abstracts/full text in 5 styles |
| **Citation Manager** | Generate & store APA/MLA/IEEE/Chicago/Harvard/Vancouver citations |
| **Section Drafter** | AI-drafted Introduction, Methods, Discussion, etc. |
| **Idea Generator** | 6 novel, feasible research ideas with methodology |
| **Project Manager** | Organize research projects and notes |
| **Dark Mode** | System-aware, toggleable dark/light theme |
| **Mobile Responsive** | Fully responsive Bootstrap 5 layout |

---

## 📋 Prerequisites

- Python 3.10+
- IBM Cloud account with **watsonx.ai** service enabled
- IBM Cloud API Key
- watsonx.ai Project ID

---

## 🔧 Setup Instructions

### 1. Clone / navigate to the project

```bash
cd research_agent
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and fill in your credentials:

```bash
# Windows
copy env.example .env

# macOS / Linux
cp env.example .env
```

Edit `.env`:

```ini
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
FLASK_SECRET_KEY=your_random_secret_key
FLASK_DEBUG=False
FLASK_PORT=5000
```

### 5. Run the application

```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🔑 Getting IBM Cloud Credentials

### IBM Cloud API Key
1. Go to [IBM Cloud Console](https://cloud.ibm.com)
2. Click your avatar → **Manage → Access (IAM)**
3. Select **API Keys** → **Create an IBM Cloud API key**
4. Copy the key (it's shown only once)

### watsonx.ai Project ID
1. Go to [IBM watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)
2. Open or create a project
3. Go to **Manage** tab → copy the **Project ID**

### Available Granite Models
| Model ID | Description |
|---|---|
| `ibm/granite-3-8b-instruct` | Recommended — fast & capable |
| `ibm/granite-3-2b-instruct` | Lighter, faster |
| `ibm/granite-13b-chat-v2` | Older chat model |

---

## 🎛️ Customizing the Agent (AGENT_INSTRUCTIONS)

All agent behavior is controlled from the `AGENT_INSTRUCTIONS` dictionary in `app.py`:

```python
AGENT_INSTRUCTIONS = {
    "name": "ResearchBot",
    "persona": "You are ...",
    "domain_focus": "Biomedical Sciences",  # or "" for general
    "tone": "professional",                  # professional | academic | friendly | concise
    "citation_style": "APA",                 # APA | MLA | Chicago | IEEE | Vancouver | Harvard
    "capabilities": {
        "literature_search": True,
        "paper_summarization": True,
        "citation_management": True,
        "hypothesis_generation": True,
        "report_drafting": True,
        ...
    },
    "safety_guidelines": [...],
    "forbidden_topics": [...],
}
```

**No other code changes needed** — the system prompt is rebuilt automatically from this dict.

---

## 🚀 Production Deployment

### Option A: Gunicorn (Linux/macOS)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option B: IBM Code Engine

1. Build a container image:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

2. Push to IBM Container Registry and deploy via IBM Code Engine console.

3. Set environment variables as **Secrets** in Code Engine:
   - `IBM_API_KEY`
   - `WATSONX_PROJECT_ID`
   - `FLASK_SECRET_KEY`

### Option C: Railway / Render / Heroku

Add a `Procfile`:

```
web: gunicorn app:app
```

Set the same env vars in the platform dashboard.

---

## 📁 Project Structure

```
research_agent/
├── app.py                  ← Flask backend + AGENT_INSTRUCTIONS
├── requirements.txt        ← Python dependencies
├── env.example             ← Environment variable template
├── README.md               ← This file
├── templates/
│   └── index.html          ← Full frontend (Bootstrap 5)
└── static/
    ├── css/
    │   └── style.css       ← Custom styles + dark mode
    └── js/
        └── app.js          ← Frontend logic
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main application UI |
| `POST` | `/api/chat` | Conversational research chat |
| `POST` | `/api/summarize` | Summarize paper text |
| `POST` | `/api/literature_search` | Literature discovery |
| `POST` | `/api/generate_citation` | Format a citation |
| `GET` | `/api/get_citations` | Retrieve saved citations |
| `POST` | `/api/draft_section` | Draft a paper section |
| `POST` | `/api/research_ideas` | Generate research ideas |
| `POST` | `/api/project` | Create a research project |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/project/<id>/note` | Add note to project |
| `POST` | `/api/clear_history` | Clear chat history |
| `GET` | `/api/health` | Health check |

---

## 🛡️ Security Notes

- Never commit your `.env` file (it is in `.gitignore`)
- Use strong random values for `FLASK_SECRET_KEY` in production
- Set `FLASK_DEBUG=False` in production
- Use HTTPS behind a reverse proxy (nginx/Caddy) in production

---

## 📝 License

MIT License — free to use, modify, and distribute.
