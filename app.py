
import os
import time
import datetime
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ─────────────────────────────────────────────────────────────
#  Load environment variables
# ─────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────
#  ███  AGENT INSTRUCTIONS  ███
#  Customize the agent's behaviour here without touching the
#  rest of the code.  Change tone, domain, safety rules, and
#  citation style in one single block.
# ─────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {

    # ── Identity & Persona ────────────────────────────────────
    "name": "ResearchBot",
    "persona": (
        "You are ResearchBot, an expert AI research assistant powered by Google Gemini. "
        "You help researchers, academics, and scientists with literature review, "
        "paper summarization, citation management, hypothesis generation, and "
        "report drafting. You communicate in a clear, professional, yet approachable tone."
    ),

    # ── Research Domain Focus ─────────────────────────────────
    # Set a primary domain or leave empty ("") to remain general.
    "domain_focus": "",
    # Examples: "Biomedical Sciences", "Computer Science & AI",
    #           "Climate & Environmental Science", "Economics & Finance"

    # ── Tone & Communication Style ───────────────────────────
    "tone": "professional",            # professional | academic | friendly | concise
    "response_language": "English",    # change to any language you need
    "max_response_length": "detailed", # brief | moderate | detailed

    # ── Capabilities enabled / disabled ──────────────────────
    "capabilities": {
        "literature_search": True,
        "paper_summarization": True,
        "citation_management": True,
        "hypothesis_generation": True,
        "report_drafting": True,
        "data_interpretation": True,
        "methodology_advice": True,
        "peer_review_assistance": True,
    },

    # ── Citation Style ────────────────────────────────────────
    # APA | MLA | Chicago | IEEE | Vancouver | Harvard
    "citation_style": "APA",

    # ── Safety Guidelines ────────────────────────────────────
    "safety_guidelines": [
        "Never fabricate citations, DOIs, journal names, or author names.",
        "Clearly state when information may be outdated or unverified.",
        "Do not provide medical, legal, or financial advice as definitive guidance.",
        "Encourage users to verify findings with primary sources.",
        "Respect intellectual property; do not reproduce copyrighted text verbatim.",
        "Flag ethically sensitive research topics and suggest proper ethical review.",
    ],

    # ── Prompting Extras ─────────────────────────────────────
    "always_include_in_response": [
        "Source transparency: note when citing from training knowledge vs user-provided text.",
        "Suggest 1–2 follow-up research directions when answering literature queries.",
    ],

    # ── Forbidden Topics ─────────────────────────────────────
    "forbidden_topics": [
        "Weapons of mass destruction research",
        "Plagiarism assistance",
        "Data fabrication or falsification",
    ],
}

# ─────────────────────────────────────────────────────────────
#  Build the system prompt from AGENT_INSTRUCTIONS
# ─────────────────────────────────────────────────────────────
def _build_system_prompt() -> str:
    ai = AGENT_INSTRUCTIONS
    caps_on   = [k for k, v in ai["capabilities"].items() if v]
    caps_off  = [k for k, v in ai["capabilities"].items() if not v]
    safety    = "\n".join(f"  • {s}" for s in ai["safety_guidelines"])
    extras    = "\n".join(f"  • {e}" for e in ai["always_include_in_response"])
    forbidden = ", ".join(ai["forbidden_topics"]) if ai["forbidden_topics"] else "None"
    domain_line = (
        f"Your primary research domain focus is: {ai['domain_focus']}.\n"
        if ai["domain_focus"] else ""
    )
    disabled_line = (
        f"Disabled capabilities (politely decline if asked): {', '.join(caps_off)}.\n"
        if caps_off else ""
    )
    return f"""{ai['persona']}

{domain_line}Respond in {ai['response_language']} using a {ai['tone']} tone with {ai['max_response_length']} responses.
Default citation style: {ai['citation_style']}.

Enabled capabilities: {', '.join(caps_on)}.
{disabled_line}
Safety guidelines (always follow these):
{safety}

Always include in responses:
{extras}

Never assist with: {forbidden}.
"""

SYSTEM_PROMPT = _build_system_prompt()

# ─────────────────────────────────────────────────────────────
#  Configuration validator
# ─────────────────────────────────────────────────────────────
_PLACEHOLDERS = {
    "your_API_KEY_here",
    "change_this_to_a_random_secret_key",
    "",
}

def validate_env_config() -> list[str]:
    """Returns a list of human-readable problem strings. Empty list = all good."""
    issues = []
    api_key = os.getenv("API_KEY", "")
    if api_key in _PLACEHOLDERS:
        issues.append(
            "API_KEY is not set. "
            "Open .env and replace 'your_API_KEY_here' with your real key. "
            "Get one free at: https://aistudio.google.com/app/apikey"
        )
    return issues


