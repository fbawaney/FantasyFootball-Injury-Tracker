# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

Or use the setup script:
```bash
./setup.sh
```

## Step 2: Get Yahoo API Credentials (2 min)

1. Go to https://developer.yahoo.com/apps/
2. Click "Create an App"
3. Fill in:
   - Name: Fantasy Injury Tracker
   - Type: Web Application
   - Redirect URI: `https://localhost:8000`
   - API: Fantasy Sports - Read
4. Copy your **Client ID** and **Client Secret**

## Step 3: Get Your League ID (30 sec)

1. Go to your Yahoo Fantasy Football league
2. Look at the URL:
   ```
   https://football.fantasysports.yahoo.com/f1/12345/...
                                              ^^^^^
                                           This is your League ID
   ```

## Step 4: Configure (1 min)

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Fill in:
```bash
YAHOO_CLIENT_ID=your_client_id
YAHOO_CLIENT_SECRET=your_client_secret
YAHOO_LEAGUE_ID=your_league_id
```

## Step 5: Run! (30 sec)

First time (authenticate):
```bash
python monitor.py --once
```

A browser will open. Log into Yahoo, authorize the app, and paste the code.

Start monitoring:
```bash
python monitor.py
```

That's it! You'll now get alerts when players get injured.

## Quick Commands

```bash
# Continuous monitoring
python monitor.py

# Single check
python monitor.py --once

# View current injuries
python monitor.py --report

# Test notifications
python monitor.py --test
```

## What You'll See

When a player gets injured:

```
🚨 INJURY ALERT 🚨
New/Updated Injuries: 1

🆕 NEW INJURY
   Player: Christian McCaffrey
   Position: RB | Team: SF
   Status: Out
   Injury: Achilles
   🏈 OWNED BY: Your Team Name (Manager: Your Name)
```

## Troubleshooting

**Authentication failed?**
- Check your Client ID and Secret
- Make sure redirect URI is `https://localhost:8000`

**No players found?**
- Verify your League ID is correct
- Make sure it's the current season

**No injuries detected?**
- The Sleeper API might be down (rare)
- Try `python injury_tracker.py` to test directly

## Desktop Notifications

Want desktop popups instead of console? Edit `.env`:

```bash
NOTIFICATION_METHOD=desktop
```

## Run in Background

**Mac/Linux:**
```bash
nohup python monitor.py > injury_monitor.log 2>&1 &
```

**View logs:**
```bash
tail -f injury_monitor.log
```

**Stop:**
```bash
pkill -f monitor.py
```

---

Need more help? See the full [README.md](README.md)
