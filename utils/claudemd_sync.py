"""Reads and writes CLAUDE.md for About Me and Routine sync."""

import os
import re
from pathlib import Path

# Default locations to search for CLAUDE.md
CLAUDEMD_SEARCH_PATHS = [
    Path.home() / "Google Drive" / "My Drive" / "claude" / "CLAUDE.md",
    Path.home() / "Library" / "CloudStorage" / "GoogleDrive-*" / "My Drive" / "claude" / "CLAUDE.md",
    Path.home() / "gdrive" / "CLAUDE.md",
    Path.home() / ".claude" / "CLAUDE.md",
]


def find_claudemd():
    """Find the user's CLAUDE.md file. Returns Path or None."""
    import glob

    for pattern in CLAUDEMD_SEARCH_PATHS:
        matches = glob.glob(str(pattern))
        if matches:
            return Path(matches[0])
    return None


def read_claudemd():
    """Read and return the full CLAUDE.md content."""
    path = find_claudemd()
    if not path or not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def parse_about_me(content):
    """Extract About Me fields from CLAUDE.md content.

    Looks for the '## About Me' section and parses key fields.
    """
    if not content:
        return {}

    about = {}

    # Match common patterns in CLAUDE.md About Me sections
    patterns = {
        "name": r"\*\*(.+?)\*\*\s*[-—]\s*(.+?)(?:\n|$)",
        "team": r"\*\*Team\*\*:\s*(.+)",
        "manager": r"\*\*Manager\*\*:\s*(.+)",
        "started": r"\*\*Started\*\*:\s*(.+)",
        "location": r"\*\*Location\*\*:\s*(.+)",
    }

    # Find About Me section
    about_match = re.search(r"## About Me\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not about_match:
        return about

    section = about_match.group(1)

    # Extract name and role from the bold line
    name_match = re.search(patterns["name"], section)
    if name_match:
        about["name"] = name_match.group(1).strip()
        about["role"] = name_match.group(2).strip()

    for key in ["team", "manager", "started", "location"]:
        match = re.search(patterns[key], section)
        if match:
            about[key] = match.group(1).strip()

    # Extract background paragraph
    bg_match = re.search(r"\*\*Background\*\*:\s*(.+?)(?=\n\n|\n-|\n\*|\Z)", section, re.DOTALL)
    if bg_match:
        about["background"] = bg_match.group(1).strip()

    return about


def update_about_me(data):
    """Update the About Me section in CLAUDE.md.

    data: dict with keys like name, role, team, manager, location, started, background, preferences
    Returns True on success, False on failure.
    """
    path = find_claudemd()
    if not path:
        return False

    content = path.read_text(encoding="utf-8") if path.exists() else ""

    # Build the new About Me section
    lines = [
        "\n## About Me\n",
        f"\n**{data.get('name', 'Unknown')}** - {data.get('role', 'Unknown')}\n",
        f"\n- **Team**: {data.get('team', '')}",
        f"- **Manager**: {data.get('manager', '')}",
        f"- **Started**: {data.get('started', '')}",
        f"- **Location**: {data.get('location', '')}",
        f"\n**Background**: {data.get('background', '')}",
    ]

    if data.get("preferences"):
        lines.append(f"\n**Preferences**: {data['preferences']}")

    new_section = "\n".join(lines) + "\n"

    # Replace existing section or append
    if "## About Me" in content:
        content = re.sub(
            r"## About Me\s*\n.*?(?=\n## |\Z)",
            new_section.lstrip("\n"),
            content,
            flags=re.DOTALL,
        )
    else:
        content += "\n" + new_section

    path.write_text(content, encoding="utf-8")
    return True


def get_stats():
    """Get basic stats from the CLAUDE.md / workspace.

    Returns dict with memory_count, project_count, routine_count.
    """
    content = read_claudemd()
    if not content:
        return {"memories": 0, "projects": 0, "routines": 0}

    # Count projects from Active Projects table
    project_matches = re.findall(r"\|\s*\d+\s*\|", content)
    project_count = len(project_matches) // 2 if project_matches else 0

    # Count memories (lines in memory file)
    memory_path = Path.home() / ".claude" / "projects" / "-Users-robgoldsmith" / "memory" / "MEMORY.md"
    memory_count = 0
    if memory_path.exists():
        lines = memory_path.read_text().splitlines()
        memory_count = len([l for l in lines if l.strip() and not l.startswith("#")])

    return {
        "memories": memory_count,
        "projects": project_count,
        "routines": 2,  # hardcoded for MVP
    }
