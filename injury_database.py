"""
Injury Database Module
Manages SQLite database for historical injury tracking and analysis
"""
import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path


class InjuryDatabase:
    """Manages historical injury data storage and retrieval"""

    def __init__(self, db_path: str = "injury_history.db"):
        """
        Initialize injury database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create database tables if they don't exist"""

        # Main injury records table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS injuries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                position TEXT,
                team TEXT,
                injury_status TEXT,
                injury_body_part TEXT,
                injury_notes TEXT,
                injury_start_date TEXT,
                injury_end_date TEXT,
                days_missed INTEGER,
                season INTEGER,
                week INTEGER,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Injury status changes tracking table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                injury_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                change_date TEXT NOT NULL,
                FOREIGN KEY (injury_id) REFERENCES injuries (id)
            )
        ''')

        # Player injury history summary table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_summary (
                player_name TEXT PRIMARY KEY,
                total_injuries INTEGER DEFAULT 0,
                total_days_missed INTEGER DEFAULT 0,
                recurring_body_parts TEXT,
                last_injury_date TEXT,
                injury_prone_score REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL
            )
        ''')

        # Create indexes for faster queries
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_name
            ON injuries(player_name)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_injury_dates
            ON injuries(injury_start_date, injury_end_date)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_body_part
            ON injuries(injury_body_part)
        ''')

        self.conn.commit()

    def add_injury_record(self, injury_data: Dict) -> int:
        """
        Add a new injury record to the database

        Args:
            injury_data: Dictionary containing injury information

        Returns:
            ID of the inserted record
        """
        now = datetime.now().isoformat()

        self.cursor.execute('''
            INSERT INTO injuries (
                player_name, position, team, injury_status,
                injury_body_part, injury_notes, injury_start_date,
                season, week, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            injury_data.get('name'),
            injury_data.get('position'),
            injury_data.get('team'),
            injury_data.get('injury_status'),
            injury_data.get('injury_body_part'),
            injury_data.get('injury_notes'),
            injury_data.get('injury_start_date', now),
            self._get_current_season(),
            self._get_current_week(),
            injury_data.get('source', 'Unknown'),
            now,
            now
        ))

        self.conn.commit()
        return self.cursor.lastrowid

    def update_injury_status(self, injury_id: int, new_status: str,
                            old_status: Optional[str] = None):
        """
        Update injury status and track the change

        Args:
            injury_id: ID of the injury record
            new_status: New injury status
            old_status: Previous injury status (for tracking)
        """
        now = datetime.now().isoformat()

        # Update main record
        self.cursor.execute('''
            UPDATE injuries
            SET injury_status = ?, updated_at = ?
            WHERE id = ?
        ''', (new_status, now, injury_id))

        # Track status change
        if old_status:
            self.cursor.execute('''
                INSERT INTO status_changes (injury_id, old_status, new_status, change_date)
                VALUES (?, ?, ?, ?)
            ''', (injury_id, old_status, new_status, now))

        self.conn.commit()

    def mark_injury_resolved(self, injury_id: int, end_date: Optional[str] = None):
        """
        Mark an injury as resolved and calculate days missed

        Args:
            injury_id: ID of the injury record
            end_date: Date injury resolved (defaults to now)
        """
        if not end_date:
            end_date = datetime.now().isoformat()

        # Get start date to calculate days missed
        self.cursor.execute('SELECT injury_start_date FROM injuries WHERE id = ?', (injury_id,))
        row = self.cursor.fetchone()

        if row and row['injury_start_date']:
            start = datetime.fromisoformat(row['injury_start_date'])
            end = datetime.fromisoformat(end_date)
            days_missed = (end - start).days

            self.cursor.execute('''
                UPDATE injuries
                SET injury_end_date = ?, days_missed = ?, updated_at = ?
                WHERE id = ?
            ''', (end_date, days_missed, datetime.now().isoformat(), injury_id))

            self.conn.commit()

    def get_player_injury_history(self, player_name: str) -> List[Dict]:
        """
        Get complete injury history for a player

        Args:
            player_name: Player's full name

        Returns:
            List of injury records
        """
        self.cursor.execute('''
            SELECT * FROM injuries
            WHERE player_name = ?
            ORDER BY injury_start_date DESC
        ''', (player_name,))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_recurring_injuries(self, player_name: str) -> Dict[str, int]:
        """
        Get count of injuries by body part for a player

        Args:
            player_name: Player's full name

        Returns:
            Dictionary mapping body part to injury count
        """
        self.cursor.execute('''
            SELECT injury_body_part, COUNT(*) as count
            FROM injuries
            WHERE player_name = ? AND injury_body_part IS NOT NULL
            GROUP BY injury_body_part
            ORDER BY count DESC
        ''', (player_name,))

        return {row['injury_body_part']: row['count'] for row in self.cursor.fetchall()}

    def get_similar_injuries(self, injury_body_part: str, position: str,
                            limit: int = 10) -> List[Dict]:
        """
        Find similar injuries for prediction/comparison

        Args:
            injury_body_part: Body part injured
            position: Player position
            limit: Maximum number of records to return

        Returns:
            List of similar injury records with recovery data
        """
        self.cursor.execute('''
            SELECT * FROM injuries
            WHERE injury_body_part = ?
            AND position = ?
            AND days_missed IS NOT NULL
            ORDER BY injury_start_date DESC
            LIMIT ?
        ''', (injury_body_part, position, limit))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_average_recovery_time(self, injury_body_part: str,
                                  injury_status: str = None) -> Optional[float]:
        """
        Calculate average recovery time for an injury type

        Args:
            injury_body_part: Body part injured
            injury_status: Injury status (Out, IR, etc.)

        Returns:
            Average days missed, or None if no data
        """
        if injury_status:
            self.cursor.execute('''
                SELECT AVG(days_missed) as avg_days
                FROM injuries
                WHERE injury_body_part = ?
                AND injury_status = ?
                AND days_missed IS NOT NULL
            ''', (injury_body_part, injury_status))
        else:
            self.cursor.execute('''
                SELECT AVG(days_missed) as avg_days
                FROM injuries
                WHERE injury_body_part = ?
                AND days_missed IS NOT NULL
            ''', (injury_body_part,))

        row = self.cursor.fetchone()
        return row['avg_days'] if row and row['avg_days'] else None

    def update_player_summary(self, player_name: str):
        """
        Update summary statistics for a player

        Args:
            player_name: Player's full name
        """
        # Get injury statistics
        self.cursor.execute('''
            SELECT
                COUNT(*) as total_injuries,
                SUM(COALESCE(days_missed, 0)) as total_days_missed,
                MAX(injury_start_date) as last_injury_date
            FROM injuries
            WHERE player_name = ?
        ''', (player_name,))

        stats = self.cursor.fetchone()

        # Get recurring body parts
        recurring = self.get_recurring_injuries(player_name)
        recurring_json = json.dumps(recurring) if recurring else None

        # Calculate injury prone score (simple heuristic for now)
        # Score based on: number of injuries, days missed, and recurrence
        injury_prone_score = min(100, (
            stats['total_injuries'] * 10 +
            (stats['total_days_missed'] or 0) / 7 +
            len([v for v in recurring.values() if v > 1]) * 15
        ))

        now = datetime.now().isoformat()

        # Upsert player summary
        self.cursor.execute('''
            INSERT OR REPLACE INTO player_summary (
                player_name, total_injuries, total_days_missed,
                recurring_body_parts, last_injury_date,
                injury_prone_score, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_name,
            stats['total_injuries'],
            stats['total_days_missed'] or 0,
            recurring_json,
            stats['last_injury_date'],
            injury_prone_score,
            now
        ))

        self.conn.commit()

    def get_player_summary(self, player_name: str) -> Optional[Dict]:
        """
        Get injury summary for a player

        Args:
            player_name: Player's full name

        Returns:
            Summary statistics dictionary or None
        """
        self.cursor.execute('''
            SELECT * FROM player_summary WHERE player_name = ?
        ''', (player_name,))

        row = self.cursor.fetchone()
        if row:
            summary = dict(row)
            # Parse recurring body parts JSON
            if summary.get('recurring_body_parts'):
                summary['recurring_body_parts'] = json.loads(summary['recurring_body_parts'])
            return summary
        return None

    def get_injury_trends(self, days: int = 30) -> Dict:
        """
        Get injury trends over the last N days

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend statistics
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        self.cursor.execute('''
            SELECT
                COUNT(*) as total_injuries,
                COUNT(DISTINCT player_name) as unique_players,
                injury_body_part,
                COUNT(*) as count
            FROM injuries
            WHERE injury_start_date >= ?
            GROUP BY injury_body_part
            ORDER BY count DESC
        ''', (cutoff_date,))

        body_part_trends = [dict(row) for row in self.cursor.fetchall()]

        self.cursor.execute('''
            SELECT COUNT(*) as total_injuries
            FROM injuries
            WHERE injury_start_date >= ?
        ''', (cutoff_date,))

        total = self.cursor.fetchone()['total_injuries']

        return {
            'total_injuries': total,
            'body_part_trends': body_part_trends,
            'period_days': days
        }

    def _get_current_season(self) -> int:
        """Get current NFL season year"""
        now = datetime.now()
        # NFL season starts in September
        return now.year if now.month >= 9 else now.year - 1

    def _get_current_week(self) -> int:
        """Get current NFL week (simplified)"""
        now = datetime.now()
        season_start = datetime(self._get_current_season(), 9, 1)

        if now < season_start:
            return 0  # Preseason

        weeks_elapsed = (now - season_start).days // 7
        return min(weeks_elapsed + 1, 18)  # Regular season is 18 weeks

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
