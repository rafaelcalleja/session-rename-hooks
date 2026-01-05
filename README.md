# Session Rename Hooks

Automatically names Claude Code sessions based on the current git branch.

## Features

- First session on a branch uses the branch name (e.g., `feature-login`)
- Subsequent sessions get incremental numbers (e.g., `feature-login (2)`, `feature-login (3)`)
- Skips renaming for `main` branch
- Only activates on session startup (not resume)
- Provides user-visible feedback via system message

## Installation

### Option 1: Marketplace (Recommended)

```bash
# From Claude Code, run:
/plugin marketplace add rafaelcalleja/session-rename-hooks
/plugin install session-rename-hooks@rafaelcalleja-session-rename-hooks
```

### Option 2: Development/Testing

```bash
# Clone and use directly
git clone https://github.com/rafaelcalleja/session-rename-hooks.git
claude --plugin-dir ./session-rename-hooks
```

### Option 3: Direct Plugin Add

```bash
claude plugins add /path/to/session-rename-hooks
```

## Structure

```
session-rename-hooks/
├── .claude-plugin/
│   ├── marketplace.json    # Marketplace metadata
│   └── plugin.json         # Plugin manifest
├── hooks/
│   └── hooks.json          # Hook configuration (SessionStart)
├── scripts/
│   ├── session_rename.py   # Main hook script
│   └── list_sessions.py    # Helper to query existing sessions
└── README.md
```

## How It Works

1. On `SessionStart` event, the hook checks if the session was created at startup
2. Gets the current git branch name
3. Queries existing sessions to count how many use this branch name
4. Renames the session with the appropriate name/number
5. Shows a confirmation message to the user

## Debug Logs

Debug information is written to `/tmp/debug.log` for troubleshooting.

## License

MIT
