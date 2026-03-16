# First Time Setup — Complete Guide

This guide is for people who have never used Git or the terminal before. If you already have Git and Claude Code installed, skip to Step 3.

---

## Step 1: Check if Git is installed

Open a terminal (see below for how), then type:

```
git --version
```

**If you see a version number** (e.g. `git version 2.39.0`) — you're good, skip to Step 2.

**If you get an error or a popup asking to install** — follow the instructions below for your platform.

### How to open a terminal

**Mac:**
- Press `Cmd + Space`, type **Terminal**, hit Enter

**Windows:**
- Press `Win + R`, type **cmd**, hit Enter

**Meta OD (VS Code in browser):**
- Press `Ctrl + `` (backtick) to open the built-in terminal
- Or go to Terminal > New Terminal in the menu

### How to install Git

**Mac:**
- When you type `git` for the first time, macOS will pop up asking to install Command Line Tools. Click **Install** and wait (takes 2-5 minutes).
- If no popup appears, run: `xcode-select --install`

**Windows:**
- Download Git from https://git-scm.com/download/win
- Run the installer with default settings
- Restart your terminal after installing

**Meta OD:**
- Git should already be installed. If not, run: `sudo apt-get install git`

---

## Step 2: Check if Claude Code is installed

In your terminal, type:

```
claude --version
```

**If you see a version number** — you're good, skip to Step 3.

**If you get "command not found"** — install Claude Code:

### Installing Claude Code on a Mac

1. Open your terminal
2. Run this command:
   ```
   curl -fsSL https://cli.anthropic.com/install.sh | sh
   ```
3. Close and reopen your terminal
4. Verify it works: `claude --version`
5. Run `claude` once to complete the initial setup (it will ask you to log in)

### Installing Claude Code on a Meta OD

1. Open the VS Code terminal on your OD
2. Run:
   ```
   curl -fsSL https://cli.anthropic.com/install.sh | sh
   ```
3. If that doesn't work, try the Meta-specific guide: https://www.internalfb.com/wiki/Thomas_Wu/Building_Your_AI_Toolkit_at_Meta/
4. Verify it works: `claude --version`

### Don't want to install Claude Code yet?

The app will still run without it — you can browse the interface, see how it looks, and explore the features. You just won't be able to connect or run real commands until Claude Code is installed.

---

## Step 3: Install My Second Brain

Copy and paste this entire block into your terminal and hit Enter:

```
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```

You'll see output like this:

```
  ╔══════════════════════════════════╗
  ║     My Second Brain — Setup      ║
  ╚══════════════════════════════════╝

[1/4] Found project at: /Users/you/my-second-brain
[2/4] Python 3.12.0
[3/4] Installing dependencies...
      Done.
[4/4] Claude Code CLI found.

  Starting My Second Brain...

  Open this URL in your browser:

    http://localhost:5151
```

**Keep this terminal window open** — it's running the server. If you close it, the app stops.

---

## Step 4: Open the app

1. Open your web browser (Chrome, Safari, Firefox — any will work)
2. Go to: **http://localhost:5151**
3. Click the green **"Connect Brain"** button
4. You should see "Your brain is active" — you're done!

---

## Step 5: Set up your profile

1. Click **"About Me"** in the sidebar
2. Fill in your name, role, team, manager, location
3. Write a short background about what you do
4. Click **"Save & Sync"**

This teaches your brain who you are. Every time you use it, it already knows your context.

---

## What to try

- **Morning Routine** — click "Run Now" on the home page. Your brain will check your emails, calendar, and tasks.
- **Build Now** — type anything: "Prepare me for my 2pm meeting", "Summarize my open tasks", "What's happening on the GAZ 3 project?"
- **Add steps** — click "+ Add to my morning" or "+ Add to my evening" to customise your routines.

---

## Troubleshooting

**"git: command not found"**
→ Git isn't installed. See Step 1 above.

**"claude: command not found"**
→ Claude Code isn't installed. See Step 2 above. The app will still run in demo mode.

**"Connect Brain" fails**
→ Claude Code may not be responding. Try running `claude --version` in a separate terminal to check.

**"Address already in use"**
→ The app is already running in another terminal. Either find and close that terminal, or start on a different port: `BIAJ_PORT=5152 python3 app.py`

**Page won't load in browser**
→ Make sure the terminal is still running (you should see the server output). Don't close the terminal window.

**"Repository not found" when cloning**
→ Check your internet connection. The repo is public — no login needed.

---

## Stopping and restarting

**To stop:** Press `Ctrl + C` in the terminal where it's running.

**To restart:**
```
cd ~/my-second-brain && bash setup.sh
```

**To update** (if Rob pushes changes):
```
cd ~/my-second-brain && git pull && bash setup.sh
```

---

Questions? Message Rob Goldsmith on GChat.
