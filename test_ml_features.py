#!/usr/bin/env python3
"""
Quick test script to verify ML features are working
"""
import os
from injury_database import InjuryDatabase
from ml_predictor import InjuryPredictor
from risk_scorer import InjuryRiskScorer


def test_database():
    """Test database connectivity and basic operations"""
    print("\n" + "="*60)
    print("TEST 1: DATABASE CONNECTIVITY")
    print("="*60)

    try:
        with InjuryDatabase() as db:
            # Test adding an injury
            test_injury = {
                'name': 'Test Player',
                'position': 'RB',
                'team': 'TST',
                'injury_status': 'Out',
                'injury_body_part': 'Hamstring',
                'source': 'Test'
            }

            injury_id = db.add_injury_record(test_injury)
            print(f"✅ Database connection successful")
            print(f"✅ Created test injury record (ID: {injury_id})")

            # Test retrieving history
            history = db.get_player_injury_history('Test Player')
            print(f"✅ Retrieved injury history ({len(history)} records)")

            # Test summary
            db.update_player_summary('Test Player')
            summary = db.get_player_summary('Test Player')
            print(f"✅ Player summary created")

            return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_ml_predictor():
    """Test ML predictor"""
    print("\n" + "="*60)
    print("TEST 2: ML PREDICTOR")
    print("="*60)

    try:
        with InjuryDatabase() as db:
            predictor = InjuryPredictor(db)

            # Check if model exists
            if predictor.model is None:
                print("⚠️  No trained model found")
                print("   Run 'python setup_ml.py' to train the model")
                return False

            # Test prediction
            test_injury = {
                'name': 'Test Player',
                'position': 'RB',
                'injury_status': 'Out',
                'injury_body_part': 'Hamstring'
            }

            prediction = predictor.predict_recovery_time(test_injury)

            if prediction.get('error'):
                print(f"❌ Prediction failed: {prediction['error']}")
                return False

            print(f"✅ ML predictor working")
            print(f"   Sample prediction:")
            print(f"   - Expected days: {prediction['predicted_days']}")
            print(f"   - Range: {prediction['confidence_low']}-{prediction['confidence_high']} days")
            print(f"   - Weeks out: {prediction['weeks_out']}")

            return True

    except Exception as e:
        print(f"❌ ML predictor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_scorer():
    """Test risk scorer"""
    print("\n" + "="*60)
    print("TEST 3: RISK SCORER")
    print("="*60)

    try:
        with InjuryDatabase() as db:
            scorer = InjuryRiskScorer(db)

            test_injury = {
                'name': 'Test Player',
                'position': 'RB',
                'injury_status': 'Out',
                'injury_body_part': 'Hamstring'
            }

            risk = scorer.calculate_risk_score('Test Player', test_injury)

            print(f"✅ Risk scorer working")
            print(f"   Sample risk assessment:")
            print(f"   - Risk level: {risk['risk_level']}")
            print(f"   - Risk score: {risk['risk_score']}/100")
            print(f"   - Message: {risk['message']}")

            return True

    except Exception as e:
        print(f"❌ Risk scorer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration with injury tracker"""
    print("\n" + "="*60)
    print("TEST 4: INTEGRATION TEST")
    print("="*60)

    try:
        from injury_tracker import InjuryTracker

        tracker = InjuryTracker(enable_ml=True)

        if not tracker.enable_ml:
            print("⚠️  ML features not enabled in tracker")
            return False

        if tracker.db is None:
            print("❌ Database not initialized")
            return False

        if tracker.predictor is None:
            print("❌ Predictor not initialized")
            return False

        if tracker.risk_scorer is None:
            print("❌ Risk scorer not initialized")
            return False

        print(f"✅ All ML components initialized in tracker")
        print(f"✅ Ready for production use")

        tracker.close()
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("ML FEATURES TEST SUITE")
    print("="*60)

    results = []

    # Run all tests
    results.append(("Database", test_database()))
    results.append(("ML Predictor", test_ml_predictor()))
    results.append(("Risk Scorer", test_risk_scorer()))
    results.append(("Integration", test_integration()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! ML features are ready to use.")
        print("\nNext steps:")
        print("  1. Run: python monitor.py --once")
        print("  2. Check injury_news.md for ML predictions")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nIf ML predictor failed:")
        print("  - Run: python setup_ml.py")
        print("\nIf other tests failed:")
        print("  - Check that all dependencies are installed")
        print("  - Run: pip install -r requirements.txt")

    print()


if __name__ == "__main__":
    main()
