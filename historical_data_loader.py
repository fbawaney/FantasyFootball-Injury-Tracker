"""
Historical Data Loader
Imports past injury data to build the historical database for ML training
"""
import json
import requests
from typing import Dict, List
from datetime import datetime, timedelta
from injury_database import InjuryDatabase


class HistoricalDataLoader:
    """Loads historical injury data from various sources"""

    def __init__(self, db: InjuryDatabase):
        """
        Initialize the historical data loader

        Args:
            db: InjuryDatabase instance
        """
        self.db = db
        self.sleeper_url = "https://api.sleeper.app/v1/players/nfl"

    def import_from_json_file(self, file_path: str) -> int:
        """
        Import injury data from a JSON file (like injury_data.json)

        Args:
            file_path: Path to JSON file

        Returns:
            Number of records imported
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            injuries = data.get('injuries', [])
            imported_count = 0

            for injury in injuries:
                try:
                    # Add to database
                    injury_id = self.db.add_injury_record(injury)

                    # If injury has an end date or is resolved, mark it
                    if injury.get('injury_end_date'):
                        self.db.mark_injury_resolved(injury_id, injury['injury_end_date'])

                    # Update player summary
                    self.db.update_player_summary(injury.get('name'))

                    imported_count += 1
                except Exception as e:
                    print(f"Error importing injury for {injury.get('name')}: {e}")
                    continue

            print(f"Imported {imported_count} injury records from {file_path}")
            return imported_count

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return 0

    def load_current_sleeper_data(self) -> int:
        """
        Load current injury data from Sleeper API

        Returns:
            Number of records loaded
        """
        try:
            print("Fetching current injury data from Sleeper API...")
            response = requests.get(self.sleeper_url, timeout=30)
            response.raise_for_status()

            players = response.json()
            loaded_count = 0

            for player_id, player_data in players.items():
                injury_status = player_data.get('injury_status')

                if injury_status and injury_status in ['Out', 'Doubtful', 'Questionable', 'IR', 'PUP', 'Suspended']:
                    injury_record = {
                        'name': f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                        'position': player_data.get('position'),
                        'team': player_data.get('team'),
                        'injury_status': injury_status,
                        'injury_body_part': player_data.get('injury_body_part'),
                        'injury_notes': player_data.get('injury_notes'),
                        'injury_start_date': player_data.get('injury_start_date'),
                        'source': 'Sleeper API'
                    }

                    try:
                        # Check if this player already has an active injury in the database
                        existing = self._find_active_injury(injury_record['name'])

                        if existing:
                            # Update existing record if status changed
                            if existing['injury_status'] != injury_status:
                                self.db.update_injury_status(
                                    existing['id'],
                                    injury_status,
                                    existing['injury_status']
                                )
                        else:
                            # Add new injury record
                            self.db.add_injury_record(injury_record)

                        # Update player summary
                        self.db.update_player_summary(injury_record['name'])
                        loaded_count += 1

                    except Exception as e:
                        print(f"Error loading injury for {injury_record['name']}: {e}")
                        continue

            print(f"Loaded {loaded_count} current injuries from Sleeper")
            return loaded_count

        except Exception as e:
            print(f"Error fetching Sleeper data: {e}")
            return 0

    def _find_active_injury(self, player_name: str) -> Dict:
        """
        Find if player has an active (unresolved) injury

        Args:
            player_name: Player's full name

        Returns:
            Active injury record or None
        """
        history = self.db.get_player_injury_history(player_name)

        # Find most recent injury without an end date
        for injury in history:
            if not injury.get('injury_end_date'):
                return injury

        return None

    def simulate_historical_data(self, weeks_back: int = 52) -> int:
        """
        Generate simulated historical data for ML training
        Uses current injuries and projects them back in time with random variations

        Args:
            weeks_back: Number of weeks of historical data to simulate

        Returns:
            Number of simulated records created
        """
        print(f"Generating {weeks_back} weeks of simulated historical data...")
        print("Note: This uses current injury patterns with variations for ML training")

        simulated_count = 0

        # Common injury patterns by position and body part
        injury_patterns = {
            'QB': {'Shoulder': 14, 'Knee': 21, 'Ankle': 10, 'Ribs': 7},
            'RB': {'Hamstring': 14, 'Ankle': 10, 'Knee': 28, 'Shoulder': 14},
            'WR': {'Hamstring': 14, 'Ankle': 10, 'Knee': 21, 'Shoulder': 7},
            'TE': {'Knee': 21, 'Ankle': 14, 'Hamstring': 10, 'Shoulder': 14},
        }

        injury_statuses = ['Out', 'Doubtful', 'Questionable', 'IR']

        import random

        # Get some sample player names from recent data
        try:
            response = requests.get(self.sleeper_url, timeout=30)
            players = response.json()

            # Sample 100 players
            sample_players = []
            for player_id, player_data in list(players.items())[:100]:
                if player_data.get('position') in ['QB', 'RB', 'WR', 'TE']:
                    sample_players.append({
                        'name': f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                        'position': player_data.get('position'),
                        'team': player_data.get('team')
                    })

            # Generate historical injuries
            for week_offset in range(weeks_back):
                # Random number of injuries per week (2-8)
                num_injuries = random.randint(2, 8)

                for _ in range(num_injuries):
                    player = random.choice(sample_players)
                    position = player['position']

                    if position not in injury_patterns:
                        continue

                    # Pick a random body part weighted by common patterns
                    body_parts = list(injury_patterns[position].keys())
                    days = list(injury_patterns[position].values())
                    body_part = random.choice(body_parts)
                    base_days = injury_patterns[position][body_part]

                    # Random variation in recovery time
                    actual_days = max(1, int(base_days + random.gauss(0, 5)))

                    injury_status = random.choice(injury_statuses)

                    # Calculate dates
                    start_date = datetime.now() - timedelta(weeks=week_offset)
                    end_date = start_date + timedelta(days=actual_days)

                    injury_record = {
                        'name': player['name'],
                        'position': position,
                        'team': player['team'],
                        'injury_status': injury_status,
                        'injury_body_part': body_part,
                        'injury_notes': f'Simulated {body_part} injury',
                        'injury_start_date': start_date.isoformat(),
                        'source': 'Simulated Data'
                    }

                    try:
                        injury_id = self.db.add_injury_record(injury_record)
                        self.db.mark_injury_resolved(injury_id, end_date.isoformat())
                        self.db.update_player_summary(player['name'])
                        simulated_count += 1
                    except Exception as e:
                        print(f"Error creating simulated injury: {e}")
                        continue

            print(f"Generated {simulated_count} simulated injury records")
            return simulated_count

        except Exception as e:
            print(f"Error generating simulated data: {e}")
            return 0

    def sync_with_current_data(self, injury_data_file: str = 'injury_data.json'):
        """
        Sync database with current injury_data.json file

        Args:
            injury_data_file: Path to current injury data JSON
        """
        print("\n" + "="*60)
        print("SYNCING HISTORICAL DATABASE")
        print("="*60)

        # Load current Sleeper data
        current_count = self.load_current_sleeper_data()

        # Import from existing injury_data.json if it exists
        import os
        if os.path.exists(injury_data_file):
            print(f"\nImporting from {injury_data_file}...")
            file_count = self.import_from_json_file(injury_data_file)
        else:
            print(f"\n{injury_data_file} not found, skipping import")
            file_count = 0

        print("\n" + "="*60)
        print("SYNC COMPLETE")
        print(f"  Current injuries loaded: {current_count}")
        print(f"  Historical records imported: {file_count}")
        print("="*60)

    def initialize_database(self, include_simulated: bool = True):
        """
        Initialize the database with historical data

        Args:
            include_simulated: Whether to include simulated data for ML training
        """
        print("\n" + "="*60)
        print("INITIALIZING INJURY HISTORY DATABASE")
        print("="*60 + "\n")

        # Sync with current data
        self.sync_with_current_data()

        # Add simulated data if requested
        if include_simulated:
            print("\nAdding simulated historical data for ML training...")
            sim_count = self.simulate_historical_data(weeks_back=52)

        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)

        # Show some statistics
        trends = self.db.get_injury_trends(days=30)
        print(f"\nInjury trends (last 30 days):")
        print(f"  Total injuries: {trends['total_injuries']}")
        if trends.get('body_part_trends'):
            print(f"  Most common injury types:")
            for trend in trends['body_part_trends'][:5]:
                if trend.get('injury_body_part'):
                    print(f"    - {trend['injury_body_part']}: {trend['count']}")


def main():
    """Main entry point for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Load historical injury data')
    parser.add_argument('--init', action='store_true', help='Initialize database with all data')
    parser.add_argument('--sync', action='store_true', help='Sync with current data only')
    parser.add_argument('--file', type=str, help='Import from specific JSON file')
    parser.add_argument('--no-simulate', action='store_true', help='Skip simulated data')

    args = parser.parse_args()

    # Create database connection
    with InjuryDatabase() as db:
        loader = HistoricalDataLoader(db)

        if args.init:
            # Full initialization
            loader.initialize_database(include_simulated=not args.no_simulate)
        elif args.sync:
            # Sync current data only
            loader.sync_with_current_data()
        elif args.file:
            # Import specific file
            loader.import_from_json_file(args.file)
        else:
            print("Please specify --init, --sync, or --file")
            print("Use --help for more information")


if __name__ == "__main__":
    main()
