# My Second Brain — Comms Drafts

Use whichever format suits. Edit as needed before sending.

---

## GChat Message (short, for your team)

Hey team — I've been building something I'd love your help testing.

**My Second Brain** is a web dashboard for Claude Code. Instead of typing in a terminal, you open a web page, click "Connect Brain", and tell it what to do in plain language. It can run your morning brief, prep meetings, prioritize tasks, do research — anything you'd normally ask Claude Code to do, but without touching the terminal.

**Setup takes 60 seconds:**
1. Open your OD terminal
2. Paste this:
```
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```
3. Open http://localhost:5151 in your browser
4. Click "Connect Brain"

There's a "Get Started" page inside the app with full instructions and troubleshooting.

I'm looking for honest feedback — what works, what doesn't, what's confusing, what's missing. Try the morning routine, type something into "Build Now", fill in your About Me. Break it if you can.

Landing page: https://robgIre.github.io/my-second-brain

Ping me if you get stuck.

---

## Workplace Post (longer, for broader audience)

**Title:** My Second Brain — A web dashboard for Claude Code (looking for testers)

I've been working on removing the biggest barrier to adopting Claude Code as a personal productivity tool: the terminal.

Most people in DEC aren't engineers. Asking them to open a terminal, type commands, and manage config files is a non-starter — no matter how powerful the tool is underneath. So I built **My Second Brain**: a web dashboard that wraps Claude Code in a clean UI.

**What it does:**
- **Connect Brain** — one click to connect to Claude Code on your OD. No terminal after initial setup.
- **Build Now** — type any task in plain language ("prep me for my 2pm meeting", "summarize my open tasks"). Your brain executes it and shows results.
- **Morning Routine / EOD Debrief** — predefined routines you can run with one click. Customise by adding your own steps in plain language.
- **About Me** — fill in your details once. It syncs to CLAUDE.md so your brain always knows who you are.
- **Talk to Me** — voice input mode (demo for now, full implementation coming).

**The pitch:** You open a web page. You click a button. You tell it what to do. It does it. No terminal, no commands, no code.

**Looking for 5-6 testers** from the P&D team. Setup takes 60 seconds — one command in your OD terminal, then it's all browser-based. There's a built-in "Get Started" guide.

**Setup:**
```
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```
Then open http://localhost:5151

Landing page: https://robgIre.github.io/my-second-brain

Comment below or DM me if you want to try it. I want honest feedback on what works, what's confusing, and what you'd want it to do.

There's an easter egg in the app if you hover over the flask icon — it's a nod to Steve Martin's "The Man With Two Brains" (1983).
