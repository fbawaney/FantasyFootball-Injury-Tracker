# Fantasy Football Injury Tracker with ML Predictions

A comprehensive tool to monitor NFL player injuries for your Yahoo Fantasy Football league with **ML-powered return timeline predictions** and **news-based intelligence**.

## ✨ Key Features

### 🤖 ML-Powered Predictions
- **Return Timeline Predictions**: Random Forest model predicts when injured players will return
- **News-Based Overrides**: Automatically detects season-ending injuries, surgeries, and return timelines from NFL news
- **Injury Risk Scoring**: 0-100 risk score predicting future injury problems based on historical patterns
- **NFL Rule Enforcement**: Respects IR/PUP minimums (4 weeks), injury designations

### 📊 Comprehensive Injury Monitoring
- Real-time alerts when players get injured or status worsens
- Tracks all owned players + top free agents
- Dual reporting modes: **Alert Mode** (urgent new injuries) vs **Comprehensive Mode** (all injuries)
- Configurable alert window (default: 24 hours)

### 📰 News Intelligence
- Analyzes RSS feeds from Yahoo Sports and Rotoworld
- Sentiment analysis with color-coded indicators (🔴 Severe, 🟡 Moderate, ⚪ Neutral, 🟢 Positive)
- Extracts specific timelines from headlines ("out 4-6 weeks", "season-ending", "activated")
- Overrides unrealistic ML predictions with confirmed news

### 🏈 Depth Chart Integration
- Identifies direct backup players using official ESPN/NFL depth charts
- Shows if backup is available as free agent or already owned
- **Warns if backup is also injured** to prevent bad pickups

### 📈 Enhanced Reporting
- Clean tree-structured console output
- Detailed markdown reports (`injury_news.md`)
- Shows ML prediction + news override + risk score for each player
- Clear legends explaining all metrics

## 🚀 Quick Start (This Repo is Pre-Configured)

This repository is already configured for a specific Yahoo Fantasy Football league. The `.env` file contains working credentials.

### Just Run It:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup ML model (one-time)
python setup_ml.py

# 3. Run once
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

### 5. Setup ML Model

```bash
python setup_ml.py
```

This creates the ML model and injury database (one-time setup).

### 6. First Run - OAuth Authentication

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
    │
    ├─ 📰 NEWS-ADJUSTED TIMELINE:
    │    Expected return: NFL Week 18 (11 weeks, ~77 days)
    │    ML model said: Week 14 (35 days)
    │    Override: Season-ending: "49ers RB ruled out for remainder of season"
    │
    ├─ ⚠️  FUTURE INJURY RISK: 🟠 High (72.5/100)
    │    Injury-prone: 4 injuries in last 6 months
    │    Recurring Hamstring injury (3x)
    │    Chronic areas: Hamstring, Achilles
    │
    └─ 👉 Backup: Jordan Mason - ✅ AVAILABLE
```

### Markdown Report (`injury_news.md`):

- Detailed tables of all injured players
- Sortable by severity, status, team
- News headlines with links
- ML predictions and risk assessments
- Backup player information

## 🧠 How ML Predictions Work

### Random Forest Model
- Trained on historical NFL injury data
- Features: injury type, position, player history, severity
- Predicts recovery timeline in days
- Provides confidence intervals (min-max range)

### NFL Rule Enforcement
- **IR/PUP**: Minimum 4 weeks (28 days)
- **Out**: Minimum 1 week (7 days)
- **Questionable/Doubtful**: No minimum

### News-Based Overrides
When news is more specific than the ML model, it takes precedence:

| News Detected | Override Action |
|---------------|----------------|
| "season-ending" | Set to rest of season |
| "surgery scheduled" | Set to 6+ weeks |
| "activated from IR" | Set to 0-7 days |
| "out 4-6 weeks" | Use extracted timeline |
| "week-to-week" | Set to 1-3 weeks |
| "day-to-day" | Set to 1-7 days |

## ⚠️ Risk Score Explained

The **Future Injury Risk** score (0-100) predicts likelihood of future injury problems:

### Factors (Weighted):
- **Frequency (30%)**: How often they get injured
- **Recurrence (25%)**: Same body part injured multiple times
- **Severity (20%)**: Current injury status (IR/PUP/Out)
- **Recency (15%)**: Recent vs. old injury patterns
- **Recovery (10%)**: Slow vs. fast healing history

### Risk Levels:
- 🔴 **Critical (75-100)**: Very high risk - frequent injuries, slow recovery
- 🟠 **High (60-74)**: Significant concern - multiple risk factors
- 🟡 **Moderate (40-59)**: Some concern - notable history
- 🟢 **Low (0-39)**: Minimal concern - clean history

**Use it to**: Decide whether to handcuff players, make trades, or avoid injury-prone pickups.

## 📁 Project Structure

```
fantasyfootball/
├── monitor.py                    # Main monitoring script
├── yahoo_client.py               # Yahoo Fantasy API client
├── injury_tracker.py             # Core injury tracking + ML integration
├── notifier.py                   # Alert system with formatting
├── depth_chart.py                # ESPN depth chart integration
├── news_analyzer.py              # News timeline extraction ✨ NEW
├── ml_predictor.py               # ML model for predictions ✨ NEW
├── risk_scorer.py                # Injury risk assessment ✨ NEW
├── injury_database.py            # Historical injury tracking ✨ NEW
├── historical_data_loader.py     # Load injury history ✨ NEW
├── setup_ml.py                   # One-time ML setup
├── test_ml_validation.py         # ML validation tests
├── requirements.txt              # Python dependencies
├── .env                          # Your configuration (pre-filled)
├── .env.example                  # Template for others
├── models/                       # Trained ML model ✨ NEW
│   └── injury_predictor.pkl
├── injury_data.json              # Cached data (auto-generated)
├── injury_news.md                # Detailed report (auto-generated)
└── token.json                    # OAuth token (auto-generated)
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

## 🐛 Troubleshooting

### OAuth Issues

```bash
# Delete token and re-authenticate
rm token.json
python monitor.py --once
```

### ML Model Issues

```bash
# Rebuild ML model
python setup_ml.py
```

### No Injuries Detected

- Verify `.env` has correct league ID
- Check Yahoo OAuth is working
- Test Sleeper API: `curl https://api.sleeper.app/v1/players/nfl`

### Desktop Notifications Not Working

- **macOS**: Should work by default
- **Linux**: `sudo apt-get install libnotify-bin`
- **Windows**: Check PowerShell execution policy

## 📚 Documentation

- **ML_FEATURES.md** - Complete ML capabilities guide
- **NEWS_INTEGRATION_ANALYSIS.md** - How news integration works
- **ML_PREDICTION_FIXES.md** - Technical bug fixes
- **REPORTING_MODES.md** - Alert vs Comprehensive modes
- **DEPTH_CHART_SOURCE.md** - ESPN API documentation

## 🔒 Privacy & Security

- Yahoo credentials stored locally in `.env`
- OAuth tokens cached in `token.json`
- No external services except official APIs
- All data processing happens locally
- **Note**: This repo's `.env` is public (read-only API, league data is public anyway)

## 🤝 Contributing

Ideas for enhancements:
- Import real historical NFL injury data
- Add practice report tracking (DNP/Limited/Full)
- Implement email notifications
- Create web dashboard
- Mobile app notifications

## 📄 License

This is a personal project. Feel free to use it for your fantasy leagues!

## ⚠️ Disclaimer

Not affiliated with Yahoo, NFL, ESPN, or Sleeper. Injury information should be verified with official team sources before making fantasy decisions.

---

**Good luck with your fantasy season!** 🏈🤖
