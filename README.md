# Fantasy Football Injury Tracker

A comprehensive tool to monitor NFL player injuries for your Yahoo Fantasy Football league with **news-based intelligence**.

## ✨ Key Features

### 📊 Comprehensive Injury Monitoring
- Real-time alerts when players get injured or status worsens
- Tracks all owned players + top free agents
- Dual reporting modes: **Alert Mode** (urgent new injuries) vs **Comprehensive Mode** (all injuries)
- Configurable alert window (default: 24 hours)

### 📰 News Intelligence & Projected Returns
- Analyzes RSS feeds from Yahoo Sports and Rotoworld
- Sentiment analysis with color-coded indicators (🔴 Severe, 🟡 Moderate, ⚪ Neutral, 🟢 Positive)
- **Extracts return timelines from news** (e.g., "out 4-6 weeks", "season-ending", "day-to-day")
- **Shows latest news headline** for every injured player
- **Projected return dates** when timeline information is available from news
- Detects: season-ending injuries, surgery timelines, specific week ranges, return imminent

### 🏈 Depth Chart Integration
- Identifies direct backup players using official ESPN/NFL depth charts
- Shows if backup is available as free agent or already owned
- **Warns if backup is also injured** to prevent bad pickups

### ⚠️ Rule-Based Risk Assessment
- Evaluates likelihood of re-injury based on historical injury patterns
- **Uses injury database** to track player's full injury history over time
- Tracks injury frequency (how often player gets injured)
- Detects recurring injuries (same body part injured multiple times)
- Considers injury severity and type (Achilles, ACL, hamstring, etc.)
- No machine learning - uses simple, transparent heuristic rules

### 📈 Enhanced Reporting
- Clean tree-structured console output
- Detailed markdown reports (`injury_news.md`)
- Shows injury status, news sentiment, risk scores, and backup player info
- Clear legends explaining all metrics

## 🚀 Quick Start (This Repo is Pre-Configured)

This repository is already configured for a specific Yahoo Fantasy Football league. The `.env` file contains working credentials.

### Just Run It:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run once
python monitor.py --once
```

The first time you run it, you'll need to authenticate with Yahoo OAuth (browser will open automatically).

## 📦 Installation for Your Own League

Want to use this tracker for your own fantasy league? Follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/fbawaney/FantasyFootball-Injury-Tracker.git
cd FantasyFootball-Injury-Tracker
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Yahoo API Credentials

#### Create a Yahoo Developer App

1. Go to [Yahoo Developer Network](https://developer.yahoo.com/apps/)
2. Click "Create an App"
3. Fill in:
   - **Application Name**: Fantasy Injury Tracker
   - **Application Type**: Web Application
   - **Callback Domain**: `localhost`
   - **Redirect URI(s)**: `https://localhost:8000`
   - **API Permissions**: Fantasy Sports - Read ✅

4. Save your **Client ID** and **Client Secret**

#### Find Your League ID

1. Log into Yahoo Fantasy Football
2. Go to your league page
3. Look at the URL:
   ```
   https://football.fantasysports.yahoo.com/f1/12345/...
                                                ^^^^^
   ```
   The number `12345` is your league ID

### 4. Configure Your Environment

Copy the example file and edit it:

```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

Fill in your credentials:

```bash
YAHOO_CLIENT_ID=your_client_id_here
YAHOO_CLIENT_SECRET=your_client_secret_here
YAHOO_LEAGUE_ID=your_league_id_here
YAHOO_GAME_KEY=nfl

