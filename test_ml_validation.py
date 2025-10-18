#!/usr/bin/env python3
"""
Test ML predictions for accuracy and validate NFL rules
"""
from injury_database import InjuryDatabase
from ml_predictor import InjuryPredictor


def test_predictions():
    """Test various injury scenarios"""

    print("\n" + "="*80)
    print("ML PREDICTION VALIDATION TEST")
    print("="*80 + "\n")

    with InjuryDatabase() as db:
        predictor = InjuryPredictor(db)

        # Test cases representing real scenarios
        test_cases = [
            {
                'name': 'Test - IR Player (Joe Mixon scenario)',
                'injury': {
                    'name': 'Joe Mixon',
                    'position': 'RB',
                    'injury_status': 'IR',
                    'injury_body_part': 'Ankle'
                },
                'expected': 'Minimum 28 days (4 weeks) due to IR rules'
            },
            {
                'name': 'Test - Out Player (Hamstring)',
                'injury': {
                    'name': 'Player A',
                    'position': 'WR',
                    'injury_status': 'Out',
                    'injury_body_part': 'Hamstring'
                },
                'expected': 'At least 7 days (1 week)'
            },
            {
                'name': 'Test - Questionable (Minor)',
                'injury': {
                    'name': 'Player B',
                    'position': 'QB',
                    'injury_status': 'Questionable',
                    'injury_body_part': 'Ankle'
                },
                'expected': 'Less than 7 days typically'
            },
            {
                'name': 'Test - PUP (Season Start)',
                'injury': {
                    'name': 'Player C',
                    'position': 'TE',
                    'injury_status': 'PUP',
                    'injury_body_part': 'Knee'
                },
                'expected': 'Minimum 28 days (4 weeks) due to PUP rules'
            }
        ]

        for test in test_cases:
            print(f"\n{'='*80}")
            print(f"TEST: {test['name']}")
            print(f"{'='*80}")

            injury = test['injury']
            print(f"\nInput:")
            print(f"  Player: {injury['name']}")
            print(f"  Position: {injury['position']}")
            print(f"  Status: {injury['injury_status']}")
            print(f"  Body Part: {injury['injury_body_part']}")

            print(f"\nExpected: {test['expected']}")

            prediction = predictor.predict_recovery_time(injury)

            if prediction.get('error'):
                print(f"\n❌ ERROR: {prediction['error']}")
                continue

            print(f"\nActual Prediction:")
            print(f"  📊 Predicted days: {prediction['predicted_days']}")
            print(f"  📊 Confidence range: {prediction['confidence_low']}-{prediction['confidence_high']} days")
            print(f"  📅 Current NFL week: {prediction['current_week']}")
            print(f"  📅 Return NFL week: {prediction['return_week']}")
            print(f"  📅 Weeks from now: {prediction['weeks_out']}")
            print(f"  📅 Return date: {prediction['expected_return_date']}")

            # Validation
            status = injury['injury_status']
            days = prediction['predicted_days']

            print(f"\n✅ Validation:")
            if status in ['IR', 'PUP']:
                if days >= 28:
                    print(f"  ✓ PASS: {status} correctly shows {days} days (minimum 28)")
                else:
                    print(f"  ✗ FAIL: {status} shows {days} days but should be minimum 28!")

            elif status == 'Out':
                if days >= 7:
                    print(f"  ✓ PASS: Out status shows {days} days (at least 1 week)")
                else:
                    print(f"  ⚠ WARNING: Out status shows {days} days (typically at least 7)")

            # Week calculation validation
            expected_weeks = (days + 6) // 7  # Ceiling division
            actual_weeks = prediction['weeks_out']
            if expected_weeks == actual_weeks:
                print(f"  ✓ PASS: Week calculation correct ({days} days = {actual_weeks} weeks)")
            else:
                print(f"  ✗ FAIL: Week calculation wrong ({days} days should be {expected_weeks} weeks, got {actual_weeks})")

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_predictions()