def _classify_exception(exc: Exception) -> str:
    """Converts SDK exceptions into clear, actionable user-facing messages."""
    msg = str(exc)
    low = msg.lower()

    if "api_key" in low or "api key" in low or "invalid" in low and "key" in low:
        return (
            "Authentication failed — invalid API key.\n\n"
            "**Fix:** Open `.env` and set `API_KEY` to your real key.\n"
            "Get one at: https://aistudio.google.com/app/apikey"
        )

    if "quota" in low or "429" in msg or "resource_exhausted" in low:
        return (
            "Rate limit / quota exceeded (HTTP 429).\n\n"
            "**Fix:** Wait a moment and retry, or upgrade your Gemini API quota at "
            "https://aistudio.google.com"
        )

    if "permission" in low or "403" in msg or "forbidden" in low:
        return (
            "Permission denied (HTTP 403).\n\n"
            "**Fix:** Ensure your API key has access to the `gemini-2.5-flash` model. "
            "Check https://aistudio.google.com/app/apikey"
        )

    if "not found" in low or "404" in msg:
        return (
            "Model not found (HTTP 404).\n\n"
            "**Fix:** Verify `MODEL` in `.env` — should be `gemini-2.5-flash`."
        )

    if "getaddrinfo" in low or "network" in low or "connection" in low:
        return (
            "Network error — cannot reach generativelanguage.googleapis.com.\n\n"
            "**Fix:** Check your internet connection and firewall settings."
        )

    return f"Gemini API error: {msg}"


# ─────────────────────────────────────────────────────────────
#  Flask app setup
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
CORS(app)

# ─────────────────────────────────────────────────────────────
#  Gemini client – created once per request (stateless & thread-safe)
# ─────────────────────────────────────────────────────────────
def get_gemini_client() -> genai.Client:
    api_key = os.getenv("API_KEY")
    if not api_key or api_key in _PLACEHOLDERS:
        raise ValueError(
            "API_KEY is not configured. "
            "Add it to your .env file. Get one at https://aistudio.google.com/app/apikey"
        )
    return genai.Client(api_key=api_key)


def _model_name() -> str:
    return os.getenv("MODEL", "gemini-2.5-flash")


# ─────────────────────────────────────────────────────────────
#  Core generate helper
#  Converts our {role, content} history + system prompt into a
#  Gemini API call and returns the text reply.
# ─────────────────────────────────────────────────────────────
def generate(messages: list[dict], system: str = "") -> str:
    """
    messages: list of {"role": "user"|"assistant", "content": str}
    Returns the model's text reply as a plain string.
    """
    client = get_gemini_client()

    # Build Gemini contents list
    # Gemini roles: "user" | "model"  (not "assistant")
    contents: list[types.Content] = []
    for msg in messages:
        role    = "model" if msg["role"] == "assistant" else "user"
        content = msg.get("content", "")
        contents.append(
            types.Content(role=role, parts=[types.Part(text=content)])
        )

    config = types.GenerateContentConfig(
        system_instruction=system if system else None,
        temperature=0.7,
        top_p=0.9,
        max_output_tokens=2048,
    )

    response = client.models.generate_content(
        model=_model_name(),
        contents=contents,
        config=config,
    )
    return response.text.strip()


# ─────────────────────────────────────────────────────────────
#  In-memory storage  (replace with a DB for production)
# ─────────────────────────────────────────────────────────────
chat_histories: dict[str, list] = {}
citations_store: dict[str, list] = {}
projects_store:  dict[str, dict] = {}

