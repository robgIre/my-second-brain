"""Wraps Claude Code CLI calls."""

import subprocess
import shutil
import json
import threading
import queue


def is_claude_installed():
    """Check if claude CLI is available."""
    return shutil.which("claude") is not None


def run_prompt(prompt, timeout=120, conversation_id=None, allow_tools=False):
    """Send a prompt to Claude Code CLI and return the response.

    Uses --print flag for non-interactive single-shot execution.
    Uses --output-format json to capture session_id for conversation continuity.
    Pass conversation_id to continue an existing conversation.
    Pass allow_tools=True to pre-approve Bash, Read, and Write tools.
    Returns dict with 'success', 'output', 'conversation_id', and optionally 'error'.
    """
    if not is_claude_installed():
        return {"success": False, "error": "Claude Code CLI not found. Install it first."}

    try:
        cmd = ["claude", "-p", "-", "--output-format", "json"]
        if allow_tools:
            for tool in ["Bash(*)", "Read", "Write", "Edit", "Skill", "mcp__*"]:
                cmd.extend(["--allowedTools", tool])
        if conversation_id:
            cmd.extend(["-c", conversation_id])

        result = subprocess.run(
            cmd,
            input=prompt,
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


def run_prompt_streaming(prompt, output_queue, timeout=600, conversation_id=None, allow_tools=False, model=None):
    """Send a prompt to Claude Code and stream output line-by-line into a queue.

    Uses --output-format stream-json to get real-time streaming events.
    Call from a thread. Puts dicts into output_queue as they arrive.
    Puts None when done.
    """
    if not is_claude_installed():
        output_queue.put({"type": "error", "text": "Claude Code CLI not found. Is it installed on this server?"})
        output_queue.put(None)
        return

    proc = None
    try:
        cmd = ["claude", "-p", "--output-format", "stream-json", "--include-partial-messages"]
        if model:
            cmd.extend(["--model", model])
        if allow_tools:
            for tool in ["Bash(*)", "Read", "Write", "Edit", "Skill", "mcp__*"]:
                cmd.extend(["--allowedTools", tool])
        if conversation_id:
            cmd.extend(["-c", conversation_id])

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered — critical for low-latency streaming
        )

        # Send prompt via stdin — handle broken pipe gracefully
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except (BrokenPipeError, OSError) as e:
            output_queue.put({"type": "error", "text": f"Claude CLI rejected input: {e}"})
            _cleanup_proc(proc)
            return

        session_id = None
        sent_chars = 0  # Track how much text we've already sent
        import time as _time

        deadline = _time.time() + timeout

        # Read stream-json events using readline() for immediate delivery
        # (iterating proc.stdout directly uses an 8KB buffer that causes huge latency)
        while True:
            line = proc.stdout.readline()
            if not line:
                break  # EOF — process finished
            if _time.time() > deadline:
                output_queue.put({"type": "error", "text": f"Claude CLI timed out after {timeout}s"})
                _cleanup_proc(proc)
                return

            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            msg_type = event.get("type", "")

            if msg_type == "result":
                session_id = event.get("session_id")
                result_text = event.get("result", "")
                if result_text and len(result_text) > sent_chars:
                    output_queue.put({"type": "text", "text": result_text[sent_chars:]})
                    sent_chars = len(result_text)
            elif msg_type == "assistant":
                message = event.get("message", {})
                content_blocks = message.get("content", [])
                full_text = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        full_text += block.get("text", "")
                if full_text and len(full_text) > sent_chars:
                    output_queue.put({"type": "text", "text": full_text[sent_chars:]})
                    sent_chars = len(full_text)

        proc.wait(timeout=30)

        if proc.returncode != 0:
            stderr = proc.stderr.read().strip()
            error_msg = stderr or f"Claude CLI exited with code {proc.returncode}"
            # Only report if we haven't sent any text (otherwise it may just be a warning)
            if sent_chars == 0:
                output_queue.put({"type": "error", "text": error_msg})
            else:
                # Log it but don't overwrite the output
                output_queue.put({"type": "error", "text": f"\n[CLI warning: {error_msg}]"})

        output_queue.put({"type": "session", "session_id": session_id})

    except subprocess.TimeoutExpired:
        _cleanup_proc(proc)
        output_queue.put({"type": "error", "text": f"Timed out after {timeout}s"})
    except Exception as e:
        _cleanup_proc(proc)
        output_queue.put({"type": "error", "text": f"Unexpected error: {e}"})
    finally:
        output_queue.put(None)


def _cleanup_proc(proc):
    """Safely terminate a subprocess."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


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
