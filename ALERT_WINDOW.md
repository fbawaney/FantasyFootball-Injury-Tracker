# 24-Hour Alert Window Feature

## What Changed

The injury monitor now uses a **24-hour alert window** - you'll only be alerted about injuries when they're first reported or within 24 hours of first being detected. After that, injuries are still tracked but won't trigger alerts.

This prevents alert fatigue from seeing the same injuries over and over!

## How It Works

### Timeline Example

**Sunday 1:00 PM** - Christian McCaffrey gets injured
```
🚨 INJURY ALERT 🚨
🆕 NEW INJURY
   Player: Christian McCaffrey
   Status: Out
   💡 BACKUP: Jordan Mason - ✅ AVAILABLE
```
**You get alerted!**

---

**Sunday 1:30 PM** - Check runs again
```
✓ No new injuries detected
```
**No alert** (same injury, within 24 hours, no status change)

---

**Monday 10:00 AM** - Check runs, CMC still out
```
✓ No new injuries detected
```
**No alert** (still within 24 hours)

---

**Monday 1:30 PM** - CMC status worsens to IR
```
🚨 INJURY ALERT 🚨
⚠️ WORSENED: Out → IR (first reported 24.5 hours ago)
   Player: Christian McCaffrey
   Status: IR
```
**You get alerted!** (Status worsened, even though > 24 hours)

---

**Tuesday 2:00 PM** - Check runs, CMC still on IR
```
✓ No new injuries detected
```
**No alert** (>24 hours since first seen, no status change)

## What Triggers Alerts

### ✅ You WILL be alerted for:

