# ML-Enhanced Injury Tracker Features

## Overview

Your Fantasy Football Injury Tracker now includes **machine learning predictions** and **injury risk scoring** to give you a competitive edge. These features analyze historical injury data to predict return timelines and assess player injury risk.

## 🆕 New Features

### 1. **ML-Powered Return Timeline Predictions**

The tracker now predicts when injured players will return using a Random Forest machine learning model trained on historical injury data.

**What you get:**
- **Expected return week** (e.g., "Week 10")
- **Predicted days out** (e.g., "14 days")
- **Confidence range** (e.g., "10-18 days")
- **Expected return date** (e.g., "2025-11-15")

**How it works:**
- Analyzes injury type (hamstring, knee, ankle, etc.)
- Considers injury severity (Out, IR, Doubtful, etc.)
- Factors in player's position (QB, RB, WR, TE)
- Looks at player's injury history
- Checks for recurring injuries (same body part multiple times)

### 2. **Injury Risk Scoring (0-100)**

Each injured player receives a comprehensive risk score that helps you understand the severity and recurrence potential of their injury.

**Risk Levels:**
- 🔴 **Critical (75-100)**: Very high risk - recurring issues, slow recovery patterns
- 🟠 **High (60-74)**: Elevated risk - multiple recent injuries
- 🟡 **Moderate (40-59)**: Some concern - watch closely
- 🟢 **Low (20-39)**: Minor concern - generally healthy player
- ⚪ **Minimal (0-19)**: Clean injury history

**Factors analyzed:**
- **Frequency**: How often the player gets injured
- **Recurrence**: Same injury multiple times (chronic issues)
- **Severity**: Current injury status (IR worse than Questionable)
- **Recency**: Recent vs. old injuries
- **Recovery**: Historical recovery time patterns

### 3. **Historical Injury Database**

All injuries are now tracked in a SQLite database for:
- Long-term pattern analysis
- Player injury history tracking
- ML model training
- Trend identification

### 4. **Enhanced Reports**

Your injury reports (both console and markdown) now include:
- ML predictions with confidence intervals
- Risk assessment with detailed breakdown
- Chronic injury warnings
- Historical context for each injury

## 📦 Installation

### Install New Dependencies

```bash
pip install -r requirements.txt
```

This adds:
- `scikit-learn` - Machine learning library
- `pandas` - Data manipulation
- `numpy` - Numerical computations

### Initialize ML Features

Run the setup script to initialize the database and train the model:

```bash
python setup_ml.py
```

This will:
1. Create `injury_history.db` database
2. Load current injury data from Sleeper API
3. Import your existing `injury_data.json`
4. Generate simulated historical data for training
5. Train the ML prediction model
6. Save model to `models/injury_predictor.pkl`

**Note**: Setup takes ~2-3 minutes on first run.

## 🚀 Usage

### Running with ML Features (Default)

ML predictions are **enabled by default**:

```bash
python monitor.py --once
```

### Disabling ML Features

If you want to run without ML (faster, no setup required):

Modify `monitor.py` to pass `enable_ml=False`:

```python
self.injury_tracker = InjuryTracker(
    depth_chart_manager=self.depth_chart_manager,
    enable_ml=False  # Disable ML features
)
```

## 📊 Example Output

### Console Alert with ML

```
🆕 NEW INJURY
   Player: Christian McCaffrey
   Position: RB | Team: SF
   Status: Out
   Injury: Achilles
   🏈 OWNED BY: Team Alpha (Manager: John Doe)

   🤖 ML PREDICTION:
      Expected return: Week 12 (42 days)
      Confidence range: 35-49 days
      Return date: 2025-11-28

   🔴 INJURY RISK: High (72/100)
      2 injuries in last 6 months; Recurring Achilles injury (2x)
      Chronic issues: Achilles, Hamstring

   🔴 NEWS SENTIMENT: Severe (Score: -0.72)

   💡 DIRECT BACKUP:
      Jordan Mason (RB, SF)
      ✅ AVAILABLE as Free Agent - ADD NOW!
```

### Markdown Report with ML

The `injury_news.md` file now includes:

```markdown
### Christian McCaffrey (SF) - Out

**Owner**: Team Alpha

**🤖 ML Prediction**:
- Expected return: Week 12 (42 days)
- Range: 35-49 days
- Return date: 2025-11-28

**⚠️ Injury Risk Assessment**: 🔴 High (Score: 72/100)
- 2 injuries in last 6 months; Recurring Achilles injury (2x)
- Chronic issues: Achilles, Hamstring

**Backup Player**: Jordan Mason (RB, SF)
- ✅ **Available** as free agent
```

