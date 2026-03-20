# My Second Brain — OD Setup Guide

The full setup guide with step-by-step instructions is on the landing page:

**https://robgire.github.io/my-second-brain/od-setup.html**

It covers:
1. Checking the On Demand dashboard
2. Opening a terminal
3. Connecting to your OD (`dev connect`)
4. Checking Python and Claude Code are installed
5. Authenticating internal tools (`jf authenticate`)
6. Installing plugins (calendar, tasks, GChat, Workplace)
7. Installing and starting My Second Brain
8. Opening the dashboard (`localhost:5151`)
9. Setting up your profile

## Quick Reference

**First time (one command):**
```bash
export https_proxy=http://fwdproxy:8080
export http_proxy=http://fwdproxy:8080
git clone https://github.com/robgIre/my-second-brain.git && cd my-second-brain && bash setup.sh
```

**Install plugins (run on your OD before starting the server):**
```bash
claude plugin install meta@Meta
claude plugin install llm-rules@Meta
claude plugin install meta_knowledge@Meta
claude plugin install meta_codesearch@Meta
```

**Restart:**
```bash
cd ~/my-second-brain && bash setup.sh
```

**Update:**
```bash
export https_proxy=http://fwdproxy:8080
cd ~/my-second-brain && git pull && bash setup.sh
```

**Page won't load?**
Close your terminal and reconnect with port forwarding:
```bash
ssh -L 5151:localhost:5151 yourusername@YOUR-OD-NUMBER.od.fbinfra.net
```

---

Questions? Message Rob Goldsmith on GChat.
