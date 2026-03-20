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

# Day view cache — meetings + brief, reset daily
day_cache = {"date": None, "meetings": None, "brief": None, "meetings_loading": False, "brief_loading": False}


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

    # Prepend any attached document text
    file_ids = data.get("file_ids", []) if data else []
    if file_ids:
        doc_parts = []
        for fid in file_ids:
            doc = uploaded_docs.get(fid)
            if doc:
                doc_parts.append(f"--- Document: {doc['filename']} ---\n{doc['text']}\n--- End of {doc['filename']} ---")
        if doc_parts:
            prompt = "\n\n".join(doc_parts) + "\n\n" + prompt

    conversation_id = data.get("conversation_id") if data else None
    mode = data.get("mode", "fast") if data else "fast"

    if mode == "deep":
        result = run_prompt(prompt, timeout=600, conversation_id=conversation_id, allow_tools=True)
    else:
        result = run_prompt(prompt, timeout=600, conversation_id=conversation_id, allow_tools=False)

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
        }
    else:
        stream_kwargs = {
            "conversation_id": conversation_id,
            "allow_tools": False,
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
    result = run_prompt(prompt, timeout=300, conversation_id=conversation_id, allow_tools=True)
    return jsonify(result)


# ─── API: Day View (Meetings + Morning Brief) ───────────────────────────────

def reset_day_cache_if_needed():
    today = time.strftime("%Y-%m-%d")
    if day_cache["date"] != today:
        day_cache["date"] = today
        day_cache["meetings"] = None
        day_cache["brief"] = None
        day_cache["meetings_loading"] = False
        day_cache["brief_loading"] = False


def fetch_meetings_background():
    """Background thread to fetch today's meetings."""
    day_cache["meetings_loading"] = True
    try:
        prompt = (
            "List my meetings for today in chronological order. "
            "For each meeting give the title, start time, end time, and key attendees. "
            "Format each meeting on its own line like: HH:MM - HH:MM | Meeting Title | Attendees\n"
            "Example: 10:00 - 10:30 | Team Sync | Alice, Bob\n"
            "If you cannot access my calendar, say 'Calendar not available'."
        )
        result = run_prompt(prompt, timeout=120, conversation_id=None, allow_tools=True)
        day_cache["meetings"] = result.get("output", "No meetings found")
    except Exception as e:
        day_cache["meetings"] = f"Could not fetch meetings: {str(e)}"
    day_cache["meetings_loading"] = False


def fetch_brief_background():
    """Background thread to generate the morning brief."""
    day_cache["brief_loading"] = True
    try:
        # Include scratchpad from yesterday if available
        yesterday_notes = ""
        if os.path.exists(os.path.join(os.path.dirname(__file__), "scratchpad.json")):
            with open(os.path.join(os.path.dirname(__file__), "scratchpad.json"), "r") as f:
                pad_data = json.load(f)
            # Find yesterday's notes
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            if yesterday in pad_data and pad_data[yesterday].strip():
                yesterday_notes = f"\n\nYesterday's notes from my scratchpad:\n{pad_data[yesterday]}\n"

        prompt = (
            "Give me a concise morning brief for today. Include:\n"
            "1. My meetings for today (list them with times)\n"
            "2. Any open tasks or follow-ups that need attention\n"
            "3. Carry-over items from yesterday that I should remember\n"
            f"{yesterday_notes}"
            "\nKeep it short and actionable — bullet points, not paragraphs."
        )
        result = run_prompt(prompt, timeout=180, conversation_id=None, allow_tools=True)
        day_cache["brief"] = result.get("output", "Could not generate brief")
    except Exception as e:
        day_cache["brief"] = f"Could not generate brief: {str(e)}"
    day_cache["brief_loading"] = False


@app.route("/api/dayview/meetings", methods=["GET"])
def api_dayview_meetings():
    """Return cached meetings or trigger a fetch."""
    reset_day_cache_if_needed()
    return jsonify({
        "success": True,
        "meetings": day_cache["meetings"],
        "loading": day_cache["meetings_loading"],
    })


@app.route("/api/dayview/meetings", methods=["POST"])
def api_dayview_meetings_fetch():
    """Trigger a meetings fetch if not already loading."""
    if not connection_state["connected"]:
        return jsonify({"success": False, "error": "Not connected"}), 400
    reset_day_cache_if_needed()
    if not day_cache["meetings_loading"]:
        day_cache["meetings"] = None
        threading.Thread(target=fetch_meetings_background, daemon=True).start()
    return jsonify({"success": True, "status": "fetching"})


@app.route("/api/dayview/brief", methods=["GET"])
def api_dayview_brief():
    """Return cached morning brief or trigger a fetch."""
    reset_day_cache_if_needed()
    return jsonify({
        "success": True,
        "brief": day_cache["brief"],
        "loading": day_cache["brief_loading"],
    })


@app.route("/api/dayview/brief", methods=["POST"])
def api_dayview_brief_fetch():
    """Trigger a brief generation if not already loading."""
    if not connection_state["connected"]:
        return jsonify({"success": False, "error": "Not connected"}), 400
    reset_day_cache_if_needed()
    if not day_cache["brief_loading"]:
        day_cache["brief"] = None
        threading.Thread(target=fetch_brief_background, daemon=True).start()
    return jsonify({"success": True, "status": "fetching"})


# ─── API: Scheduled Routines ─────────────────────────────────────────────────

SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), "schedules.json")
scheduled_results = {}  # In-memory store of auto-run results


