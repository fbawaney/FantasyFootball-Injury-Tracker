# Dual Reporting Modes: Alerts vs. Comprehensive Reports

## Overview

The injury tracker now operates with **two distinct modes** to give you the best of both worlds:

1. **Alert Mode** - Urgent notifications for new/worsened injuries
2. **Comprehensive Report Mode** - Full injury landscape with ML predictions

---

## 🚨 Alert Mode (NEW/WORSENED INJURIES)

**Purpose**: Catch breaking injury news that requires immediate action

**What it shows:**
- Only injuries that are NEW or WORSENED within the alert window
- Default: Last 24 hours (configurable)
- Urgent notification format

**When to use:**
- Continuous monitoring (`python monitor.py`)
- Quick checks when you need to know what changed
- Before making waiver wire decisions

**Example Output:**
```
🚨 INJURY ALERT 🚨
Time: 2025-10-18 14:30:00
New/Updated Injuries: 2
(Recent injuries requiring immediate attention)

🆕 NEW INJURY
   Player: Christian McCaffrey
   Position: RB | Team: SF
   Status: Out
   ...
```

**Configuration:**
```bash
# In .env file
ALERT_WINDOW_HOURS=24   # Default: 24 hours
ALERT_WINDOW_HOURS=168  # 1 week - see all new injuries this week
ALERT_WINDOW_HOURS=999999  # Effectively infinite - alert on everything
```

---

## 📊 Comprehensive Report Mode (ALL INJURIES)

**Purpose**: Complete injury landscape analysis with ML predictions

**What it shows:**
- **ALL currently injured players** in your league
- Full ML predictions (return timeline, confidence intervals)
- Injury risk scores for every player
- Backup player analysis
- News sentiment analysis
- Complete injury history

**When to use:**
- Weekly injury report review
- League sharing (your whole league sees all injuries)
- Strategic planning (who to target, who to trade)
- Injury risk assessment before trades

**Example Output:**
```
📊 COMPREHENSIVE INJURY REPORT 📊
Time: 2025-10-18 14:30:00
Total Injured Players: 41
(All current injuries with ML predictions)

⚠️  OWNED PLAYERS WITH INJURIES

Team Alpha:
  • Christian McCaffrey (RB, SF)
    Status: Out
    Injury: Achilles
    ⚪ News Sentiment: Neutral (0.00)
    🤖 ML Prediction: Week 12 (42 days)
    🔴 Injury Risk: High (72/100)
    👉 Backup: Jordan Mason - ✅ AVAILABLE
```

---

## How They Work Together

### Workflow Example:

**Monday Morning (Continuous Monitor Running):**
```bash
python monitor.py  # Running continuously
```
- **Alert Mode**: "🚨 2 new injuries! McCaffrey (Out), Jefferson (Questionable)"
- **Comprehensive Report**: Shows all 41 injured players with predictions
- **Action**: You see the alert, check the full report, add Jordan Mason

**Wednesday (Quick Check):**
```bash
python monitor.py --once
```
- **Alert Mode**: "✓ No new injuries" (nothing in last 24h)
- **Comprehensive Report**: Still shows all 41 injuries + updated predictions
- **Action**: Review everyone's status, make informed decisions

**Sunday Morning (Pre-Gameday):**
```bash
python monitor.py --report
```
- **No Alerts**: Just shows comprehensive report
- **Comprehensive Report**: All injuries with latest status
- **Action**: Set your lineup based on complete injury picture

---

## Key Differences

| Feature | Alert Mode | Comprehensive Mode |
|---------|-----------|-------------------|
| **Scope** | New/worsened only | ALL injuries |
| **Time Window** | Last 24h (configurable) | Current injuries |
| **ML Predictions** | Yes | Yes (for everyone) |
| **Purpose** | Immediate action | Strategic analysis |
| **Frequency** | Real-time | Always available |
| **Output** | Urgent notifications | Full report |

---

## Where You See Each Mode

### Console Output:
- **Alert Mode**: Appears after "Step 4: Detecting new/worsened injuries"
- **Comprehensive Mode**: Appears in "Step 7: Comprehensive injury report"

### Files:
- **`injury_news.md`**: Always shows ALL injuries (comprehensive)
- **`injury_data.json`**: Stores all current injuries

### Summary Report:
- Shows ALL injuries
- ML predictions included if `show_all=True`
- Grouped by ownership (your team, league teams, free agents)

---

## Configuration Guide

