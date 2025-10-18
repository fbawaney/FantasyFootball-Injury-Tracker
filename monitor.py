"""
Fantasy Football Injury Monitor
Main script to monitor injuries and send alerts
"""
import os
import json
import time
import schedule
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from yahoo_client import YahooFantasyClient
from injury_tracker import InjuryTracker
from notifier import Notifier
from depth_chart import DepthChartManager

load_dotenv()


class InjuryMonitor:
    """Monitors fantasy league players for injury updates"""

    def __init__(self, use_depth_charts: bool = True):
        """
        Initialize the injury monitor

        Args:
            use_depth_charts: Whether to fetch and use depth chart data for backup info
        """
        self.yahoo_client = YahooFantasyClient()

        # Initialize depth chart manager if enabled
        self.depth_chart_manager = None
        if use_depth_charts:
            self.depth_chart_manager = DepthChartManager()

        self.injury_tracker = InjuryTracker(depth_chart_manager=self.depth_chart_manager)
        self.notifier = Notifier()

        self.data_file = 'injury_data.json'
        self.previous_injuries = self._load_previous_injuries()

        self.check_interval = int(os.getenv('CHECK_INTERVAL', '30'))  # minutes
        self.alert_window_hours = int(os.getenv('ALERT_WINDOW_HOURS', '24'))  # hours
        self.use_depth_charts = use_depth_charts

    def _load_previous_injuries(self) -> List[Dict]:
        """
        Load previously tracked injuries from file

        Returns:
            List of previous injury records
        """
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    return data.get('injuries', [])
            except Exception as e:
                print(f"Error loading previous injuries: {e}")
                return []
        return []

    def _save_injuries(self, injuries: List[Dict]):
        """
        Save current injuries to file

        Args:
            injuries: List of injury records to save
        """
        try:
            # Convert bytes to strings in the data
            def convert_bytes(obj):
                if isinstance(obj, bytes):
                    return obj.decode('utf-8')
                elif isinstance(obj, dict):
                    return {k: convert_bytes(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_bytes(item) for item in obj]
                return obj

            cleaned_injuries = convert_bytes(injuries)

            data = {
                'last_updated': datetime.now().isoformat(),
                'injuries': cleaned_injuries
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving injuries: {e}")

    def check_injuries(self):
        """
        Check for injury updates and send alerts if needed
        """
        print(f"\n{'='*80}")
        print(f"Starting injury check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        try:
            # Step 1: Get all relevant players from Yahoo
            print("Step 1: Fetching players from Yahoo Fantasy League...")
            yahoo_players = self.yahoo_client.get_all_relevant_players()
            print(f"  ✓ Found {len(yahoo_players)} players to monitor")

            # Step 2: Fetch depth charts if enabled (once per session)
            if self.use_depth_charts and self.depth_chart_manager:
                if not self.depth_chart_manager.depth_charts:
                    print("\nStep 2: Fetching NFL depth charts (this may take ~10 seconds)...")
                    self.depth_chart_manager.fetch_all_depth_charts()
                    print(f"  ✓ Depth charts cached")
                else:
                    print("\nStep 2: Using cached depth charts")

            # Step 3: Get current injury data
            print("\nStep 3: Fetching injury data from external sources...")
            current_injuries = self.injury_tracker.get_injury_updates(yahoo_players)
            print(f"  ✓ Found {len(current_injuries)} players with injuries")
            if self.use_depth_charts:
                print(f"  ✓ Backup player info included")

            # Step 4: Compare with previous data to find new/updated injuries
            print("\nStep 4: Comparing with previous injury data...")
            print(f"  Alert window: {self.alert_window_hours} hours")
            new_injuries = self.injury_tracker.get_new_injuries(
                current_injuries,
                self.previous_injuries,
                alert_window_hours=self.alert_window_hours
            )

            if new_injuries:
                print(f"  ⚠️  {len(new_injuries)} new or updated injuries detected!")
                # Send alerts for new injuries
                self.notifier.send_alert(new_injuries)
            else:
                print("  ✓ No new injuries detected")

            # Step 5: Save current injuries for next check
            print("\nStep 5: Saving current injury data...")
            self._save_injuries(current_injuries)
            self.previous_injuries = current_injuries
            print("  ✓ Data saved successfully")

            # Step 6: Save injury news to markdown
            if current_injuries:
                print("\nStep 6: Generating injury news markdown report...")
                self.injury_tracker.save_injury_news_to_markdown(current_injuries)
                print("  ✓ Injury news report saved to injury_news.md")

            # Step 7: Display summary
            if current_injuries:
                print("\nStep 7: Generating summary report...")
                summary = self.notifier.format_summary_report(current_injuries)
                print(summary)

            print(f"\n{'='*80}")
            print(f"Check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next check in {self.check_interval} minutes")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"❌ Error during injury check: {e}")
            import traceback
            traceback.print_exc()

    def run_once(self):
        """Run a single injury check"""
        self.check_injuries()

    def run_continuous(self):
        """Run continuous monitoring with scheduled checks"""
        print("=" * 80)
        print("🏈 FANTASY FOOTBALL INJURY MONITOR")
        print("=" * 80)
        print(f"Monitoring league: {self.yahoo_client.league_id}")
        print(f"Check interval: {self.check_interval} minutes")
        print(f"Alert window: {self.alert_window_hours} hours")
        print(f"Notification method: {self.notifier.method}")
        print(f"Depth chart tracking: {'Enabled' if self.use_depth_charts else 'Disabled'}")
        print("=" * 80)
        print("\nPress Ctrl+C to stop monitoring\n")

        # Run immediately on startup
        self.check_injuries()

        # Schedule periodic checks
        schedule.every(self.check_interval).minutes.do(self.check_injuries)

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
        except KeyboardInterrupt:
            print("\n\n" + "=" * 80)
            print("Monitoring stopped by user")
            print("=" * 80)

    def show_current_injuries(self):
        """Display current injury report without checking for updates"""
        print("\n📊 Loading current injury data...\n")

        try:
            # Get all relevant players from Yahoo
            yahoo_players = self.yahoo_client.get_all_relevant_players()

            # Get current injury data
            current_injuries = self.injury_tracker.get_injury_updates(yahoo_players)

            if current_injuries:
                # Save to markdown
                self.injury_tracker.save_injury_news_to_markdown(current_injuries)
                print("✓ Injury news report saved to injury_news.md\n")

                # Display summary
                summary = self.notifier.format_summary_report(current_injuries)
                print(summary)
            else:
                print("No injuries currently reported for monitored players.")

        except Exception as e:
            print(f"❌ Error loading injury data: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fantasy Football Injury Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python monitor.py                    # Run continuous monitoring
  python monitor.py --once             # Run single check
  python monitor.py --report           # Show current injury report
  python monitor.py --test             # Test notification system
        '''
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run a single injury check and exit'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Show current injury report without checking for updates'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the notification system'
    )

    args = parser.parse_args()

    try:
        if args.test:
            # Test notification system
            print("Testing notification system...\n")
            notifier = Notifier()
            test_injuries = [
                {
                    'name': 'Test Player',
                    'position': 'RB',
                    'team': 'TST',
                    'injury_status': 'Questionable',
                    'injury_body_part': 'Ankle',
                    'owned_by_team': 'Test Team',
                    'owned_by_manager': 'Test Manager',
                    'alert_type': 'NEW_INJURY',
                    'source': 'Test'
                }
            ]
            notifier.send_alert(test_injuries)
            print("\n✓ Test notification sent!")

        elif args.report:
            # Show current injury report
            monitor = InjuryMonitor()
            monitor.show_current_injuries()

        elif args.once:
            # Run single check
            monitor = InjuryMonitor()
            monitor.run_once()

        else:
            # Run continuous monitoring
            monitor = InjuryMonitor()
            monitor.run_continuous()

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
