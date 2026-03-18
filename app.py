"""My Second Brain — Flask backend for the Second Brain Command Center."""

import json
import os
import queue
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request, Response, send_from_directory
from PyPDF2 import PdfReader

from utils.claude_runner import check_connection, run_prompt, run_prompt_streaming, is_claude_installed
from utils.claudemd_sync import (
    find_claudemd,
    parse_about_me,
    read_claudemd,
    update_about_me,
    get_stats,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory state
connection_state = {"connected": False, "server_id": None, "last_check": None}


# ─── Pages ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ─── API: Connection ─────────────────────────────────────────────────────────


@app.route("/api/connect", methods=["POST"])
def api_connect():
    """Test connection to Claude Code CLI and mark as connected."""
    result = check_connection()
    if result["connected"]:
        connection_state["connected"] = True
        connection_state["server_id"] = os.uname().nodename
        connection_state["last_check"] = time.time()

        stats = get_stats()
        return jsonify({
            "success": True,
            "server_id": connection_state["server_id"],
            "stats": stats,
        })
    else:
        connection_state["connected"] = False
        return jsonify({"success": False, "error": result.get("error", "Unknown error")}), 500


@app.route("/api/disconnect", methods=["POST"])
def api_disconnect():
    """Mark as disconnected."""
    connection_state["connected"] = False
    connection_state["server_id"] = None
    return jsonify({"success": True})


@app.route("/api/status")
def api_status():
    """Return current connection state and stats."""
    stats = get_stats() if connection_state["connected"] else {}
    return jsonify({
        "connected": connection_state["connected"],
        "server_id": connection_state["server_id"],
        "stats": stats,
        "claude_installed": is_claude_installed(),
    })


# ─── API: About Me ───────────────────────────────────────────────────────────


@app.route("/api/about", methods=["GET"])
def api_about_get():
    """Read About Me from CLAUDE.md."""
    content = read_claudemd()
    if content is None:
        return jsonify({"success": False, "error": "CLAUDE.md not found"}), 404

    about = parse_about_me(content)
    return jsonify({"success": True, "about": about})


@app.route("/api/about", methods=["POST"])
def api_about_save():
    """Save About Me to CLAUDE.md."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    success = update_about_me(data)
    if success:
        return jsonify({"success": True, "message": "Saved and synced to CLAUDE.md"})
    else:
        return jsonify({"success": False, "error": "Could not find CLAUDE.md"}), 404


# ─── API: Projects ───────────────────────────────────────────────────────────

PROJECTS_FILE = os.path.join(os.path.dirname(__file__), "projects.json")


def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_projects(projects):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)


@app.route("/api/projects", methods=["GET"])
def api_projects_get():
    return jsonify({"success": True, "projects": load_projects()})


@app.route("/api/projects", methods=["POST"])
def api_projects_save():
    data = request.get_json()
    if not data or "projects" not in data:
        return jsonify({"success": False, "error": "No projects provided"}), 400
    save_projects(data["projects"])
    return jsonify({"success": True})


# ─── API: Build (send prompt to Claude) ──────────────────────────────────────


@app.route("/api/build", methods=["POST"])
def api_build():
    """Send a prompt to Claude Code and return the response."""
    if not connection_state["connected"]:
        return jsonify({"success": False, "error": "Not connected"}), 400

    data = request.get_json()
    prompt = data.get("prompt", "").strip() if data else ""
    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"}), 400

    conversation_id = data.get("conversation_id") if data else None
    result = run_prompt(prompt, timeout=600, conversation_id=conversation_id, allow_tools=True)
    return jsonify(result)


@app.route("/api/build/stream", methods=["POST"])
def api_build_stream():
    """Send a prompt to Claude Code and stream the response via SSE."""
    if not connection_state["connected"]:
        return jsonify({"success": False, "error": "Not connected"}), 400

    data = request.get_json()
    prompt = data.get("prompt", "").strip() if data else ""
    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"}), 400

    # Prepend any attached document text to the prompt
    file_ids = data.get("file_ids", [])
    if file_ids:
        doc_parts = []
        for fid in file_ids:
            doc = uploaded_docs.get(fid)
            if doc:
                doc_parts.append(f"--- Document: {doc['filename']} ---\n{doc['text']}\n--- End of {doc['filename']} ---")
        if doc_parts:
            prompt = "\n\n".join(doc_parts) + "\n\n" + prompt

    conversation_id = data.get("conversation_id")
    mode = data.get("mode", "fast")  # "fast" or "deep"

    if mode == "deep":
        stream_kwargs = {
            "conversation_id": conversation_id,
            "allow_tools": True,
            "max_turns": 5,
        }
    else:
        # Fast mode: Sonnet, no tools, single turn — answers in seconds
        stream_kwargs = {
            "conversation_id": conversation_id,
            "allow_tools": False,
            "max_turns": 1,
            "model": "claude-sonnet-4-6",
        }

    output_queue = queue.Queue()
    thread = threading.Thread(
        target=run_prompt_streaming,
        args=(prompt, output_queue),
        kwargs=stream_kwargs,
        daemon=True,
    )
    thread.start()

    def generate():
        while True:
            item = output_queue.get()
            if item is None:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


# ─── API: Routines ───────────────────────────────────────────────────────────


# MVP: hardcoded routines. Future: stored in CLAUDE.md or a routines.json
DEFAULT_ROUTINES = {
    "morning": {
        "name": "Morning Routine",
        "icon": "sunrise",
        "steps": [
            "Review my calendar for today and flag meetings I need to prepare for",
            "Check for any new Workplace posts or updates from my team",
            "Fetch my open tasks and sort by priority",
            "Give me a summary of my top 3 priorities for the day",
        ],
    },
    "evening": {
        "name": "EOD Debrief",
        "icon": "moon",
        "steps": [
            "Summarize everything I accomplished today",
            "Save any important learnings or decisions to memory",
            "Flag any items that need attention tomorrow",
            "Update project statuses based on today's work",
        ],
    },
}

ROUTINES_FILE = os.path.join(os.path.dirname(__file__), "routines.json")


def load_routines():
    if os.path.exists(ROUTINES_FILE):
        with open(ROUTINES_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_ROUTINES.copy()


def save_routines(routines):
    with open(ROUTINES_FILE, "w") as f:
        json.dump(routines, f, indent=2)


@app.route("/api/routines", methods=["GET"])
def api_routines_get():
    return jsonify({"success": True, "routines": load_routines()})


@app.route("/api/routines/<routine_id>/add-step", methods=["POST"])
def api_routines_add_step(routine_id):
    """Add a step to a routine."""
    data = request.get_json()
    step = data.get("step", "").strip() if data else ""
    if not step:
        return jsonify({"success": False, "error": "No step provided"}), 400

    routines = load_routines()
    if routine_id not in routines:
        return jsonify({"success": False, "error": "Routine not found"}), 404

    routines[routine_id]["steps"].append(step)
    save_routines(routines)
    return jsonify({"success": True, "routines": routines})


@app.route("/api/routines/<routine_id>/run", methods=["POST"])
def api_routines_run(routine_id):
    """Run a routine by sending all steps as a single prompt to Claude."""
    if not connection_state["connected"]:
        return jsonify({"success": False, "error": "Not connected"}), 400

    routines = load_routines()
    if routine_id not in routines:
        return jsonify({"success": False, "error": "Routine not found"}), 404

    routine = routines[routine_id]
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(routine["steps"]))
    prompt = f"Please execute the following routine steps in order:\n\n{steps_text}\n\nProvide a summary of each step's results."

    data = request.get_json() or {}
    conversation_id = data.get("conversation_id")
    result = run_prompt(prompt, timeout=300, conversation_id=conversation_id, allow_tools=True, max_turns=5)
    return jsonify(result)


# ─── API: File Upload ─────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store of extracted text from uploads (keyed by file_id)
uploaded_docs = {}

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload a document and extract its text content."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": f"Unsupported file type: .{ext}. Use PDF, TXT, MD, or CSV."}), 400

    # Read file content
    file_bytes = file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return jsonify({"success": False, "error": "File too large (max 20 MB)"}), 400

    # Extract text
    try:
        if ext == "pdf":
            import io
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            if not text.strip():
                return jsonify({"success": False, "error": "Could not extract text from PDF (may be scanned/image-based)"}), 400
        else:
            text = file_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to read file: {str(e)}"}), 400

    # Store with a unique ID
    file_id = str(uuid.uuid4())[:8]
    # Truncate very long docs to avoid overloading the prompt
    max_chars = 80000
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]

    uploaded_docs[file_id] = {
        "filename": file.filename,
        "text": text,
        "char_count": len(text),
        "truncated": truncated,
    }

    return jsonify({
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "char_count": len(text),
        "truncated": truncated,
    })


@app.route("/api/upload/<file_id>", methods=["DELETE"])
def api_upload_delete(file_id):
    """Remove an uploaded document from memory."""
    uploaded_docs.pop(file_id, None)
    return jsonify({"success": True})


# ─── API: CLAUDE.md info ─────────────────────────────────────────────────────


@app.route("/api/claudemd/path")
def api_claudemd_path():
    """Return the detected CLAUDE.md path."""
    path = find_claudemd()
    return jsonify({
        "found": path is not None,
        "path": str(path) if path else None,
    })


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("MSB_PORT", os.environ.get("BIAJ_PORT", 5151)))
    print(f"\n  My Second Brain is running at: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
