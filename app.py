"""Brain In A Jar — Flask backend for the Second Brain Command Center."""

import json
import os
import queue
import threading
import time

from flask import Flask, jsonify, render_template, request, Response, send_from_directory

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

    result = run_prompt(prompt, timeout=180)
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

    output_queue = queue.Queue()
    thread = threading.Thread(
        target=run_prompt_streaming,
        args=(prompt, output_queue),
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
            "Check what emails I received overnight and summarize the important ones",
            "Review my calendar for today and flag meetings I need to prepare for",
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

    result = run_prompt(prompt, timeout=300)
    return jsonify(result)


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
    port = int(os.environ.get("BIAJ_PORT", 5151))
    print(f"\n  Brain In A Jar is running at: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
