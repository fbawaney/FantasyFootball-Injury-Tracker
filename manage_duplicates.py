#!/usr/bin/env python3
"""
Database Duplicate Management Tool

Checks for and optionally cleans duplicate injury records.
Duplicates are defined as: same player + body part + status

Usage:
    python manage_duplicates.py --check    # Check only (no changes)
    python manage_duplicates.py --clean    # Clean duplicates
"""
from injury_database import InjuryDatabase
import argparse


def check_duplicates(db):
    """Check for duplicate injury records without making changes"""
    cursor = db.cursor

    cursor.execute("""
        SELECT player_name, injury_body_part, injury_status, COUNT(*) as count
        FROM injuries
        GROUP BY player_name, injury_body_part, injury_status
        HAVING count > 1
        ORDER BY count DESC
    """)

    duplicates = cursor.fetchall()

    if not duplicates:
        print("✅ No duplicate injury records found!")
        return 0

    print(f"Found {len(duplicates)} injury combinations with duplicates:\n")

    for dup in duplicates:
        player_name = dup[0] if isinstance(dup, tuple) else dup['player_name']
        body_part = dup[1] if isinstance(dup, tuple) else dup['injury_body_part']
        status = dup[2] if isinstance(dup, tuple) else dup['injury_status']
        count = dup[3] if isinstance(dup, tuple) else dup['count']

        print(f"  - {player_name}: {body_part} ({status}) - {count} records")

    return len(duplicates)


def clean_duplicates(db):
    """Clean all duplicate injury records (keeps most recent)"""
    cursor = db.cursor

    # Find all duplicate groups
    cursor.execute("""
        SELECT player_name, injury_body_part, injury_status, COUNT(*) as count
        FROM injuries
        GROUP BY player_name, injury_body_part, injury_status
        HAVING count > 1
        ORDER BY count DESC
    """)

    duplicates = cursor.fetchall()

    if not duplicates:
        print("✅ No duplicate injury records found!")
        return 0

    print(f"Found {len(duplicates)} injury combinations with duplicates\n")
    total_deleted = 0

    for dup in duplicates:
        player_name = dup[0] if isinstance(dup, tuple) else dup['player_name']
        body_part = dup[1] if isinstance(dup, tuple) else dup['injury_body_part']
        status = dup[2] if isinstance(dup, tuple) else dup['injury_status']

        # Get all records for this combination, ordered by ID (most recent first)
        cursor.execute("""
            SELECT id FROM injuries
            WHERE player_name = ?
              AND injury_body_part = ?
              AND injury_status = ?
            ORDER BY id DESC
        """, (player_name, body_part, status))

        injury_ids = cursor.fetchall()

        if len(injury_ids) > 1:
            # Keep the first (most recent), delete the rest
            keep_id = injury_ids[0][0] if isinstance(injury_ids[0], tuple) else injury_ids[0]['id']

            print(f"Cleaning {player_name} - {body_part} ({status}):")
            print(f"  Keeping injury ID {keep_id} (most recent)")

            for injury_id_row in injury_ids[1:]:
                old_id = injury_id_row[0] if isinstance(injury_id_row, tuple) else injury_id_row['id']
                cursor.execute("DELETE FROM injuries WHERE id = ?", (old_id,))
                total_deleted += 1

            print(f"  ✓ Deleted {len(injury_ids) - 1} duplicate(s)")

    # Delete any orphaned status change records
    cursor.execute("""
        DELETE FROM status_changes
        WHERE injury_id NOT IN (SELECT id FROM injuries)
    """)

    # Commit all changes
    db.conn.commit()

    print(f"\n{'='*80}")
    print(f"✅ Deleted {total_deleted} duplicate injury records")
    print(f"{'='*80}\n")

    # Rebuild player summaries
    if total_deleted > 0:
        print("Rebuilding player summaries...")
        cursor.execute("SELECT DISTINCT player_name FROM injuries")
        players = cursor.fetchall()

        for player in players:
            player_name = player[0] if isinstance(player, tuple) else player['player_name']
            db.update_player_summary(player_name)

        db.conn.commit()
        print(f"✅ Rebuilt summaries for {len(players)} players\n")

    # Show stats after cleanup
    cursor.execute("SELECT COUNT(*) FROM injuries")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM injuries WHERE injury_end_date IS NULL")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT player_name) FROM injuries")
    unique = cursor.fetchone()[0]

    print(f"After cleanup:")
    print(f"  Total records: {total}")
    print(f"  Active injuries: {active}")
    print(f"  Unique players: {unique}")
    if unique > 0:
        print(f"  Avg per player: {total / unique:.1f}\n")

    return total_deleted


def main():
    parser = argparse.ArgumentParser(
        description='Check for and clean duplicate injury records'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for duplicates without cleaning'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean duplicate records (keeps most recent)'
    )

    args = parser.parse_args()

    # Default to check if no args provided
    if not args.check and not args.clean:
        args.check = True

    print("\n" + "="*80)
    if args.clean:
        print("DATABASE DUPLICATE CLEANER")
    else:
        print("DATABASE DUPLICATE CHECKER")
    print("="*80 + "\n")

    with InjuryDatabase() as db:
        if args.clean:
            clean_duplicates(db)
        else:
            count = check_duplicates(db)
            if count > 0:
                print(f"\nTo clean these duplicates, run:")
                print(f"  python manage_duplicates.py --clean\n")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