NOTIFICATION_METHOD=console
CHECK_INTERVAL=30
ALERT_WINDOW_HOURS=24
```

### 5. First Run - OAuth Authentication

```bash
python monitor.py --once
```

1. A browser window will open
2. Log into Yahoo and authorize the app
3. Copy the verification code
4. Paste it into the terminal
5. Your token is saved for future use

## 📖 Usage

### Continuous Monitoring (Recommended)

```bash
python monitor.py
```

- Checks immediately on startup
- Re-checks every 30 minutes (configurable)
- Runs until you stop it (Ctrl+C)

### Single Check

```bash
python monitor.py --once
```

- Runs one check and exits
- Perfect for cron jobs/schedulers

### View Saved Report

```bash
python monitor.py --report
```

- Shows the last saved injury report
- No API calls made

### Test Notifications

```bash
python monitor.py --test
```

## 📊 What You Get

### Console Output Example:

```
================================================================================
📊 INJURY SUMMARY REPORT WITH NEWS SENTIMENT
================================================================================
Generated: 2025-10-18 18:39:28
Total Injuries: 41
  - Owned Players: 31
  - Free Agents: 10

--------------------------------------------------------------------------------
⚠️  OWNED PLAYERS WITH INJURIES
--------------------------------------------------------------------------------

Team Alpha:

  • Christian McCaffrey (RB, SF)
    ├─ Status: IR
    ├─ Injury: Achilles
    ├─ 🔴 News Sentiment: Severe (-0.85)
    ├─ 📰 Latest: 49ers RB ruled out for remainder of season with Achilles injury
    │
    ├─ 📅 PROJECTED RETURN:
    │    Season-ending injury detected in news
    │    Estimated: 12 weeks (~84 days)
    │
    ├─ ⚠️  RE-INJURY RISK: 🟠 High (68.5/100)
    │    Multiple injuries this season (3x); Serious injury status (IR)
    │
    └─ 👉 Backup: Jordan Mason - ✅ AVAILABLE
```

### Markdown Report (`injury_news.md`):

- Detailed tables of all injured players
- Sortable by severity, status, team
- **Latest news headline** (clickable link) for every player
- **Projected return timelines** when available from news analysis
- Rule-based re-injury risk scores
- Backup player information
- Full news article details with sentiment analysis

## ⚠️ Risk Score Explained

The **Re-Injury Risk** score (0-100) predicts likelihood of future injury problems using rule-based heuristics and **historical injury data from the database**:

### Factors Considered:
- **Injury Frequency (30%)**: Number of injuries in player's history (tracked across multiple runs)
  - 1 injury = 15 points
  - 2 injuries = 35 points
  - 3 injuries = 60 points
  - 4+ injuries = 85+ points

- **Recurrence (25%)**: Same body part injured multiple times (checks full injury history)
  - 2x same injury = +30 points
  - 3x same injury = +60 points
  - 4+ same injury = +90 points
  - Extra +20 if current injury is recurring

- **Current Severity (20%)**: How serious the current injury is
  - Questionable = 20 points
  - Out = 60 points
  - IR/PUP = 90-100 points

- **Injury Type (10%)**: Known problematic injuries get extra penalty
  - High-risk: Achilles, ACL, back, concussion (+20 points)
  - Moderate-risk: Hamstring, groin, ankle (+10 points)

- **Currently Injured (15%)**: Currently injured players get recency penalty (90 points)

### Risk Levels:
- 🔴 **Critical (75-100)**: Very high risk - multiple recurring injuries
- 🟠 **High (60-74)**: Significant concern - multiple risk factors
- 🟡 **Moderate (40-59)**: Some concern - notable injury history
- 🟢 **Low (0-39)**: Minimal concern - first or infrequent injuries

**Use it to**: Decide whether to trade injured players, pick up handcuffs, or avoid injury-prone pickups.

## 📁 Project Structure

```
fantasyfootball/
├── Core Application
│   ├── monitor.py                # Main monitoring script
│   ├── yahoo_client.py           # Yahoo Fantasy API client
│   └── injury_tracker.py         # Core injury tracking logic
│
├── Database & Analysis
│   ├── injury_database.py        # SQLite database management
│   ├── news_analyzer.py          # News analysis & timeline extraction
│   ├── risk_scorer.py            # Rule-based injury risk assessment
│   ├── depth_chart.py            # ESPN depth chart integration
│   └── historical_data_loader.py # Database initialization tool
│
├── Utilities
│   ├── notifier.py               # Email/notification system
│   ├── check_database.py         # Database status checker
│   ├── manage_duplicates.py      # Duplicate checker/cleaner
│   └── test_system.py            # System integration tests
│
├── Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Your configuration (pre-filled)
│   └── .env.example              # Template for others
│
└── Generated Files
    ├── injury_data.json          # Cached injury data (auto-generated)
    ├── injury_news.md            # Detailed report (auto-generated)
    ├── injury_history.db         # SQLite database (auto-generated)
    └── token.json                # Yahoo OAuth token (auto-generated)
