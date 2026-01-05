#!/usr/bin/env python3
"""
SessionStart hook: Rename session based on git branch.
- First session on branch: "BRANCH"
- Subsequent sessions: "BRANCH (2)", "BRANCH (3)", etc.

Uses list_sessions.py to get existing session names.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

DEBUG_LOG = Path("/tmp/debug.log")
SCRIPT_DIR = Path(__file__).parent


def log(message: str) -> None:
    """Append message to debug log."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEBUG_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def get_git_branch(cwd: str) -> str | None:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_project_dir(cwd: str) -> Path:
    """Get Claude project directory for this cwd."""
    project_path = cwd.replace("/", "-")
    return Path.home() / ".claude" / "projects" / project_path


def get_existing_session_names(cwd: str) -> list[str]:
    """Get session names using list_sessions.py script."""
    list_sessions_script = SCRIPT_DIR / "list_sessions.py"

    if not list_sessions_script.exists():
        log(f"list_sessions.py not found at {list_sessions_script}")
        return []

    # Extract project filter from cwd (e.g., "bcs-lakehouse" from full path)
    project_filter = Path(cwd).name

    try:
        result = subprocess.run(
            [sys.executable, str(list_sessions_script), project_filter],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            log(f"list_sessions.py failed: {result.stderr}")
            return []

        # Parse output: "session_id  name"
        names = []
        for line in result.stdout.strip().split("\n"):
            if line and "  " in line:
                # Format: "uuid  session_name"
                parts = line.split("  ", 1)
                if len(parts) == 2:
                    names.append(parts[1])

        log(f"Found {len(names)} sessions via list_sessions.py")
        return names

    except Exception as e:
        log(f"Error running list_sessions.py: {e}")
        return []


def count_branch_sessions(branch: str, session_names: list[str]) -> int:
    """Count how many sessions match this branch (exact or numbered)."""
    pattern = re.compile(rf"^{re.escape(branch)}(?: \(\d+\))?$")
    count = sum(1 for name in session_names if pattern.match(name))
    return count


def generate_session_name(branch: str, existing_names: list[str]) -> str:
    """
    Generate session name based on branch.
    - If no session with branch name exists: return "BRANCH"
    - If exists: return "BRANCH (N)" where N is count + 1
    """
    count = count_branch_sessions(branch, existing_names)

    if count == 0:
        return branch

    return f"{branch} ({count + 1})"


def rename_session(session_id: str, new_name: str, cwd: str) -> bool:
    """Rename session by appending custom-title to JSONL file."""
    project_dir = get_project_dir(cwd)
    session_file = project_dir / f"{session_id}.jsonl"

    if not session_file.exists():
        log(f"Session file not found: {session_file}")
        return False

    record = {
        "type": "custom-title",
        "customTitle": new_name,
        "sessionId": session_id
    }

    try:
        with open(session_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        return True
    except Exception as e:
        log(f"Error writing: {e}")
        return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        log(f"JSON parse error: {e}")
        sys.exit(1)

    session_id = input_data.get("session_id", "unknown")
    cwd = input_data.get("cwd", "")
    source = input_data.get("source", "unknown")

    log(f"SessionStart - id: {session_id} | cwd: {cwd} | source: {source}")

    if source != "startup":
        log(f"Skipping rename for source: {source}")
        return

    # Get git branch
    branch = get_git_branch(cwd)
    if not branch:
        log("No git branch found, skipping rename")
        return

    if branch == "main":
        log("Skipping rename for main branch")
        return

    # Get existing session names
    existing_names = get_existing_session_names(cwd)
    log(f"Found {len(existing_names)} existing session names")

    # Generate name
    new_name = generate_session_name(branch, existing_names)
    log(f"Renaming to: {new_name}")

    if rename_session(session_id, new_name, cwd):
        log(f"SUCCESS: {new_name}")
        output = {
            "continue": True,
            "systemMessage": f"Session: {new_name}"
        }
    else:
        log("FAILED")
        output = {
            "continue": True,
            "systemMessage": f"Failed to rename session to: {new_name}"
        }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
