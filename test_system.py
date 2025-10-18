"""
System Test Script
Tests each component independently to verify setup
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_result(test_name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"       {message}")


def test_environment():
    """Test environment variables"""
    print_header("Testing Environment Configuration")

    tests = [
        ("YAHOO_CLIENT_ID", os.getenv('YAHOO_CLIENT_ID')),
        ("YAHOO_CLIENT_SECRET", os.getenv('YAHOO_CLIENT_SECRET')),
        ("YAHOO_LEAGUE_ID", os.getenv('YAHOO_LEAGUE_ID')),
    ]

    all_passed = True
    for var_name, var_value in tests:
        passed = var_value is not None and var_value != f"your_{var_name.lower()}_here"
        print_result(var_name, passed, var_value[:20] + "..." if passed else "Not set")
        if not passed:
            all_passed = False

    return all_passed


def test_dependencies():
    """Test required Python packages"""
    print_header("Testing Dependencies")

    packages = [
        ("yfpy", "Yahoo Fantasy API wrapper"),
        ("requests", "HTTP library"),
        ("dotenv", "Environment variables"),
        ("schedule", "Task scheduler"),
    ]

    all_passed = True
    for package, description in packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print_result(package, True, description)
        except ImportError:
            print_result(package, False, f"Not installed - {description}")
            all_passed = False

    return all_passed


def test_injury_tracker():
    """Test injury tracker module"""
    print_header("Testing Injury Tracker")

    try:
        from injury_tracker import InjuryTracker

        tracker = InjuryTracker()
        print_result("Import InjuryTracker", True)

        # Test Sleeper API
        print("\nFetching data from Sleeper API (this may take a moment)...")
        injuries = tracker.get_injured_players_from_sleeper()

        if injuries:
            print_result("Sleeper API Connection", True, f"Found {len(injuries)} injured players")
            print(f"\nSample injuries:")
            for injury in injuries[:3]:
                print(f"  - {injury['name']} ({injury['position']}, {injury['team']}): {injury['injury_status']}")
            return True
        else:
            print_result("Sleeper API Connection", False, "No data returned")
            return False

    except Exception as e:
        print_result("Injury Tracker Test", False, str(e))
        return False


def test_notifier():
    """Test notification system"""
    print_header("Testing Notification System")

    try:
        from notifier import Notifier

        notifier = Notifier('console')
        print_result("Import Notifier", True)

        # Test with sample data
        test_injury = [{
            'name': 'Test Player',
            'position': 'RB',
            'team': 'TST',
            'injury_status': 'Questionable',
            'injury_body_part': 'Ankle',
            'owned_by_team': 'Test Team',
            'owned_by_manager': 'Test Manager',
            'alert_type': 'NEW_INJURY',
            'source': 'Test'
        }]

        print("\nSending test notification:")
        notifier.send_alert(test_injury)
        print_result("Console Notification", True)

        return True

    except Exception as e:
        print_result("Notifier Test", False, str(e))
        return False


def test_yahoo_client():
    """Test Yahoo Fantasy client"""
    print_header("Testing Yahoo Fantasy Client")

    # Check if credentials are set
    if not os.getenv('YAHOO_CLIENT_ID') or not os.getenv('YAHOO_LEAGUE_ID'):
        print_result("Yahoo Client", False, "Environment variables not set")
        print("\n⚠️  Skipping Yahoo API test - configure .env first")
        return False

    try:
        from yahoo_client import YahooFantasyClient

        print_result("Import YahooFantasyClient", True)
        print("\n⚠️  Yahoo API test requires OAuth authentication")
        print("    Run 'python monitor.py --once' to test Yahoo connection")

        return True

    except Exception as e:
        print_result("Yahoo Client Test", False, str(e))
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  FANTASY FOOTBALL INJURY TRACKER - SYSTEM TEST")
    print("=" * 80)

    results = {
        "Environment": test_environment(),
        "Dependencies": test_dependencies(),
        "Injury Tracker": test_injury_tracker(),
        "Notifier": test_notifier(),
        "Yahoo Client": test_yahoo_client(),
    }

    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 80)
    print(f"  Results: {passed}/{total} tests passed")
    print("=" * 80)

    if passed == total:
        print("\n✓ All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python monitor.py --once")
        print("     (Authenticate with Yahoo)")
        print("  2. Run: python monitor.py")
        print("     (Start monitoring)")
    else:
        print("\n⚠️  Some tests failed. Please:")
        print("  1. Check your .env configuration")
        print("  2. Install missing dependencies: pip install -r requirements.txt")
        print("  3. See README.md for detailed setup instructions")

    print()
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
