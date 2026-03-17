# My Second Brain — OD Setup Guide

Hey! This is a **one-time setup** to get My Second Brain running on a Meta On-Demand server (OD). Same steps whether you're on Mac or Windows. Once done, you just reconnect and go.

---

## Why an OD?

My Second Brain is a wrapper around Claude Code CLI, which only runs on ODs — not on your regular Windows or Mac laptop. If you tried running it locally and got errors about pip, Flask, or "module not found", this is why. This setup is a **one-time thing**. After you've done it once, you just reconnect to your OD and start the server — takes 30 seconds.

---

## Step 1: Check the On Demand dashboard

Go to your browser's address bar (where you'd normally type google.com), type **od**, and hit Enter. This opens the On Demand dashboard.

Look at the top of the page under **"Current Instances"**:
- If it says **"You do not currently have any instances"** — that's fine, move to Step 2
- If you see an existing instance listed, click **"Save & Release"** next to it first, then move to Step 2

---

## Step 2: Open a terminal on your laptop

**On a Mac:** Press **Cmd + Space** to open Spotlight, type **Terminal**, and hit Enter.

**On Windows:** Press **Win + R**, type **cmd**, and hit Enter.

You should see a black or white window with a blinking cursor — that's your terminal.

---

## Step 3: Connect to your OD server

In the terminal, type these two commands (or copy and paste them):

```
cd
dev connect
```

A list of options will appear. Use your arrow keys to find and select:
**"WWW+FBSource+Configerator (Hardware: Default) (VPNLess)"**
Then hit Enter.

It will ask you to touch your **YubiKey** (the small USB security key on your laptop). Tap it.

Wait a moment. You're connected when you see something like:
```
[yourusername@12345.od ~]
```

This means you're now on a remote server, not your laptop. Everything you type from here runs on the OD.

---

## Step 4: Check Python and Claude Code are installed

Once connected to your OD, run these checks:

```
python3 --version
claude --version
```

If **Python 3** shows a version number (e.g. `Python 3.10.12`) — you're good.

If not, install it:
```
sudo apt-get update && sudo apt-get install -y python3 python3-pip
```

If **Claude Code** shows a version number — you're good.

If not, install it:
```
curl -fsSL https://cli.anthropic.com/install.sh | sh
```
Then close and reopen your terminal.

---

## Step 5: Install and start Second Brain

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

## Step 6: Open the dashboard

1. Open your browser and go to: **http://localhost:5151**
2. Click the green **"Connect Brain"** button
3. You should see "Your brain is active"

**Keep the terminal window open** — if you close it, the server stops.

---

## Step 7: Set up your profile

1. Click **"About Me"** in the sidebar
2. Fill in your name, role, team, manager, location
3. Write a short background about what you do
4. Click **"Save & Sync"**

This teaches your brain who you are so it has context every time you use it.

---

## What to try first

- **Morning Routine** — click "Run Now" on the home page
- **Ask My Brain** — type anything in plain language, e.g. "What's on my calendar today?"
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
- Start on a different port: `MSB_PORT=5152 bash setup.sh`

**Page won't load**
- Make sure the terminal with the server is still running
- Check you're using the right URL: http://localhost:5151

---

Questions? Message Rob Goldsmith on GChat.
