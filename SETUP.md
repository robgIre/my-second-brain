# Brain In A Jar — Setup Guide

## What is it?

Brain In A Jar is a web dashboard for your Second Brain (Claude Code + PARA workspace). Instead of typing in a terminal, you open a web page, connect your brain, and tell it what to do in plain language. It handles morning routines, end-of-day debriefs, meeting prep, task management, and anything else you'd normally ask Claude Code.

## Requirements

- An On-Demand server (OD) with Google Drive mounted
- Python 3 (pre-installed on most ODs)
- Claude Code CLI (pre-installed on most ODs)

## Quick Setup (one command)

Open your OD terminal and paste:

```bash
bash ~/Google\ Drive/My\ Drive/claude/01_projects/13_brain_in_a_jar/src/setup.sh
```

That's it. The script will:
1. Find the project on your Google Drive
2. Check Python is installed
3. Install Flask (the only dependency)
4. Check Claude Code is available
5. Start the server and print the URL

## Open the App

After running the setup command, open your browser to:

```
http://localhost:5151
```

## Using the App

### First time
1. Click **"Connect Brain"** on the home page — this tests that Claude Code CLI is working
2. Go to **About Me** and fill in your details — this syncs to your CLAUDE.md so Claude always knows who you are
3. Check **My Routines** — customise the morning and evening routines to match your workflow

### Daily use
- **Morning**: Open the app, click "Run Now" on your Morning Routine
- **During the day**: Use "Build Now" to ask your brain anything in plain language
- **Evening**: Click "Run Now" on your EOD Debrief to wrap up the day

### Stopping the server
Press `Ctrl+C` in the terminal where setup.sh is running.

### Restarting
Run the same setup command again — it skips already-installed deps and starts the server.

## Troubleshooting

**"Claude Code CLI not found"**
- Make sure Claude Code is installed. See: Building Your AI Toolkit at Meta (wiki)
- Try running `claude --version` in your terminal

**"CLAUDE.md not found"**
- The app looks for CLAUDE.md in your Google Drive. Make sure Google Drive is mounted.
- Run `ls ~/Google\ Drive/My\ Drive/claude/CLAUDE.md` to check

**Port already in use**
- Set a different port: `BIAJ_PORT=5152 bash setup.sh`

**Google Drive not mounted**
- Run `mclone mount` or check your OD's Google Drive configuration

## Feedback

Found a bug or have an idea? Tell Rob Goldsmith (robgoldsmith) on Workplace or GChat.