```

## 🗂️ Data Sources

| Source | Purpose | Official? |
|--------|---------|-----------|
| **Yahoo Fantasy API** | League rosters, player ownership | ✅ Official |
| **Sleeper API** | Injury statuses, designations | ✅ Official |
| **ESPN API** | NFL depth charts | ✅ Official |
| **Yahoo Sports RSS** | News headlines | ✅ Official |
| **Rotoworld RSS** | Injury news | ✅ Official |

## ⚙️ Configuration Options

Edit `.env` to customize:

```bash
# Alert window - only alert on injuries within this timeframe
ALERT_WINDOW_HOURS=24           # Default: 24 hours

# Check interval for continuous monitoring
CHECK_INTERVAL=30               # Default: 30 minutes

# Notification method
NOTIFICATION_METHOD=console     # Options: console, desktop, email
```

## 📅 Scheduling Options

### Keep Running in Terminal

```bash
python monitor.py
```

### Run in Background (Linux/Mac)

```bash
nohup python monitor.py > injury_monitor.log 2>&1 &
```

### Cron Job (Linux/Mac) - Every 30 Minutes

```bash
crontab -e
```

Add:
```bash
*/30 * * * * cd /path/to/fantasyfootball && python monitor.py --once
```

### Windows Task Scheduler

Create a task to run `python monitor.py --once` every 30 minutes.

## 🛠️ Utility Scripts

### Check Database Status
```bash
python check_database.py
```
Shows database statistics, top injured players, and recurring injuries.

### Manage Duplicates
```bash
# Check for duplicate injury records
python manage_duplicates.py --check

# Clean duplicate records (keeps most recent)
python manage_duplicates.py --clean
```

### Initialize/Sync Database
```bash
# Sync current injuries from Sleeper API
python historical_data_loader.py --sync

# Full database initialization
python historical_data_loader.py --init
```

## 🐛 Troubleshooting

### OAuth Issues

```bash
# Delete token and re-authenticate
rm token.json
python monitor.py --once
```

### No Injuries Detected

- Verify `.env` has correct league ID
- Check Yahoo OAuth is working
- Test Sleeper API: `curl https://api.sleeper.app/v1/players/nfl`

### Desktop Notifications Not Working

- **macOS**: Should work by default
- **Linux**: `sudo apt-get install libnotify-bin`
- **Windows**: Check PowerShell execution policy

### Database Issues

```bash
# Check database status and integrity
python check_database.py

# Check for duplicate records
python manage_duplicates.py --check

# Clean duplicates if found
python manage_duplicates.py --clean
```

## 🔒 Privacy & Security

- Yahoo credentials stored locally in `.env`
- OAuth tokens cached in `token.json`
- No external services except official APIs
- All data processing happens locally
- **Note**: This repo's `.env` is public (read-only API, league data is public anyway)

## 🤝 Contributing

Ideas for enhancements:
- Add practice report tracking (DNP/Limited/Full)
- Enhance email notifications
- Create web dashboard
- Mobile app notifications
- Improve return timeline predictions with more data sources

## 📄 License

This is a personal project. Feel free to use it for your fantasy leagues!

## ⚠️ Disclaimer

Not affiliated with Yahoo, NFL, ESPN, or Sleeper. Injury information should be verified with official team sources before making fantasy decisions.

---

**Good luck with your fantasy season!** 🏈
