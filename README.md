# Fantasy Football Injury Tracker

A comprehensive tool to monitor NFL player injuries for your Yahoo Fantasy Football league. Get real-time alerts when owned players or top free agents are injured.

## Features

- **Yahoo Fantasy Integration**: Automatically tracks all players in your league (owned + top free agents)
- **Multiple Data Sources**: Fetches injury data from Sleeper API (most comprehensive free source)
- **Real-time Alerts**: Get notified immediately when:
  - A player gets newly injured
  - An injury status worsens (e.g., Questionable → Out)
- **News Sentiment Analysis**:
  - Analyzes RSS news feeds from Yahoo Sports and Rotoworld
  - Color-coded severity indicators (🔴 Severe, 🟡 Moderate, ⚪ Neutral, 🟢 Positive)
  - Sentiment scoring from -1 (very negative) to +1 (very positive)
- **NFL Depth Chart Integration**:
  - Identifies direct backup players for injured starters
  - Shows backup availability (owned vs. free agent)
  - **Warns if backup is also injured** to prevent bad pickups
- **Smart Matching**: Automatically matches Yahoo players with injury data sources
- **Multiple Notification Methods**:
  - Console alerts (default)
  - Desktop notifications (macOS, Linux, Windows)
  - Email alerts (coming soon)
- **Continuous Monitoring**: Runs in background and checks for updates at configurable intervals
- **Detailed Reports**: View comprehensive injury reports for your entire league with sentiment analysis
- **Alert Window**: Only alerts on injuries first seen within 24 hours (configurable)

## Data Sources

### Primary: Sleeper API
- **Free** and requires no authentication
- Most comprehensive injury data
- Includes: injury status, body part, notes, and start date
- Updates frequently

### Future Enhancements
- ESPN API (unofficial, may be added)
- Twitter/X integration for beat reporter updates
- Additional APIs as they become available

## Installation

### 1. Clone or Download

```bash
cd /path/to/fantasyfootball
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `yfpy` - Yahoo Fantasy Sports API wrapper
- `requests` - HTTP requests
- `python-dotenv` - Environment variable management
- `schedule` - Task scheduling
- `feedparser` - RSS feed parsing for news
- `textblob` - Sentiment analysis

### 3. Set Up Yahoo API Credentials

#### Create Yahoo App

1. Go to [Yahoo Developer Network](https://developer.yahoo.com/apps/)
2. Click "Create an App"
3. Fill in the form:
   - **Application Name**: Fantasy Injury Tracker (or your choice)
   - **Application Type**: Web Application
   - **Callback Domain**: `localhost`
   - **Redirect URI(s)**: `https://localhost:8000`
   - **API Permissions**: Fantasy Sports - Read

4. Note your **Client ID** and **Client Secret**

#### Find Your League ID

1. Log into Yahoo Fantasy Football
2. Go to your league page
3. Look at the URL - it will look like:
   ```
   https://football.fantasysports.yahoo.com/f1/12345/...
   ```
   The number `12345` is your league ID

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```bash
# Yahoo Fantasy Sports API Credentials
YAHOO_CLIENT_ID=your_client_id_here
YAHOO_CLIENT_SECRET=your_client_secret_here

# Yahoo Fantasy League Settings
YAHOO_LEAGUE_ID=your_league_id_here
YAHOO_GAME_KEY=nfl

# Notification Settings
NOTIFICATION_METHOD=console  # Options: console, email, desktop
CHECK_INTERVAL=30  # Check every 30 minutes
```

### 5. First Time Setup - OAuth Authentication

The first time you run the tool, it will open a browser for OAuth authentication:

```bash
python monitor.py --once
```

1. A browser window will open
2. Log into Yahoo and authorize the app
3. Copy the verification code
4. Paste it into the terminal
5. The tool will save your token for future use

## Usage

### Run Continuous Monitoring (Recommended)

Monitor injuries continuously with periodic checks:

```bash
python monitor.py
```

This will:
- Check for injuries immediately on startup
- Continue checking every 30 minutes (or your configured interval)
- Send alerts when new injuries are detected
- Run until you stop it with Ctrl+C

### Run Single Check

Run a one-time injury check and exit:

```bash
python monitor.py --once
```

### View Current Injury Report

Show current injuries without checking for updates:

```bash
python monitor.py --report
```

### Test Notifications

Test your notification system:

```bash
python monitor.py --test
```

## Notification Methods

### Console (Default)

Displays alerts in your terminal with detailed formatting including sentiment analysis:

```
🚨 INJURY ALERT 🚨
Time: 2025-10-15 14:30:00
New/Updated Injuries: 2

🆕 NEW INJURY
   Player: Christian McCaffrey
   Position: RB | Team: SF
   Status: Out
   Injury: Achilles
   🏈 OWNED BY: Team Alpha (Manager: John Doe)

   🔴 NEWS SENTIMENT: Severe (Score: -0.65)

   💡 DIRECT BACKUP:
      Jordan Mason (RB, SF)
      ✅ AVAILABLE as Free Agent - ADD NOW!

   Source: Sleeper API
```

### Desktop Notifications

Set `NOTIFICATION_METHOD=desktop` in your `.env` file.

Shows native OS notifications:
- **macOS**: Uses `osascript`
- **Linux**: Uses `notify-send`
- **Windows**: Uses PowerShell toast notifications

### Email (Coming Soon)

Email notifications require SMTP configuration (Gmail, SendGrid, etc.)

## Project Structure