1. **Brand New Injuries** (player wasn't injured before)
   ```
   🆕 NEW INJURY
   ```

2. **Injury Worsened Within 24 Hours** (Questionable → Out)
   ```
   ⚠️ WORSENED: Questionable → Out (first reported 8.2 hours ago)
   ```

3. **Injury Worsened Anytime** (even after 24 hours, if severity increases)
   ```
   ⚠️ WORSENED: Doubtful → IR (first reported 36.5 hours ago)
   ```

### ❌ You will NOT be alerted for:

1. **Same injury after 24 hours** (player still injured, no status change)
2. **Improved status after 24 hours** (Questionable → Healthy - good news!)
3. **Unchanged injuries on subsequent checks**

## Summary Reports Still Show Everything

The `--report` command and end-of-check summaries show **ALL current injuries**, not just recent ones:

```bash
python monitor.py --report
```

```
📊 INJURY SUMMARY REPORT
Total Injuries: 15

⚠️  OWNED PLAYERS WITH INJURIES
Your Team:
  • Christian McCaffrey (RB, SF) - Out (Day 3)
  • Deebo Samuel (WR, SF) - Questionable (Day 1)
  👉 Backup: Jordan Mason - ✅ AVAILABLE
```

## Configuration

### Default: 24 Hours

In `.env`:
```bash
ALERT_WINDOW_HOURS=24  # Default
```

### Customize Alert Window

Want more or less frequent alerts?

```bash
# More aggressive - alert for 48 hours
ALERT_WINDOW_HOURS=48

# Less aggressive - alert for 12 hours only
ALERT_WINDOW_HOURS=12

# Alert only once (first detection)
ALERT_WINDOW_HOURS=0

# Alert for a full week
ALERT_WINDOW_HOURS=168  # 7 days × 24 hours
```

### Game Day vs Off-Season

**During Games (Sundays):**
```bash
ALERT_WINDOW_HOURS=8   # Alert throughout game day
CHECK_INTERVAL=15      # Check every 15 minutes
```

**Rest of Week:**
```bash
ALERT_WINDOW_HOURS=24  # Standard 24-hour window
CHECK_INTERVAL=60      # Check hourly
```

## Data Storage

Injury records now include timestamps:

```json
{
  "name": "Christian McCaffrey",
  "injury_status": "Out",
  "first_seen": "2025-10-15T13:00:00",
  "last_updated": "2025-10-15T13:30:00",
  ...
}
```

- **first_seen**: When injury was first detected (never changes)
- **last_updated**: When injury data was last refreshed (changes each check)

## Example Scenarios

### Scenario 1: Sunday Game Day
```
1:05 PM - Player injured, alerted ✅
1:35 PM - Still injured, no alert ❌
2:05 PM - Still injured, no alert ❌
4:15 PM - Status worsens, alerted ✅
```

### Scenario 2: Week-Long Injury
```
Sunday 1 PM - Player injured, alerted ✅
Monday 9 AM - Still injured, no alert ❌
Tuesday 5 PM - Still injured, no alert ❌
Sunday 12 PM - Still injured, no alert ❌ (7 days later)
```

### Scenario 3: Re-injury
```
Week 1 Sunday - Player injured, alerted ✅
Week 1 Friday - Player healthy, no alert ❌
Week 2 Sunday - Player re-injured, alerted ✅ (new injury!)
```

## Benefits

### 1. Reduces Alert Fatigue
Don't see the same injury 50 times during the season

### 2. Still Tracks Everything
All injuries are tracked and shown in reports

### 3. Catches Important Changes
Status worsening always alerts you

### 4. Customizable
Adjust alert window to your preference

### 5. Smart Timestamps
System remembers when each injury first appeared

## Monitoring Flow

### Continuous Mode (`python monitor.py`)

```
🏈 FANTASY FOOTBALL INJURY MONITOR
Monitoring league: 12345
Check interval: 30 minutes
Alert window: 24 hours
Depth chart tracking: Enabled

[Check 1 - 1:00 PM Sunday]
  ⚠️  3 new injuries detected!
  🚨 Shows alerts

[Check 2 - 1:30 PM Sunday]
  ✓ No new injuries detected

[Check 3 - 2:00 PM Sunday]
  ⚠️  1 new injury detected!
  🚨 Shows alert

[Check 4 - 2:30 PM Sunday]
  ✓ No new injuries detected

... continues forever
```

### After 24 Hours

```
[Check 50 - Monday 2:00 PM]
  ✓ No new injuries detected

  📊 INJURY SUMMARY REPORT
  Total Injuries: 12
  - Owned Players: 5
  - Free Agents: 7

  (All injuries shown, including old ones)
```

## Viewing All Injuries Anytime

```bash
# See full injury report
python monitor.py --report
```

Shows everything, regardless of alert window.

## Migration from Old Data

If you have existing `injury_data.json` without timestamps:

1. Old injuries get `first_seen` set to current time on first check
2. They're treated as "new" for that check
3. After that, alert window applies normally

## Technical Details

### Timestamp Format
ISO 8601: `2025-10-15T13:00:00.123456`

### Time Calculations
```python
hours_since_first = (now - first_seen).total_seconds() / 3600
if hours_since_first <= alert_window_hours:
    send_alert()
```

### Severity Scale
```python
{
    'IR': 5,        # Most severe
    'Out': 4,
    'PUP': 4,
    'Suspended': 4,
    'Doubtful': 3,
    'Questionable': 2  # Least severe
}
```

Worsening = severity increases (Questionable → Out)

## Frequently Asked Questions

**Q: Will I miss injuries if I stop monitoring for 2 days?**
A: No! When you restart, the system compares against saved data. New injuries detected on restart will alert.

**Q: What if a player's status improves?**
A: Improvements (Out → Questionable) don't trigger alerts. You'll see it in the summary report.

**Q: Can I be alerted forever for a specific player?**
A: Set `ALERT_WINDOW_HOURS=8760` (1 year) in `.env`

**Q: What if I want alerts only once per injury?**
A: Set `ALERT_WINDOW_HOURS=0` - only brand new injuries will alert

**Q: Does this affect the summary reports?**
A: No! Reports always show ALL injuries, regardless of age.

**Q: What happens to old injury_data.json files?**
A: They're upgraded automatically. Old injuries get `first_seen` timestamps on first run.

---

**Recommended Settings:**

**For active monitoring (Sundays):**
```bash
ALERT_WINDOW_HOURS=12
CHECK_INTERVAL=15
```

**For background monitoring (rest of week):**
```bash
ALERT_WINDOW_HOURS=24
CHECK_INTERVAL=60
```
