# NFL Injury News Integration Analysis

## Current State: How News is Used

### 📰 **News Sources**

Currently pulling from 2 RSS feeds:
```python
self.rss_feeds = [
    "https://sports.yahoo.com/nfl/rss.xml",
    "https://www.rotoworld.com/rss/feed.aspx?sport=nfl&ftype=news"
]
```

### 🔍 **How It Works Now**

#### Step 1: Fetch News
- Pulls all RSS feed entries from Yahoo Sports and Rotoworld
- Stores title, description, link, published date
- Caches in `self.news_cache['rss_news']`

#### Step 2: Match to Players
- For each injured player, searches news cache by name
- Matches on full name or last name
- Returns top 3 most relevant articles

#### Step 3: Sentiment Analysis
- Uses **TextBlob** to analyze headline sentiment
- Score: -1 (very negative) to +1 (very positive)
- Categorizes as: Severe, Moderate, Neutral, Positive

#### Step 4: Display
- Shows in injury reports and alerts
- Color-coded indicators (🔴 🟡 ⚪ 🟢)
- Includes news links for user to read

---

## ⚠️ **CRITICAL FINDING: News is NOT Used for ML Predictions**

### What News Currently Does:
✅ Provides context and headlines
✅ Sentiment analysis for severity
✅ Links to articles for manual reading
✅ Visual indicators in reports

### What News Does NOT Do:
❌ Does **NOT** influence ML predictions
❌ Does **NOT** adjust return timelines
❌ Does **NOT** modify risk scores
❌ Does **NOT** factor into model training

### The Gap:
```
ML Prediction: "28 days, NFL Week 11"
News Sentiment: "Severe (-0.85)" - "Season-ending surgery scheduled"

→ These are shown side-by-side but DON'T talk to each other!
```

**Example Problem:**
- ML predicts: "14 days return"
- News headline: "Player ruled out for season"
- Result: Conflicting information shown to user ⚠️

---

## 🔗 **How News COULD/SHOULD Be Integrated**

### Option 1: Sentiment-Adjusted Predictions (Quick Win)
Adjust ML predictions based on news severity:

```python
# If news is severely negative, increase timeline
if news_severity == 'Severe' and sentiment_score < -0.6:
    predicted_days *= 1.3  # Add 30% more time

# If news is positive (recovery progressing), decrease timeline
elif news_severity == 'Positive' and sentiment_score > 0.3:
    predicted_days *= 0.85  # Reduce by 15%
```

**Pros:**
- Simple to implement
- Uses existing sentiment analysis
- Provides more realistic predictions

**Cons:**
- Crude multiplier approach
- Doesn't parse actual content
- May over/under adjust

---

### Option 2: Keyword-Based Rule Overrides (Better)
Parse news for specific keywords and override predictions:

```python
news_keywords = {
    'season-ending': {'action': 'set_weeks', 'value': 18},
    'week-to-week': {'action': 'set_range', 'value': (1, 3)},
    'day-to-day': {'action': 'set_range', 'value': (1, 7)},
    'multiple weeks': {'action': 'set_min', 'value': 14},
    'surgery': {'action': 'set_min', 'value': 42},
    'torn': {'action': 'set_min', 'value': 180},  # ACL/Achilles
    'practicing': {'action': 'reduce', 'value': 0.7},
    'activated': {'action': 'return', 'value': 0}
}

# Example:
if 'season-ending' in news_text:
    predicted_days = 126  # Rest of season
    override_reason = "News reports season-ending injury"
```

**Pros:**
- More accurate than sentiment alone
- Catches specific medical terms
- Can override unrealistic ML predictions

**Cons:**
- Requires maintenance of keyword dictionary
- May miss context/nuance
- Could create false positives

---

### Option 3: NLP-Powered Timeline Extraction (Best)
Use NLP to extract actual timeline from news:

```python
# Parse news for timeline mentions
patterns = [
    r"out (\d+) weeks?",
    r"return in (Week \d+)",
    r"miss (\d+) games?",
    r"(\d+)-(\d+) weeks?",
    r"day-to-day",
    r"week-to-week",
    r"doubtful for (Week \d+)"
]

# Example headlines:
"McCaffrey expected to miss 4-6 weeks with Achilles injury"
→ Extract: 4-6 weeks = 28-42 days

"Jefferson listed as week-to-week with hamstring"
→ Extract: 1-3 weeks range

"Mixon placed on IR, out minimum 4 games"
→ Extract: Minimum 4 weeks = 28+ days
```

**Pros:**
- Most accurate approach
- Uses actual reported information
- Can detect ranges and minimums
- Respects journalistic reporting

**Cons:**
- More complex to implement
- Requires robust pattern matching
- News may be vague or conflicting

---

### Option 4: Practice Report Integration (Most Valuable)
Track Wednesday/Thursday/Friday practice participation:

```python
practice_status = {
    'DNP → DNP → DNP': 'Very unlikely to play (extend timeline)',
    'DNP → Limited → Limited': 'Questionable (50/50)',
    'DNP → Limited → Full': 'Likely to play (reduce timeline)',
    'Limited → Limited → Full': 'Very likely (reduce significantly)',
    'Full → Full → Full': 'Will play (return imminent)'
}

# Adjust ML prediction based on practice trend
if practice_trend == 'DNP → DNP → DNP':
    predicted_days = max(predicted_days, 7)  # At least 1 more week
elif practice_trend == 'Limited → Limited → Full':
    predicted_days = min(predicted_days, 3)  # Could play this week
```