def load_schedules():
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_schedules(schedules):
    with open(SCHEDULES_FILE, "w") as f:
        json.dump(schedules, f, indent=2)


@app.route("/api/schedules", methods=["GET"])
def api_schedules_get():
    return jsonify({"success": True, "schedules": load_schedules()})


@app.route("/api/schedules", methods=["POST"])
def api_schedules_save():
    data = request.get_json()
    if data is None:
        return jsonify({"success": False, "error": "No data"}), 400
    save_schedules(data)
    return jsonify({"success": True})


@app.route("/api/schedules/last-result", methods=["GET"])
def api_schedules_last_result():
    return jsonify({"success": True, "results": scheduled_results})


def run_scheduled_routine(routine_id):
    """Run a routine in the background (called by scheduler)."""
    if not connection_state["connected"]:
        return

    routines = load_routines()
    if routine_id not in routines:
        return

    routine = routines[routine_id]
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(routine["steps"]))

    # Include scratchpad notes for EOD debrief
    extra_context = ""
    if routine_id == "evening":
        pad = load_scratchpad()
        if pad.get("notes"):
            extra_context = f"\n\nHere are my notes from today's scratchpad — use these as context:\n\n{pad['notes']}\n"

    prompt = f"Please execute the following routine steps in order:\n\n{steps_text}{extra_context}\n\nProvide a summary of each step's results."

    result = run_prompt(prompt, timeout=300, conversation_id=None, allow_tools=True)
    scheduled_results[routine_id] = {
        "output": result.get("output", ""),
        "success": result.get("success", False),
        "ran_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def scheduler_loop():
    """Background thread that checks schedules every 60 seconds."""
    ran_today = {}
    while True:
        time.sleep(60)
        try:
            schedules = load_schedules()
            now = time.strftime("%H:%M")
            today = time.strftime("%Y-%m-%d")

            for routine_id, config in schedules.items():
                if not config.get("enabled"):
                    continue
                scheduled_time = config.get("time", "")
                if now == scheduled_time and ran_today.get(routine_id) != today:
                    ran_today[routine_id] = today
                    threading.Thread(
                        target=run_scheduled_routine,
                        args=(routine_id,),
                        daemon=True,
                    ).start()
        except Exception:
            pass  # Don't crash the scheduler


# Start scheduler on app boot
scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()


# ─── API: Scratchpad (Daily Log) ──────────────────────────────────────────────

SCRATCHPAD_FILE = os.path.join(os.path.dirname(__file__), "scratchpad.json")


def load_scratchpad():
    if os.path.exists(SCRATCHPAD_FILE):
        with open(SCRATCHPAD_FILE, "r") as f:
            data = json.load(f)
        # Return today's notes only; keep history
        today = time.strftime("%Y-%m-%d")
        return {"today": today, "notes": data.get(today, ""), "history": data}
    return {"today": time.strftime("%Y-%m-%d"), "notes": "", "history": {}}


def save_scratchpad_notes(notes):
    today = time.strftime("%Y-%m-%d")
    data = {}
    if os.path.exists(SCRATCHPAD_FILE):
        with open(SCRATCHPAD_FILE, "r") as f:
            data = json.load(f)
    data[today] = notes
    with open(SCRATCHPAD_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/api/scratchpad", methods=["GET"])
def api_scratchpad_get():
    return jsonify({"success": True, **load_scratchpad()})


@app.route("/api/scratchpad", methods=["POST"])
def api_scratchpad_save():
    data = request.get_json()
    if data is None or "notes" not in data:
        return jsonify({"success": False, "error": "No notes provided"}), 400
    save_scratchpad_notes(data["notes"])
    return jsonify({"success": True})


# ─── API: Action Items ───────────────────────────────────────────────────────

ACTIONS_FILE = os.path.join(os.path.dirname(__file__), "actionitems.json")


def load_action_items():
    if os.path.exists(ACTIONS_FILE):
        with open(ACTIONS_FILE, "r") as f:
            return json.load(f)
    return []


def save_action_items(items):
    with open(ACTIONS_FILE, "w") as f:
        json.dump(items, f, indent=2)


@app.route("/api/actionitems", methods=["GET"])
def api_actionitems_get():
    return jsonify({"success": True, "items": load_action_items()})


@app.route("/api/actionitems", methods=["POST"])
def api_actionitems_save():
    data = request.get_json()
    if data is None or "items" not in data:
        return jsonify({"success": False, "error": "No items provided"}), 400
    save_action_items(data["items"])
    return jsonify({"success": True})


# ─── API: Quick Links ────────────────────────────────────────────────────────

QUICKLINKS_FILE = os.path.join(os.path.dirname(__file__), "quicklinks.json")


def load_quicklinks():
    if os.path.exists(QUICKLINKS_FILE):
        with open(QUICKLINKS_FILE, "r") as f:
            return json.load(f)
    return []


def save_quicklinks(links):
    with open(QUICKLINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)


@app.route("/api/quicklinks", methods=["GET"])
def api_quicklinks_get():
    return jsonify({"success": True, "links": load_quicklinks()})


@app.route("/api/quicklinks", methods=["POST"])
def api_quicklinks_save():
    data = request.get_json()
    if data is None or "links" not in data:
        return jsonify({"success": False, "error": "No links provided"}), 400
    save_quicklinks(data["links"])
    return jsonify({"success": True})


# ─── API: File Upload ─────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store of extracted text from uploads (keyed by file_id)
uploaded_docs = {}

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "csv"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


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
        return jsonify({"success": False, "error": "File too large (max 100 MB)"}), 400

    # Extract text
    MAX_PDF_PAGES = 50
    try:
        if ext == "pdf":
            import io
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_to_read = reader.pages[:MAX_PDF_PAGES]
            text = "\n\n".join(page.extract_text() or "" for page in pages_to_read)
            pages_truncated = len(reader.pages) > MAX_PDF_PAGES
            total_pages = len(reader.pages)
            if pages_truncated:
                text += f"\n\n[Note: PDF has {total_pages} pages. Extracted first {MAX_PDF_PAGES} pages.]"
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

    response = {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "char_count": len(text),
        "truncated": truncated,
    }

    # Add PDF page info if applicable
    if ext == "pdf":
        response["total_pages"] = total_pages
        response["pages_extracted"] = min(total_pages, MAX_PDF_PAGES)
        response["pages_truncated"] = pages_truncated

    return jsonify(response)


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
