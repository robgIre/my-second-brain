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
- Git is pre-installed on ODs.

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

## Step 3: Install plugins (calendar, tasks, GChat)

Still in the same terminal window — without plugins, your brain can't access your calendar, tasks, or other internal tools. Paste these commands:

```
claude plugin install meta@Meta
claude plugin install llm-rules@Meta
claude plugin install meta_knowledge@Meta
claude plugin install meta_codesearch@Meta
```

You only need to do this once per OD. If you release your OD and get a new one, you'll need to install plugins again.

---

## Step 4: Install and start My Second Brain

Still in the same terminal window. **On a Meta OD:** Set the proxy first so your OD can reach GitHub:
```
export https_proxy=http://fwdproxy:8080
export http_proxy=http://fwdproxy:8080
```

Then paste this to download and start the app:

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

**Don't close this terminal window** — it's running the server. If you close it, the app stops.

---

## Step 5: Open the app

You're done with the terminal! Open your web browser (Chrome, Safari, Firefox — any will work):

1. Go to: **http://localhost:5151**
2. Click the green **"Connect Brain"** button
3. You should see "Your brain is active" — you're all set!

**Page won't load?** See the OD Setup Guide for the port forwarding fix.

---

## Step 6: Set up your profile

1. Click **"About Me"** in the sidebar
2. Fill in your name, role, team, manager, location
3. Write a short background about what you do
4. Click **"Save & Sync"**

This teaches your brain who you are. Every time you use it, it already knows your context. From now on, everything happens in your browser.

---

## What to try

- **Morning Routine** — click "Run Now" on the home page. Your brain will check your emails, calendar, and tasks.
- **Ask My Brain** — type anything: "Prepare me for my 2pm meeting", "Summarize my open tasks", "What's happening on the GAZ 3 project?"
- **Add steps** — click "+ Add to my morning" or "+ Add to my evening" to customise your routines.

---

## Troubleshooting

**"git: command not found"**
→ Git isn't installed. See Step 1 above.

**"claude: command not found"**
→ In the terminal tab where you're connected to your OD, run: `curl -fsSL https://cli.anthropic.com/install.sh | sh`, then type `source ~/.bashrc` and try `claude --version` again.

**"Connect Brain" fails**
→ Open a new terminal tab (**Cmd+T** on Mac), connect to your OD (`ssh yourusername@YOUR-OD-NUMBER.od.fbinfra.net`), and run `claude --version` to check if Claude Code is installed.

**"Port already in use"**
→ Check your other terminal tabs for a server already running — press **Ctrl+C** in that tab to stop it. If you can't find it, start on a different port in the terminal tab connected to your OD: `cd ~/my-second-brain && MSB_PORT=5152 bash setup.sh`, then open `http://localhost:5152` in your browser (note: **5152** not 5151).

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