# ─────────────────────────────────────────────────────────────
#  Routes – Pages
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = f"sess_{int(time.time())}"
    return render_template(
        "index.html",
        agent_name=AGENT_INSTRUCTIONS["name"],
        citation_style=AGENT_INSTRUCTIONS["citation_style"],
        domain=AGENT_INSTRUCTIONS["domain_focus"] or "All Domains",
    )

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/chat
# ─────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data         = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id   = data.get("session_id") or session.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if session_id not in chat_histories:
        chat_histories[session_id] = []

    history = chat_histories[session_id]
    history.append({"role": "user", "content": user_message})

    # Keep last 20 turns to avoid token overflow
    recent = history[-20:]

    try:
        reply = generate(recent, SYSTEM_PROMPT)
    except Exception as exc:
        history.pop()  # remove the failed user turn
        return jsonify({"error": _classify_exception(exc)}), 500

    history.append({"role": "assistant", "content": reply})

    return jsonify({
        "reply":      reply,
        "session_id": session_id,
        "timestamp":  datetime.datetime.utcnow().isoformat(),
        "model":      _model_name(),
    })

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/summarize
# ─────────────────────────────────────────────────────────────
@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    data    = request.get_json(silent=True) or {}
    text    = (data.get("text") or "").strip()
    style   = data.get("style", "abstract")
    purpose = data.get("purpose", "general")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    prompt_msg = (
        f"Please summarize the following research text in '{style}' style "
        f"for purpose: {purpose}. "
        f"Cite in {AGENT_INSTRUCTIONS['citation_style']} style where applicable.\n\n"
        f"---\n{text}\n---"
    )

    try:
        summary = generate([{"role": "user", "content": prompt_msg}], SYSTEM_PROMPT)
    except Exception as exc:
        return jsonify({"error": _classify_exception(exc)}), 500

    return jsonify({"summary": summary, "style": style, "word_count": len(text.split())})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/literature_search
# ─────────────────────────────────────────────────────────────
@app.route("/api/literature_search", methods=["POST"])
def api_literature_search():
    data      = request.get_json(silent=True) or {}
    query     = (data.get("query") or "").strip()
    year_from = data.get("year_from", "")
    year_to   = data.get("year_to", "")
    domain    = data.get("domain", AGENT_INSTRUCTIONS["domain_focus"] or "general")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    year_filter = ""
    if year_from or year_to:
        year_filter = f" published between {year_from or 'any'} and {year_to or 'present'}"

    prompt_msg = (
        f"Act as a systematic literature review assistant. "
        f"For the research topic '{query}' in domain '{domain}'{year_filter}:\n\n"
        f"1. Identify 5–7 key research themes or findings.\n"
        f"2. List 5 representative (but clearly noted as illustrative) papers with:\n"
        f"   - Title, first author(s), approximate year, journal/conference\n"
        f"   - One-sentence contribution summary\n"
        f"   - Formatted in {AGENT_INSTRUCTIONS['citation_style']} style\n"
        f"3. Highlight research gaps and open problems.\n"
        f"4. Suggest 2 promising follow-up directions.\n\n"
        f"Important: Clearly state that paper details are illustrative examples from "
        f"training knowledge and should be verified via Google Scholar, PubMed, or Semantic Scholar."
    )

    try:
        result = generate([{"role": "user", "content": prompt_msg}], SYSTEM_PROMPT)
    except Exception as exc:
        return jsonify({"error": _classify_exception(exc)}), 500

    return jsonify({"results": result, "query": query, "domain": domain})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/generate_citation
# ─────────────────────────────────────────────────────────────
@app.route("/api/generate_citation", methods=["POST"])
def api_generate_citation():
    data   = request.get_json(silent=True) or {}
    source = (data.get("source") or "").strip()
    style  = data.get("style", AGENT_INSTRUCTIONS["citation_style"])

    if not source:
        return jsonify({"error": "No source information provided"}), 400

    prompt_msg = (
        f"Generate a properly formatted {style} citation for the following source. "
        f"If any information is missing, note what is needed. "
        f"Also provide an in-text citation example.\n\nSource info:\n{source}"
    )

    try:
        citation = generate([{"role": "user", "content": prompt_msg}], SYSTEM_PROMPT)
    except Exception as exc:
        return jsonify({"error": _classify_exception(exc)}), 500

    session_id = data.get("session_id", "default")
    if session_id not in citations_store:
        citations_store[session_id] = []
    citations_store[session_id].append({
        "source":   source,
        "citation": citation,
        "style":    style,
        "added":    datetime.datetime.utcnow().isoformat(),
    })

    return jsonify({"citation": citation, "style": style})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/get_citations
# ─────────────────────────────────────────────────────────────
@app.route("/api/get_citations", methods=["GET"])
def api_get_citations():
    session_id = request.args.get("session_id", "default")
    return jsonify({"citations": citations_store.get(session_id, [])})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/draft_section