```
fantasyfootball/
├── monitor.py              # Main monitoring script
├── yahoo_client.py         # Yahoo Fantasy API client
├── injury_tracker.py       # Injury data fetching, matching, and sentiment analysis
├── notifier.py            # Notification system with sentiment display
├── depth_chart.py         # NFL depth chart integration
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (you create this)
├── .env.example          # Configuration template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── QUICKSTART.md         # Quick start guide
├── injury_data.json      # Cached injury data (auto-generated)
├── injury_news.md        # Detailed injury news report (auto-generated)
└── token.json            # OAuth tokens (auto-generated)
```

## How It Works

1. **Fetch Players**: Gets all players from your Yahoo league (owned + top free agents)
2. **Fetch News**: Pulls RSS feeds from Yahoo Sports and Rotoworld
3. **Get Injury Data**: Fetches latest injury info from Sleeper API
4. **Match Players**: Intelligently matches Yahoo players with injury data by name and team
5. **Analyze Sentiment**: Uses TextBlob to analyze news sentiment for each injured player
6. **Check Depth Charts**: Identifies backup players and checks if they're also injured
7. **Detect Changes**: Compares current injuries with previous check to find:
   - New injuries (within 24-hour alert window)
   - Worsened injury status
8. **Send Alerts**: Notifies you of changes with sentiment analysis and backup info
9. **Generate Reports**: Creates both console display and markdown file (injury_news.md)
10. **Save State**: Stores current injuries for next comparison

## Injury Status Levels

The tool tracks these injury designations:

- **IR** (Injured Reserve) - Out for extended period
- **Out** - Will not play
- **Doubtful** - Unlikely to play
- **Questionable** - Uncertain
- **PUP** (Physically Unable to Perform)
- **Suspended** - League suspension

## Scheduling Options

### Keep Running in Terminal

```bash
python monitor.py
```

### Run in Background (Linux/Mac)

```bash
nohup python monitor.py > injury_monitor.log 2>&1 &
```

### Use a Scheduler

**Linux/Mac (cron)**: Run every 30 minutes
```bash
*/30 * * * * cd /path/to/fantasyfootball && python monitor.py --once
```

**Windows (Task Scheduler)**: Create a task to run `monitor.py --once` every 30 minutes

### Run in Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "monitor.py"]
```

## Troubleshooting

### OAuth Issues

If you get authentication errors:
1. Delete `token.json`
2. Run `python monitor.py --once` to re-authenticate
3. Make sure your redirect URI in Yahoo app is `https://localhost:8000`

### No Injuries Detected

- Make sure your `.env` file is configured correctly
- Verify your league ID is correct
- Check that Sleeper API is accessible: `curl https://api.sleeper.app/v1/players/nfl`

### Rate Limiting

The tool includes rate limiting protections. If you get rate limited:
- Increase `CHECK_INTERVAL` in your `.env`
- The Sleeper API is generous and shouldn't rate limit normal usage

### Desktop Notifications Not Working

**macOS**: Should work by default
**Linux**: Install `notify-send`: `sudo apt-get install libnotify-bin`
**Windows**: Make sure PowerShell execution policy allows scripts

## Advanced Configuration

### Monitor Specific Positions

Edit `yahoo_client.py` line 122 to change free agent filters:

```python
# Only monitor RB and WR free agents
free_agents_rb = self.get_free_agents(position='RB', count=50)
free_agents_wr = self.get_free_agents(position='WR', count=50)
```

### Adjust Alert Sensitivity

Edit `injury_tracker.py` line 188 to change which statuses trigger alerts:

```python
# Only alert on severe injuries
if injury_status in ['Out', 'IR', 'PUP']:
    # ... alert logic
```

### Custom Notification Format

Edit `notifier.py` to customize alert messages and formatting.

## API Rate Limits

- **Yahoo Fantasy API**: Rate limits vary, tool handles them gracefully
- **Sleeper API**: Very generous limits, no API key required
- Default 30-minute check interval is well within all limits

## Privacy & Security

- Your Yahoo credentials are stored locally in `.env` (never committed to git)
- OAuth tokens are cached locally in `token.json`
- No data is sent to external services except Yahoo and Sleeper APIs
- Injury data is cached locally in `injury_data.json`

## Sentiment Analysis

The tool analyzes news headlines using TextBlob to provide actionable sentiment scores:

- **Severe** (🔴): Score < -0.5 - Very negative news, major concern
- **Moderate** (🟡): Score -0.5 to -0.2 - Somewhat negative, monitor closely
- **Neutral** (⚪): Score -0.2 to 0.2 - Mixed or neutral reporting
- **Positive** (🟢): Score > 0.2 - Encouraging news

This helps prioritize which injuries require immediate action vs. routine monitoring.

## Contributing

Feel free to enhance this tool! Some ideas:
- Add more injury data sources
- Implement email notifications
- Add web dashboard
- Create mobile app notifications
- Improve sentiment analysis algorithms
- Implement ML predictions for return timelines
- Add historical injury tracking

## License

This is a personal tool. Use it freely for your fantasy football leagues!

## Disclaimer

This tool uses publicly available APIs and data. It is not affiliated with Yahoo, NFL, or any other sports organization. Injury information should be verified with official team sources before making fantasy decisions.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Verify your `.env` configuration
3. Test individual components:
   - `python yahoo_client.py` - Test Yahoo connection
   - `python injury_tracker.py` - Test injury data fetching
   - `python notifier.py` - Test notifications

---

**Good luck with your fantasy season!** 🏈
