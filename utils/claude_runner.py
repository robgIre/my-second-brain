"""Wraps Claude Code CLI calls."""

import subprocess
import shutil
import json
import threading
import queue


def is_claude_installed():
    """Check if claude CLI is available."""
    return shutil.which("claude") is not None


def run_prompt(prompt, timeout=120, conversation_id=None, allow_tools=False, max_turns=None):
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
        if max_turns is not None:
            cmd.extend(["--max-turns", str(max_turns)])
        if allow_tools:
            for tool in ["Bash(*)", "Read", "Write", "Edit", "mcp__*"]:
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


def run_prompt_streaming(prompt, output_queue, timeout=600, conversation_id=None, allow_tools=False, max_turns=None, model=None):
    """Send a prompt to Claude Code and stream output line-by-line into a queue.

    Call from a thread. Puts dicts into output_queue as they arrive.
    Puts None when done. Sends conversation_id via a final 'done' message.
    """
    if not is_claude_installed():
        output_queue.put({"type": "error", "text": "Claude Code CLI not found."})
        output_queue.put(None)
        return

    try:
        cmd = ["claude", "-p", "--output-format", "stream-json"]
        if model:
            cmd.extend(["--model", model])
        if max_turns is not None:
            cmd.extend(["--max-turns", str(max_turns)])
        if allow_tools:
            for tool in ["Bash(*)", "Read", "Write", "Edit", "mcp__*"]:
                cmd.extend(["--allowedTools", tool])
        if conversation_id:
            cmd.extend(["-c", conversation_id])

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Send prompt via stdin
        proc.stdin.write(prompt)
        proc.stdin.close()

        session_id = None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                msg_type = event.get("type", "")

                if msg_type == "assistant":
                    # Text content from assistant
                    content = event.get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            output_queue.put({"type": "text", "text": block["text"]})
                elif msg_type == "result":
                    # Final result with session_id
                    session_id = event.get("session_id")
                    result_text = event.get("result", "")
                    if result_text:
                        output_queue.put({"type": "result", "text": result_text})
                    if event.get("is_error"):
                        output_queue.put({"type": "error", "text": result_text or "Unknown error"})
            except (json.JSONDecodeError, ValueError):
                # Plain text fallback
                output_queue.put({"type": "text", "text": line})

        proc.wait(timeout=timeout)

        if proc.returncode != 0:
            stderr = proc.stderr.read().strip()
            if stderr:
                output_queue.put({"type": "error", "text": stderr})

        # Send session_id so frontend can continue the conversation
        output_queue.put({"type": "session", "session_id": session_id})

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
