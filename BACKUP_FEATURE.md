# Backup Player Feature - Quick Reference

## Overview

The injury tracker now automatically identifies and shows backup players for injured players! This helps you make quick waiver wire decisions.

## What You'll See

When a player gets injured, alerts now include:

```
🚨 INJURY ALERT 🚨
🆕 NEW INJURY
   Player: Christian McCaffrey
   Position: RB | Team: SF
   Status: Out
   Injury: Achilles
   🏈 OWNED BY: Your Team (Manager: Your Name)

   💡 BACKUP PLAYER:
      Name: Jordan Mason (RB, SF)
      Depth Chart: #2
      Status: ✅ AVAILABLE as Free Agent - ADD NOW!

   Source: Sleeper API
```

## Three Possible Backup Statuses

### 1. ✅ Available as Free Agent
```
Status: ✅ AVAILABLE as Free Agent - ADD NOW!
```
**Action**: The backup is unowned - grab them immediately!

### 2. ❌ Already Owned
```
Status: ❌ Owned by Team Beta
        (Manager: Jane Smith)
```
**Action**: Someone else has the handcuff. Consider other options.

### 3. ⚠️  Not on Any Roster
```
Status: ⚠️  Not on any roster (deep backup)
```
**Action**: This is a 3rd+ string player, may not be fantasy relevant.

## How It Works

### Data Sources
- **Depth Charts**: ESPN API (all 32 NFL teams)
- **Ownership**: Your Yahoo Fantasy League
- **Injuries**: Sleeper API

### Process
1. Player gets injured
2. System looks up team's depth chart
3. Finds next player at that position
4. Checks if they're owned in your league
5. Shows you the result!

## Supported Positions

Backup tracking for fantasy-relevant positions:
- **QB** - Quarterbacks
- **RB** - Running Backs
- **WR** - Wide Receivers
- **TE** - Tight Ends

Kickers (K) and Defenses (DEF) are excluded (less relevant for backups).

## Example Scenarios

### Scenario 1: Starting RB Injured
```
Player: Saquon Barkley (RB, PHI)
Status: Out
Backup: Kenneth Gainwell (RB, PHI)
Status: ✅ AVAILABLE
```
**Decision**: Grab Gainwell immediately - likely to get volume

### Scenario 2: Backup Already Rostered
```
Player: Travis Kelce (TE, KC)
Status: Doubtful
Backup: Noah Gray (TE, KC)
Status: ❌ Owned by Team Alpha
```
**Decision**: Look at other TEs, can't get the direct replacement

### Scenario 3: WR Committee
```
Player: DeVonta Smith (WR, PHI)
Status: Out
Backup: Olamide Zaccheaus (WR, PHI)
Status: ⚠️  Not on any roster
```
**Decision**: WR3/4 unlikely to provide fantasy value, monitor situation

## Summary Reports Include Backups

The daily summary report also shows backup info:

```
📊 INJURY SUMMARY REPORT
⚠️  OWNED PLAYERS WITH INJURIES

Your Team:
  • Christian McCaffrey (RB, SF)
    Status: Out
    Injury: Achilles
    👉 Backup: Jordan Mason - ✅ AVAILABLE

Team Beta:
  • Travis Kelce (TE, KC)
    Status: Questionable
    Injury: Ankle
    👉 Backup: Noah Gray - Owned by Team Alpha
```

## Configuration

### Enable/Disable Backup Tracking

Backup tracking is **enabled by default**. To disable:

```python
# In monitor.py __init__
monitor = InjuryMonitor(use_depth_charts=False)
```

Or modify the default:

```python
# monitor.py line 24
def __init__(self, use_depth_charts: bool = False):  # Disable by default
```

### Performance

- **First run**: Fetches all 32 team depth charts (~10 seconds)
- **Subsequent checks**: Uses cached data (instant)
- **Depth charts cached**: For entire session
- **Refresh**: Automatic on restart

## Troubleshooting

### "No backup listed on depth chart"

**Cause**: ESPN depth chart doesn't have a #2 listed for that position

**Reason**: Could be:
- Position battle/committee approach
- Depth chart not yet updated
- Team doesn't publish full depth chart

**Action**: Manually check team news/depth charts

### Backup shown isn't the "real" backup

**Cause**: Depth charts may not reflect coaching decisions

**Note**: Official depth charts != actual usage. Use this as a starting point, not gospel.

### Depth chart outdated

**Solution**: Restart the monitor to fetch fresh depth charts

```bash
# Stop and restart
Ctrl+C
python monitor.py
```

## API Details

### ESPN Depth Chart Endpoint
```
https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{teamID}/depthcharts
```

### Team ID Mapping
All 32 teams mapped in `depth_chart.py`:
```python
'SF': 25, 'KC': 12, 'PHI': 21, 'BUF': 2, ...
```

### Data Structure
```python
backup_player = {
    'name': 'Jordan Mason',
    'position': 'RB',
    'team': 'SF',
    'depth': 2,  # Position on depth chart
    'available': True,  # Free agent?
    'owned_by_team': 'Free Agent',
    'owned_by_manager': None
}
```

## Module: depth_chart.py

New module added (12KB) with these main functions:

### `fetch_team_depth_chart(team_abbr)`
Fetches depth chart for one team from ESPN API

### `get_backup_for_player(player_name, team, position)`
Finds the next player behind an injured starter

### `check_player_availability(backup_name, yahoo_players)`
Checks if backup is owned or available in your league

### `fetch_all_depth_charts()`
Fetches all 32 teams at once (with rate limiting)

## Tips for Best Use

### 1. Act Fast on Alerts
When you see "✅ AVAILABLE", grab them before your league mates!

### 2. Prioritize Bell Cows
RB backups on run-heavy teams are most valuable:
- Eagles, 49ers, Browns, etc.

### 3. Monitor Starter Status
- **Out** = Backup likely starts
- **Doubtful** = Backup might start
- **Questionable** = Backup probably won't start

### 4. Consider Committee Situations
Some teams don't have a clear #1/#2:
- Browns RBs
- Patriots RBs
- Backups may not provide value

### 5. TE Situation-Dependent
TE backups rarely fantasy relevant unless:
- Starter is elite (Kelce, Andrews, etc.)
- Team is pass-heavy

## Future Enhancements

Potential additions:
- [ ] Historical snap share for backups
- [ ] Projected fantasy points
- [ ] Multiple backup options (show #2 and #3)
- [ ] Offensive line injury impact
- [ ] Vegas odds adjustment
- [ ] ADP/ownership percentages

## Questions?

**Q: Why is the backup wrong?**
A: Depth charts are updated weekly by teams, may not reflect latest coaching decisions.

**Q: Can I see backups without alerts?**
A: Yes! Run `python monitor.py --report` to see all current injuries with backups.

**Q: Does this work for defenses?**
A: No, only QB/RB/WR/TE. Individual defensive players aren't fantasy relevant.

**Q: How often do depth charts update?**
A: Currently fetched once per session. Restart to refresh.

**Q: Can I disable this feature?**
A: Yes, modify `monitor.py` line 24 to `use_depth_charts=False`

---

**Pro Tip**: Set up desktop notifications (`NOTIFICATION_METHOD=desktop` in `.env`) so you get instant alerts when a player is injured and their backup is available!