## 🛠️ Advanced Features

### Manual Database Operations

#### Load Historical Data

```bash
# Initialize database with current + simulated data
python historical_data_loader.py --init

# Sync only current data (no simulation)
python historical_data_loader.py --sync

# Import from specific JSON file
python historical_data_loader.py --file my_injuries.json
```

#### Train/Retrain Model

```bash
# Train the ML model
python ml_predictor.py --train

# Test a prediction
python ml_predictor.py --predict
```

#### Test Risk Scoring

```bash
python risk_scorer.py
```

## 📈 How Predictions Improve Over Time

The more you use the tracker:
1. **More injury data** is collected in the database
2. **Better predictions** as model learns from real recovery times
3. **Improved risk scores** with more player history

### Retraining the Model

As you accumulate more data, retrain the model:

```bash
python ml_predictor.py --train
```

This should be done:
- Every few weeks during the season
- At the start of each new season
- After major injury data imports

## 🗂️ Files Created

```
fantasyfootball/
├── injury_database.py          # SQLite database manager
├── historical_data_loader.py   # Data import/simulation
├── ml_predictor.py             # ML prediction engine
├── risk_scorer.py              # Injury risk calculator
├── setup_ml.py                 # Setup script
├── ML_FEATURES.md              # This file
├── injury_history.db           # SQLite database (created on setup)
└── models/
    └── injury_predictor.pkl    # Trained ML model (created on setup)
```

## ⚙️ Configuration

ML features are controlled in `injury_tracker.py`:

```python
def __init__(self, depth_chart_manager=None, enable_ml: bool = True):
    # Set enable_ml=False to disable ML predictions
    ...
```

## 🐛 Troubleshooting

### "No training data available"

**Solution**: Run the setup script first:
```bash
python setup_ml.py
```

### Model predictions seem inaccurate

**Solution**: You need more historical data. Options:
1. Run setup again to generate more simulated data
2. Let the tracker run for several weeks to collect real data
3. Import historical injury data from external sources

### ML components won't load

**Solution**: Check that all dependencies are installed:
```bash
pip install scikit-learn pandas numpy
```

### Database locked errors

**Solution**: Only one process can write to the database at a time. Make sure you're not running multiple instances of the tracker.

## 🔮 Future Enhancements

Potential improvements for Phase 2:
- **Practice report integration**: Track DNP/Limited/Full participation
- **Weather impact**: Adjust predictions for outdoor games
- **Opponent strength**: Factor in team schedules
- **Player age**: Weight predictions by age/experience
- **Position-specific models**: Separate models for QB/RB/WR/TE
- **Ensemble models**: Combine multiple ML algorithms
- **Real-time updates**: Live prediction updates as new data arrives

## 🎯 Tips for Maximum Value

1. **Run regularly**: More data = better predictions
2. **Review risk scores**: High-risk players may not be worth the headache
3. **Compare timelines**: Use predictions to decide when to pick up backups
4. **Monitor chronic issues**: Players with recurring injuries are risky long-term holds
5. **Share with league**: If your league values transparency, share the dashboard!

## 📝 Technical Details

### ML Model Architecture

- **Algorithm**: Random Forest Regressor
- **Target**: Days missed (recovery time)
- **Features**:
  - Injury body part (encoded)
  - Player position (encoded)
  - Injury severity (Out=3, IR=5, etc.)
  - Player's total injury count
  - Recurrence count for this body part
  - Season progress (week/18)

### Risk Score Calculation

**Weighted formula**:
```
Risk Score = (
    Frequency * 0.30 +
    Recurrence * 0.25 +
    Severity * 0.20 +
    Recency * 0.15 +
    Recovery * 0.10
) × 100
```

### Database Schema

**injuries** table:
- Player info (name, position, team)
- Injury details (body part, status, notes)
- Dates (start, end, days missed)
- Season/week context

**player_summary** table:
- Aggregated stats per player
- Total injuries, days missed
- Recurring body parts (JSON)
- Injury-prone score

---

## ❓ Questions?

Check out the main README.md or examine the source code:
- `injury_database.py` - Database operations
- `ml_predictor.py` - ML predictions
- `risk_scorer.py` - Risk calculations
- `historical_data_loader.py` - Data import

**Enjoy your ML-powered competitive advantage!** 🏈🤖