**Pros:**
- Most reliable indicator of return
- Updated 3x per week
- Directly predicts game availability

**Cons:**
- Requires scraping practice reports
- Not available in RSS feeds (need team beat reporters)
- Twitter/X integration needed

---

## 📊 **Recommended Implementation**

### Phase 1: Quick Wins (Now)
1. **Keyword Override System**
   - Parse for "season-ending", "surgery", "activated"
   - Override ML predictions with hard rules
   - Show override reason to user

2. **Sentiment Adjustment**
   - Severe negative news (+20% timeline)
   - Positive recovery news (-15% timeline)
   - Display adjusted vs. raw prediction

### Phase 2: NLP Enhancement (Next)
3. **Timeline Extraction**
   - Regex patterns for "X weeks", "Y days"
   - Extract ranges ("4-6 weeks")
   - Prefer news timeline over ML when specific

4. **Conflicting Info Detection**
   - Flag when ML and news strongly disagree
   - Show warning: "⚠️ ML predicts 2 weeks, news reports 6+ weeks"
   - Let user decide which to trust

### Phase 3: Practice Reports (Future)
5. **Practice Participation Tracking**
   - Scrape team injury reports (Wed/Thu/Fri)
   - Twitter bot for beat reporter updates
   - Real-time adjustment based on practice status

---

## 🎯 **Example: Integrated Approach**

### Current Output:
```
Christian McCaffrey (RB, SF)
Status: IR

🤖 ML PREDICTION:
   NFL Week 11 (4 weeks, 28 days)

🔴 NEWS SENTIMENT: Severe (-0.82)
   "McCaffrey undergoes season-ending Achilles surgery"
```
**Problem:** ML says 4 weeks, news says season-ending! 😱

### With Integration:
```
Christian McCaffrey (RB, SF)
Status: IR

🤖 ML PREDICTION (OVERRIDDEN):
   ❌ Raw prediction: NFL Week 11 (4 weeks)
   ✅ News-adjusted: Season-ending (Rest of 2025)

   📰 News override reason:
      "McCaffrey undergoes season-ending Achilles surgery"
      Link: [Read more]

   ⚠️ Note: News timeline takes precedence over ML model
```

---

## 💡 **Immediate Action Items**

### 1. Add Keyword Override System
Create `news_analyzer.py`:
```python
class NewsAnalyzer:
    def check_timeline_overrides(self, news_items, ml_prediction):
        """Check if news contains timeline overrides"""
        for news in news_items:
            text = news['title'].lower() + ' ' + news['description'].lower()

            # Season-ending
            if any(word in text for word in ['season-ending', 'out for season', 'done for year']):
                return {
                    'override': True,
                    'timeline': 'season-ending',
                    'weeks': 18,
                    'reason': news['title']
                }

            # Surgery (typically 6+ weeks)
            if 'surgery' in text and 'minor' not in text:
                return {
                    'override': True,
                    'timeline': '6-12 weeks',
                    'weeks': 8,
                    'reason': f"Surgery reported: {news['title']}"
                }

            # Activated from IR
            if any(word in text for word in ['activated', 'designated to return', 'removed from ir']):
                return {
                    'override': True,
                    'timeline': 'return imminent',
                    'weeks': 0,
                    'reason': news['title']
                }

        return {'override': False}
```

### 2. Integrate with ML Predictor
Modify `ml_predictor.py`:
```python
def predict_with_news(self, injury_data, news_items):
    # Get base ML prediction
    ml_prediction = self.predict_recovery_time(injury_data)

    # Check for news overrides
    news_override = NewsAnalyzer().check_timeline_overrides(
        news_items,
        ml_prediction
    )

    if news_override['override']:
        ml_prediction['overridden'] = True
        ml_prediction['original_prediction'] = ml_prediction['predicted_days']
        ml_prediction['predicted_days'] = news_override['weeks'] * 7
        ml_prediction['override_reason'] = news_override['reason']

    return ml_prediction
```

### 3. Display in Reports
Show both ML and news-adjusted predictions:
```
🤖 ML PREDICTION:
   Base model: NFL Week 9 (2 weeks)
   📰 News adjusted: NFL Week 15 (8 weeks)
   Override: "Surgery scheduled for torn hamstring"
```

---

## 🚀 **Next Steps**

**Recommend implementing:**
1. ✅ Keyword override system (2-3 hours)
2. ✅ Display overridden predictions (1 hour)
3. ✅ Add override reasons to reports (30 min)

**This would fix the Joe Mixon scenario:**
- ML: "28 days"
- News: "No timetable for return"
- **Override**: "Indefinite - monitoring week-to-week"

**Want me to implement this now?** I can add:
- Keyword detection
- News-based overrides
- Integrated display showing both predictions
- Clear indication when news trumps ML

---

## 📝 **Summary**

### Current State:
- News is fetched and displayed ✅
- Sentiment analyzed ✅
- **But NOT used to adjust predictions** ❌

### The Problem:
- ML and news can contradict each other
- Users see conflicting information
- "Season-ending" news but ML says "2 weeks"

### The Solution:
- Parse news for specific timelines
- Override ML when news is more specific
- Show both for transparency
- Let users make informed decisions

**Bottom line:** News is currently just "FYI" - we should make it "actionable intelligence" that improves prediction accuracy!

Want me to implement the keyword override system now?
