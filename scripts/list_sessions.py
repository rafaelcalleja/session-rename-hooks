#!/usr/bin/env python3
"""
List Claude Code sessions with their IDs and custom names.
Usage: list_sessions.py [project_path]
"""

import json
import sys
from pathlib import Path


def get_sessions(filter_project: str = None):
    """Find all sessions and their custom names."""
    claude_projects = Path.home() / ".claude" / "projects"

    if not claude_projects.exists():
        print("No Claude projects directory found")
        return []

    sessions = []

    for project_dir in claude_projects.iterdir():
        if not project_dir.is_dir():
            continue

        # Filter by project if specified
        if filter_project and filter_project not in project_dir.name:
            continue

        project_name = project_dir.name

        for jsonl_file in project_dir.glob("*.jsonl"):
            session_id = jsonl_file.stem
            # Skip agent sessions
            if session_id.startswith("agent-"):
                continue
            custom_name = None
            summary = None

            try:
                with open(jsonl_file) as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                            if record.get("type") == "custom-title":
                                custom_name = record.get("customTitle")
                            elif record.get("type") == "summary":
                                summary = record.get("summary")
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

            sessions.append({
                "project": project_name,
                "session_id": session_id,
                "custom_name": custom_name,
                "summary": summary,
            })

    return sessions


def main():
    filter_project = sys.argv[1] if len(sys.argv) > 1 else None
    sessions = get_sessions(filter_project)

    if not sessions:
        print("No sessions found")
        return

    for s in sessions:
        name = s["custom_name"] or s["summary"]
        if not name:
            continue
        print(f"{s['session_id']}  {name[:50]}")


if __name__ == "__main__":
    main()
