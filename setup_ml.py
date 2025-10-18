#!/usr/bin/env python3
"""
Setup and Test Script for ML-Enhanced Injury Tracker
Initializes the database, trains the model, and runs a test
"""
import os
import sys
from injury_database import InjuryDatabase
from historical_data_loader import HistoricalDataLoader
from ml_predictor import InjuryPredictor


def main():
    print("\n" + "="*80)
    print("ML-ENHANCED INJURY TRACKER SETUP")
    print("="*80 + "\n")

    print("This script will:")
    print("  1. Initialize the injury history database")
    print("  2. Load current injury data from Sleeper API")
    print("  3. Import existing injury_data.json (if available)")
    print("  4. Generate simulated historical data for ML training")
    print("  5. Train the ML prediction model")
    print("  6. Run a test prediction\n")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Setup cancelled.")
        return

    # Step 1: Initialize database
    print("\n" + "="*80)
    print("STEP 1: INITIALIZING DATABASE")
    print("="*80)

    with InjuryDatabase() as db:
        loader = HistoricalDataLoader(db)

        # Step 2: Load historical data
        print("\n" + "="*80)
        print("STEP 2: LOADING HISTORICAL DATA")
        print("="*80)

        loader.initialize_database(include_simulated=True)

        # Step 3: Train ML model
        print("\n" + "="*80)
        print("STEP 3: TRAINING ML MODEL")
        print("="*80)

        predictor = InjuryPredictor(db)

        try:
            predictor.train_model()
        except ValueError as e:
            print(f"\nError: {e}")
            print("Not enough training data. Please ensure historical data was loaded.")
            return

        # Step 4: Test prediction
        print("\n" + "="*80)
        print("STEP 4: TESTING PREDICTION")
        print("="*80)

        # Test with a sample injury
        test_injury = {
            'name': 'Test Player',
            'position': 'RB',
            'injury_status': 'Out',
            'injury_body_part': 'Hamstring'
        }

        print("\nTest case:")
        print(f"  Player: {test_injury['name']}")
        print(f"  Position: {test_injury['position']}")
        print(f"  Injury: {test_injury['injury_body_part']}")
        print(f"  Status: {test_injury['injury_status']}")

        prediction = predictor.predict_recovery_time(test_injury)

        if prediction.get('error'):
            print(f"\nError: {prediction['error']}")
        else:
            print(f"\n✅ Prediction successful!")
            print(f"  Expected days out: {prediction['predicted_days']}")
            print(f"  Confidence range: {prediction['confidence_low']}-{prediction['confidence_high']} days")
            print(f"  Weeks out: {prediction['weeks_out']}")
            print(f"  Expected return: {prediction['expected_return_date']}")

    print("\n" + "="*80)
    print("SETUP COMPLETE!")
    print("="*80)

    print("\nYou can now run the injury tracker with ML predictions enabled:")
    print("  python monitor.py --once")
    print("\nOr run continuous monitoring:")
    print("  python monitor.py")

    print("\nThe following files have been created:")
    print("  - injury_history.db (SQLite database)")
    print("  - models/injury_predictor.pkl (Trained ML model)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
