#!/usr/bin/env python3
"""
Quick script to check the injury database status
"""
from injury_database import InjuryDatabase
from historical_data_loader import HistoricalDataLoader

def main():
    print("\n" + "="*80)
    print("INJURY DATABASE STATUS CHECK")
    print("="*80 + "\n")

    with InjuryDatabase() as db:
        # Get total injury count
        cursor = db.cursor
        cursor.execute("SELECT COUNT(*) FROM injuries")
        total_injuries = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT player_name) FROM injuries")
        unique_players = cursor.fetchone()[0]

        print(f"📊 Database Statistics:")
        print(f"   Total injury records: {total_injuries}")
        print(f"   Unique players tracked: {unique_players}")

        # Get some sample data
        cursor.execute("""
            SELECT player_name, COUNT(*) as injury_count
            FROM injuries
            GROUP BY player_name
            ORDER BY injury_count DESC
            LIMIT 10
        """)
        top_injured = cursor.fetchall()

        if top_injured:
            print(f"\n🏥 Most Injured Players (in database):")
            for row in top_injured:
                player_name = row[0] if isinstance(row, tuple) else row['player_name']
                injury_count = row[1] if isinstance(row, tuple) else row['injury_count']
                print(f"   - {player_name}: {injury_count} injuries")

        # Check for recurring injuries
        cursor.execute("""
            SELECT player_name, injury_body_part, COUNT(*) as count
            FROM injuries
            WHERE injury_body_part IS NOT NULL
            GROUP BY player_name, injury_body_part
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        recurring = cursor.fetchall()

        if recurring:
            print(f"\n🔄 Top Recurring Injuries:")
            for row in recurring:
                player = row[0] if isinstance(row, tuple) else row['player_name']
                body_part = row[1] if isinstance(row, tuple) else row['injury_body_part']
                count = row[2] if isinstance(row, tuple) else row['count']
                print(f"   - {player}: {body_part} ({count}x)")

        print("\n" + "="*80)

        # Offer to load more data
        if total_injuries == 0:
            print("\n⚠️  Database is empty!")
            print("\nTo populate with historical data, run:")
            print("   python historical_data_loader.py --init")
            print("\nThis will:")
            print("   1. Load current injuries from Sleeper API")
            print("   2. Import existing injury_data.json if present")
            print("   3. Optionally add simulated historical data")
        else:
            print(f"\n✅ Database has {total_injuries} injury records")
            print("\nManage data:")
            print("   python manage_duplicates.py --check      (check for duplicates)")
            print("   python historical_data_loader.py --sync  (sync current injuries)")
            print("   python historical_data_loader.py --init  (full reload)")

        print("="*80 + "\n")

if __name__ == "__main__":
    main()