### Default Setup (Recommended):
```bash
ALERT_WINDOW_HOURS=24  # Alert on last 24 hours
```
- **Alerts**: New injuries from last day
- **Reports**: All current injuries

### Aggressive Setup (Don't Miss Anything):
```bash
ALERT_WINDOW_HOURS=168  # Alert on last week
```
- **Alerts**: All new injuries from last 7 days
- **Reports**: All current injuries

### League-Wide Dashboard Setup:
```bash
ALERT_WINDOW_HOURS=999999  # Effectively infinite
```
- **Alerts**: Every single injury (use with caution)
- **Reports**: All current injuries
- Good for shared dashboards where you want to see everything

### Conservative Setup (Only Critical):
```bash
ALERT_WINDOW_HOURS=6  # Last 6 hours only
```
- **Alerts**: Very recent injuries only
- **Reports**: Still shows all injuries
- Good if you check multiple times per day

---

## Best Practices

### For Personal Use:
1. **Keep ALERT_WINDOW_HOURS=24** for daily monitoring
2. Check comprehensive report weekly for strategic planning
3. Use alerts for reactive decisions (waiver wire)
4. Use full report for proactive decisions (trades, lineup)

### For League Sharing:
1. **Set ALERT_WINDOW_HOURS=168** (1 week) so new members see recent context
2. Share `injury_news.md` with your league
3. Everyone sees ML predictions for all players
4. Establishes you as the analytics expert

### For Multiple Daily Checks:
1. **Set ALERT_WINDOW_HOURS=6-12** to avoid duplicate alerts
2. Quick checks show only new information
3. Full report always available for context

---

## Examples

### Example 1: Typical Monday After Sunday Games

```bash
$ python monitor.py --once

Step 4: Detecting new/worsened injuries for alerts...
  Alert window: 24 hours
  ⚠️  5 new or updated injuries for alerts!

🚨 INJURY ALERT 🚨
[Shows 5 new injuries from Sunday's games]

Step 7: Generating comprehensive injury report (ALL injuries)...

📊 COMPREHENSIVE INJURY REPORT 📊
Total Injured Players: 46
[Shows all 46 injuries including the 5 new ones + 41 existing]
```

**Result**: You get urgent alerts for the 5 new injuries, but also see the complete picture.

### Example 2: Wednesday Mid-Week Check

```bash
$ python monitor.py --once

Step 4: Detecting new/worsened injuries for alerts...
  ✓ No new injuries to alert on

Step 7: Generating comprehensive injury report (ALL injuries)...

📊 COMPREHENSIVE INJURY REPORT 📊
Total Injured Players: 46
[Shows all 46 injuries with updated ML predictions]
```

**Result**: No alerts (nothing new), but you see everyone's status and updated predictions.

### Example 3: Sharing With League

```bash
# Set in .env
ALERT_WINDOW_HOURS=999999

$ python monitor.py --once
# Generates injury_news.md

# Share injury_news.md with your league
# They see ALL injuries with ML predictions
```

---

## Technical Details

### How Alert Window Works:

1. **First time injury is seen**: `first_seen` timestamp recorded
2. **On subsequent checks**: Compare `first_seen` to current time
3. **If within window**: Include in alerts
4. **If outside window**: Still tracked, reported, gets ML predictions, but no alert

### Data Flow:

```
Sleeper API → Get all injuries →
  ├─ Save to database (historical tracking)
  ├─ ML predictions added (ALL injuries)
  ├─ Risk scores calculated (ALL injuries)
  ├─ Compare with previous → New/worsened? →
  │    ├─ Yes + within window → ALERT MODE
  │    └─ Otherwise → Just track
  └─ Save to injury_news.md (COMPREHENSIVE MODE - all injuries)
```

---

## Summary

**Think of it like this:**

- **Alert Mode** = "What's new and urgent?"
- **Comprehensive Mode** = "What's the complete injury situation?"

Both modes work together:
- Alerts keep you reactive and informed about breaking news
- Reports keep you strategic and aware of the full landscape
- ML predictions help you plan for both immediate and future moves

**You always get the full picture, but alerts help you focus on what needs immediate attention.**

---

## Quick Reference

**Want urgent alerts only**: Use default (`ALERT_WINDOW_HOURS=24`)

**Want to see everything**: Change to `ALERT_WINDOW_HOURS=999999`

**Want weekly summary**: Set to `ALERT_WINDOW_HOURS=168`

**Want hourly updates**: Set to `ALERT_WINDOW_HOURS=1`

**Always get**: Full comprehensive report with ALL injuries + ML predictions, regardless of alert window setting.