# ─────────────────────────────────────────────────────────────
@app.route("/api/draft_section", methods=["POST"])
def api_draft_section():
    data       = request.get_json(silent=True) or {}
    section    = (data.get("section") or "").strip()
    topic      = (data.get("topic") or "").strip()
    context    = (data.get("context") or "").strip()
    word_count = data.get("word_count", 300)

    if not section or not topic:
        return jsonify({"error": "Section type and topic are required"}), 400

    prompt_msg = (
        f"Draft a '{section}' section (~{word_count} words) for a research paper on: '{topic}'.\n"
        + (f"Additional context / notes:\n{context}\n\n" if context else "\n")
        + f"Follow academic writing conventions. Use {AGENT_INSTRUCTIONS['citation_style']} "
        f"citation placeholders (e.g., [Author, Year]) where references would typically appear. "
        f"Be thorough and scholarly."
    )

    try:
        draft = generate([{"role": "user", "content": prompt_msg}], SYSTEM_PROMPT)
    except Exception as exc:
        return jsonify({"error": _classify_exception(exc)}), 500

    return jsonify({"draft": draft, "section": section, "topic": topic})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/research_ideas
# ─────────────────────────────────────────────────────────────
@app.route("/api/research_ideas", methods=["POST"])
def api_research_ideas():
    data  = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    level = data.get("level", "graduate")

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    prompt_msg = (
        f"Generate 6 original and feasible research ideas for '{topic}' "
        f"suitable for a {level}-level researcher. "
        f"For each idea provide:\n"
        f"1. A concise working title\n"
        f"2. Research question / hypothesis\n"
        f"3. Proposed methodology (2–3 sentences)\n"
        f"4. Expected impact / contribution\n"
        f"5. Potential challenges\n\n"
        f"Ensure ideas are novel, ethically sound, and practically achievable."
    )

    try:
        ideas = generate([{"role": "user", "content": prompt_msg}], SYSTEM_PROMPT)
    except Exception as exc:
        return jsonify({"error": _classify_exception(exc)}), 500

    return jsonify({"ideas": ideas, "topic": topic, "level": level})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/project  (CRUD)
# ─────────────────────────────────────────────────────────────
@app.route("/api/project", methods=["POST"])
def api_create_project():
    data       = request.get_json(silent=True) or {}
    title      = (data.get("title") or "").strip()
    desc       = data.get("description", "")
    session_id = data.get("session_id", "default")

    if not title:
        return jsonify({"error": "Project title required"}), 400

    pid = f"proj_{int(time.time())}"
    projects_store[pid] = {
        "id":          pid,
        "title":       title,
        "description": desc,
        "session_id":  session_id,
        "created":     datetime.datetime.utcnow().isoformat(),
        "notes":       [],
        "citations":   [],
        "status":      "active",
    }
    return jsonify({"project": projects_store[pid]}), 201


@app.route("/api/projects", methods=["GET"])
def api_list_projects():
    session_id    = request.args.get("session_id", "default")
    user_projects = [p for p in projects_store.values() if p["session_id"] == session_id]
    return jsonify({"projects": user_projects})


@app.route("/api/project/<pid>/note", methods=["POST"])
def api_add_note(pid):
    if pid not in projects_store:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json(silent=True) or {}
    note = (data.get("note") or "").strip()
    if not note:
        return jsonify({"error": "Empty note"}), 400
    projects_store[pid]["notes"].append({
        "text": note,
        "ts":   datetime.datetime.utcnow().isoformat(),
    })
    return jsonify({"project": projects_store[pid]})

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/health
# ─────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def api_health():
    issues = validate_env_config()
    return jsonify({
        "status":         "ok" if not issues else "misconfigured",
        "agent":          AGENT_INSTRUCTIONS["name"],
        "model":          _model_name(),
        "citation_style": AGENT_INSTRUCTIONS["citation_style"],
        "domain":         AGENT_INSTRUCTIONS["domain_focus"] or "General",
        "timestamp":      datetime.datetime.utcnow().isoformat(),
        "config_issues":  issues,
    })

# ─────────────────────────────────────────────────────────────
#  Routes – API  /api/clear_history
# ─────────────────────────────────────────────────────────────
@app.route("/api/clear_history", methods=["POST"])
def api_clear_history():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    chat_histories.pop(session_id, None)
    return jsonify({"message": "History cleared", "session_id": session_id})

# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print(f"\nResearch Agent starting on http://localhost:{port}")
    print(f"   Model   : {_model_name()}")
    print(f"   Domain  : {AGENT_INSTRUCTIONS['domain_focus'] or 'All Domains'}")
    print(f"   Citation: {AGENT_INSTRUCTIONS['citation_style']}\n")

    # ── Startup config validation ──────────────────────────────
    issues = validate_env_config()
    if issues:
        print("CONFIGURATION ISSUES DETECTED:")
        for i, issue in enumerate(issues, 1):
            print(f"\n  [{i}] {issue}")
        print("\n  Fix the issues above in your .env file before making API calls.\n")
    else:
        print("Configuration OK - Gemini API key is set.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
