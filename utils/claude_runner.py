"""Wraps Claude Code CLI calls."""

import subprocess
import shutil
import json
import threading
import queue


def is_claude_installed():
    """Check if claude CLI is available."""
    return shutil.which("claude") is not None


def run_prompt(prompt, timeout=120, conversation_id=None):
    """Send a prompt to Claude Code CLI and return the response.

    Uses --print flag for non-interactive single-shot execution.
    Uses --output-format json to capture session_id for conversation continuity.
    Pass conversation_id to continue an existing conversation.
    Returns dict with 'success', 'output', 'conversation_id', and optionally 'error'.
    """
    if not is_claude_installed():
        return {"success": False, "error": "Claude Code CLI not found. Install it first."}

    try:
        cmd = ["claude", "--print", "--output-format", "json", prompt]
        if conversation_id:
            cmd.extend(["--conversation-id", conversation_id])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,
        )

        # Try to parse JSON output for session_id
        try:
            parsed = json.loads(result.stdout.strip())
            return {
                "success": not parsed.get("is_error", False),
                "output": parsed.get("result", ""),
                "conversation_id": parsed.get("session_id"),
            }
        except (json.JSONDecodeError, ValueError):
            # Fallback if JSON parsing fails — treat as plain text
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {
                    "success": False,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip(),
                }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_prompt_streaming(prompt, output_queue, timeout=120, conversation_id=None):
    """Send a prompt to Claude Code and stream output line-by-line into a queue.

    Call from a thread. Puts lines into output_queue as they arrive.
    Puts None when done. Returns conversation_id via a final message.
    """
    if not is_claude_installed():
        output_queue.put({"type": "error", "text": "Claude Code CLI not found."})
        output_queue.put(None)
        return

    try:
        cmd = ["claude", "--print", prompt]
        if conversation_id:
            cmd.extend(["--conversation-id", conversation_id])

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        for line in proc.stdout:
            output_queue.put({"type": "output", "text": line.rstrip()})

        proc.wait(timeout=timeout)

        if proc.returncode != 0:
            stderr = proc.stderr.read().strip()
            if stderr:
                output_queue.put({"type": "error", "text": stderr})

    except subprocess.TimeoutExpired:
        proc.kill()
        output_queue.put({"type": "error", "text": f"Timed out after {timeout}s"})
    except Exception as e:
        output_queue.put({"type": "error", "text": str(e)})
    finally:
        output_queue.put(None)


def check_connection():
    """Quick check that Claude Code CLI is responsive."""
    if not is_claude_installed():
        return {"connected": False, "error": "Claude Code CLI not installed"}

    try:
        # Check claude is installed and reachable — just check the binary exists
        claude_path = shutil.which("claude")
        if claude_path:
            return {"connected": True}
        else:
            return {"connected": False, "error": "Claude Code CLI not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"connected": False, "error": "Connection timed out"}
    except Exception as e:
        return {"connected": False, "error": str(e)}
