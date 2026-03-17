# My Second Brain — Setup Guide

## What is it?

My Second Brain is a web dashboard for Claude Code. Instead of typing in a terminal, you open a web page, connect your brain, and tell it what to do in plain language. It handles morning routines, end-of-day debriefs, meeting prep, task management, and anything else you'd normally ask Claude Code.

## Requirements

- An On-Demand server (OD) or Dev Server
- Python 3 (pre-installed on most ODs)
- Claude Code CLI (pre-installed on most ODs)

## Quick Setup (one command)

Connect to your server and paste:

```bash
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```

That's it. The script will:
1. Find the project
2. Check Python is installed
3. Create a virtual environment and install Flask
4. Check Claude Code is available
5. Start the server and print the URL

## Open the App

After running the setup command, open your browser to:

```
http://localhost:5151
```

**Dev Server users:** Make sure you SSH'd in with port forwarding:
```
ssh -L 5151:localhost:5151 your-devserver-name
```

## Using the App

### First time
1. Click **"Connect Brain"** on the home page — this tests that Claude Code CLI is working
2. Go to **About Me** and fill in your details — this syncs to your CLAUDE.md so Claude always knows who you are
3. Check **Quick Routines** — customise the morning and evening routines to match your workflow

### Daily use
- **Morning**: Open the app, click "Run Now" on your Morning Routine
- **During the day**: Use "Ask My Brain" to ask your brain anything in plain language
- **Evening**: Click "Run Now" on your EOD Debrief to wrap up the day

### Stopping the server
Press `Ctrl+C` in the terminal where setup.sh is running.

### Restarting
Run the same setup command again — it skips already-installed deps and starts the server.

## Troubleshooting

**"Claude Code CLI not found"**
- Make sure Claude Code is installed. See: Building Your AI Toolkit at Meta (wiki)
- Try running `claude --version` in your terminal

**Port already in use**
- Set a different port: `MSB_PORT=5152 bash setup.sh`

**Page won't load**
- Make sure the terminal with the server is still running
- Dev Server users: make sure you used `-L 5151:localhost:5151` when SSH'ing in

## Feedback

Found a bug or have an idea? Tell Rob Goldsmith (robgoldsmith) on GChat.
