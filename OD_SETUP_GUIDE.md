# My Second Brain — OD Setup Guide

Hey! This guide will get you up and running on a Meta On-Demand server (OD). The app needs Claude Code CLI to work properly, which is available on ODs but not on your regular Windows/Mac laptop.

---

## Why an OD?

My Second Brain is a wrapper around Claude Code CLI. Claude Code runs on ODs — it won't work from your regular laptop. Your Windows machine was giving you errors because pip and Flask weren't set up, but even if they were, the core features (Build Now, Morning Routine, etc.) need Claude Code CLI running behind the scenes.

---

## Step 1: Get an OD

1. Type **od** in your bunnylol bar (browser address bar) and hit Enter
2. You'll see the On Demand page with your workspaces listed
3. Click **"Join Workspace"** on your default workspace, or click **"Create New Workspace"** if you don't have one
4. Wait for it to spin up (usually 1-2 minutes)
5. Click **"Open"** to launch VS Code connected to your OD

---

## Step 2: Open a terminal

In VS Code on your OD, open a terminal:
- Press **Ctrl + `** (backtick) to open the built-in terminal
- Or go to **Terminal > New Terminal** in the menu

---

## Step 3: One-command install

Paste this entire line into your terminal and hit Enter:

```bash
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```

That's it. The script will:
1. Find the project
2. Check Python is installed (it's pre-installed on ODs)
3. Install Flask (the only dependency)
4. Check Claude Code CLI is available
5. Start the server

You should see something like:

```
  ╔══════════════════════════════════╗
  ║     My Second Brain — Setup      ║
  ╚══════════════════════════════════╝

[1/4] Found project at: /home/you/my-second-brain
[2/4] Python 3.x.x
[3/4] Installing dependencies...
      Done.
[4/4] Claude Code CLI found.

  Starting My Second Brain...

  Open this URL in your browser:

    http://localhost:5151
```

---

## Step 4: Open the app

1. Open your browser and go to: **http://localhost:5151**
2. Click the green **"Connect Brain"** button
3. You should see "Your brain is active"

**Keep the terminal window open** — if you close it, the server stops.

---

## Step 5: Set up your profile

1. Click **"About Me"** in the sidebar
2. Fill in your name, role, team, manager, location
3. Write a short background about what you do
4. Click **"Save & Sync"**

This teaches your brain who you are so it has context every time you use it.

---

## What to try first

- **Morning Routine** — click "Run Now" on the home page
- **Build Now** — type anything in plain language, e.g. "What's on my calendar today?"
- **Evening Routine** — wrap up your day with an EOD debrief

---

## Restarting (after you close it)

```bash
cd ~/my-second-brain && bash setup.sh
```

## Updating (when Rob pushes changes)

```bash
cd ~/my-second-brain && git pull && bash setup.sh
```

---

## Troubleshooting

**"Claude Code CLI not found"**
- Run `claude --version` to check if it's installed
- If not, run: `curl -fsSL https://cli.anthropic.com/install.sh | sh`
- Then close and reopen your terminal

**Port already in use**
- Start on a different port: `BIAJ_PORT=5152 bash setup.sh`

**Page won't load**
- Make sure the terminal with the server is still running
- Check you're using the right URL: http://localhost:5151

---

Questions? Message Rob Goldsmith on GChat.
