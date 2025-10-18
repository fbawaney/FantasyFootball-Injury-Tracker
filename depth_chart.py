"""
Depth Chart Module
Fetches NFL depth charts to identify backup players for injured starters
"""
import requests
import json
from typing import Dict, List, Optional
import time


class DepthChartManager:
    """Manages NFL depth charts and identifies backup players"""

    def __init__(self):
        """Initialize depth chart manager"""
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        self.depth_charts = {}  # Cache depth charts

        # ESPN team ID mapping (team abbreviation -> ESPN ID)
        self.team_id_map = {
            'ARI': 22, 'ATL': 1, 'BAL': 33, 'BUF': 2, 'CAR': 29, 'CHI': 3,
            'CIN': 4, 'CLE': 5, 'DAL': 6, 'DEN': 7, 'DET': 8, 'GB': 9,
            'HOU': 34, 'IND': 11, 'JAX': 30, 'KC': 12, 'LAC': 24, 'LAR': 14,
            'LV': 13, 'MIA': 15, 'MIN': 16, 'NE': 17, 'NO': 18, 'NYG': 19,
            'NYJ': 20, 'PHI': 21, 'PIT': 23, 'SEA': 26, 'SF': 25, 'TB': 27,
            'TEN': 10, 'WAS': 28
        }

        # Position groups for fantasy relevance
        self.fantasy_positions = ['QB', 'RB', 'WR', 'TE']

    def fetch_team_depth_chart(self, team_abbr: str) -> Optional[Dict]:
        """
        Fetch depth chart for a specific team

        Args:
            team_abbr: Team abbreviation (e.g., 'SF', 'KC')

        Returns:
            Depth chart data or None if fetch fails
        """
        team_id = self.team_id_map.get(team_abbr.upper())
        if not team_id:
            print(f"Unknown team abbreviation: {team_abbr}")
            return None

        url = f"{self.espn_base_url}/{team_id}/depthcharts"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch depth chart for {team_abbr}: HTTP {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error fetching depth chart for {team_abbr}: {e}")
            return None

    def parse_depth_chart(self, depth_chart_data: Dict) -> Dict[str, List[Dict]]:
        """
        Parse ESPN depth chart response into organized structure

        Args:
            depth_chart_data: Raw ESPN depth chart response

        Returns:
            Dictionary mapping positions to list of players in depth order
        """
        parsed = {}

        if not depth_chart_data or 'depthchart' not in depth_chart_data:
            return parsed

        # depthchart is a list of formations (offense, defense, etc.)
        for formation in depth_chart_data['depthchart']:
            formation_name = formation.get('name', '')
            positions_dict = formation.get('positions', {})

            # Iterate through each position in this formation
            for pos_key, pos_data in positions_dict.items():
                position_obj = pos_data.get('position', {})
                # Get the parent abbreviation for fantasy positions (QB, RB, WR, TE)
                parent_abbr = None
                if 'parent' in position_obj:
                    parent_abbr = position_obj['parent'].get('abbreviation', '').upper()

                # Also check the position itself
                position_abbr = position_obj.get('abbreviation', '').upper()

                # Use parent if available (more generic), otherwise use specific position
                fantasy_position = parent_abbr if parent_abbr in self.fantasy_positions else position_abbr

                # Only track fantasy-relevant positions
                if fantasy_position not in self.fantasy_positions:
                    continue

                athletes = pos_data.get('athletes', [])

                for idx, athlete in enumerate(athletes):
                    player_info = {
                        'name': athlete.get('displayName', 'Unknown'),
                        'depth': idx + 1,  # 1 = starter, 2 = backup, etc.
                        'position': fantasy_position,
                        'espn_id': athlete.get('id'),
                        'jersey': athlete.get('jersey', '')
                    }

                    # Add to parsed dict
                    if fantasy_position not in parsed:
                        parsed[fantasy_position] = []
                    parsed[fantasy_position].append(player_info)

        return parsed

    def get_backup_for_player(self, player_name: str, team_abbr: str, position: str) -> Optional[Dict]:
        """
        Find the backup player for an injured player

        Args:
            player_name: Name of injured player
            team_abbr: Team abbreviation
            position: Player position

        Returns:
            Backup player info or None
        """
        # Fetch depth chart if not cached
        if team_abbr not in self.depth_charts:
            depth_chart_data = self.fetch_team_depth_chart(team_abbr)
            if depth_chart_data:
                self.depth_charts[team_abbr] = self.parse_depth_chart(depth_chart_data)
            else:
                return None

        depth_chart = self.depth_charts.get(team_abbr, {})
        position_players = depth_chart.get(position, [])

        # Find the injured player and return next in depth
        normalized_name = self.normalize_name(player_name)

        for idx, player in enumerate(position_players):
            if self.normalize_name(player['name']) == normalized_name:
                # Found the injured player, return next player if exists
                if idx + 1 < len(position_players):
                    backup = position_players[idx + 1].copy()
                    backup['backup_for'] = player_name
                    backup['team'] = team_abbr
                    return backup
                else:
                    # No backup listed
                    return None

        # Player not found in depth chart
        return None

    def get_all_backups_for_position(self, team_abbr: str, position: str) -> List[Dict]:
        """
        Get all backup players for a position on a team

        Args:
            team_abbr: Team abbreviation
            position: Position to get backups for

        Returns:
            List of backup players (depth > 1)
        """
        if team_abbr not in self.depth_charts:
            depth_chart_data = self.fetch_team_depth_chart(team_abbr)
            if depth_chart_data:
                self.depth_charts[team_abbr] = self.parse_depth_chart(depth_chart_data)

        depth_chart = self.depth_charts.get(team_abbr, {})
        position_players = depth_chart.get(position, [])

        # Return all players with depth > 1
        backups = [p for p in position_players if p['depth'] > 1]
        for backup in backups:
            backup['team'] = team_abbr

        return backups

    def fetch_all_depth_charts(self):
        """
        Fetch depth charts for all 32 NFL teams
        Uses rate limiting to be respectful
        """
        print("Fetching depth charts for all 32 NFL teams...")

        for team_abbr, team_id in self.team_id_map.items():
            if team_abbr not in self.depth_charts:
                print(f"  Fetching {team_abbr}...", end=' ')
                depth_chart_data = self.fetch_team_depth_chart(team_abbr)

                if depth_chart_data:
                    self.depth_charts[team_abbr] = self.parse_depth_chart(depth_chart_data)
                    print(f"✓ ({len(self.depth_charts[team_abbr])} positions)")
                else:
                    print("✗ Failed")

                time.sleep(0.2)  # Rate limiting

        print(f"Completed: {len(self.depth_charts)}/32 teams")

    def normalize_name(self, name: str) -> str:
        """
        Normalize player name for matching

        Args:
            name: Player name to normalize

        Returns:
            Normalized name (lowercase, no extra spaces, no suffixes)
        """
        # Remove common suffixes
        name = name.replace(' Jr.', '').replace(' Sr.', '').replace(' III', '').replace(' II', '')
        return ' '.join(name.lower().split())

    def find_player_in_all_depth_charts(self, player_name: str, position: str) -> Optional[Dict]:
        """
        Search all cached depth charts for a player

        Args:
            player_name: Name of player to find
            position: Player position

        Returns:
            Player info with team and depth, or None
        """
        normalized_name = self.normalize_name(player_name)

        for team_abbr, depth_chart in self.depth_charts.items():
            position_players = depth_chart.get(position, [])

            for player in position_players:
                if self.normalize_name(player['name']) == normalized_name:
                    player['team'] = team_abbr
                    return player

        return None

    def check_player_availability(self, backup_name: str, yahoo_players: List[Dict]) -> Dict:
        """
        Check if a backup player is owned or available in Yahoo league

        Args:
            backup_name: Name of backup player
            yahoo_players: List of all Yahoo league players

        Returns:
            Dictionary with availability info
        """
        normalized_backup = self.normalize_name(backup_name)

        for player in yahoo_players:
            normalized_player = self.normalize_name(player['name'])

            if normalized_player == normalized_backup:
                owned_by = player.get('owned_by_team', 'Free Agent')
                return {
                    'available': owned_by == 'Free Agent',
                    'owned_by_team': owned_by,
                    'owned_by_manager': player.get('owned_by_manager'),
                    'player_info': player
                }

        # Not found in Yahoo league at all (deep bench/practice squad)
        return {
            'available': True,
            'owned_by_team': 'Not in League',
            'owned_by_manager': None,
            'player_info': None
        }


if __name__ == "__main__":
    # Test the depth chart manager
    manager = DepthChartManager()

    # Test single team
    print("Testing depth chart fetch for San Francisco 49ers...")
    print("=" * 80)

    depth_chart_data = manager.fetch_team_depth_chart('SF')
    if depth_chart_data:
        parsed = manager.parse_depth_chart(depth_chart_data)

        print("\nSan Francisco 49ers Depth Chart:")
        for position, players in parsed.items():
            print(f"\n{position}:")
            for player in players:
                depth_indicator = "STARTER" if player['depth'] == 1 else f"BACKUP {player['depth']}"
                print(f"  {player['depth']}. {player['name']} ({depth_indicator})")

    # Test backup finding
    print("\n" + "=" * 80)
    print("Testing backup player lookup...")
    print("=" * 80)

    # Example: Find CMC's backup
    backup = manager.get_backup_for_player("Christian McCaffrey", "SF", "RB")
    if backup:
        print(f"\nBackup for Christian McCaffrey:")
        print(f"  Name: {backup['name']}")
        print(f"  Position: {backup['position']}")
        print(f"  Depth: {backup['depth']}")
    else:
        print("\nNo backup found or player not in depth chart")

    # Fetch all depth charts (optional - takes ~10 seconds)
    print("\n" + "=" * 80)
    print("Want to fetch all 32 team depth charts? (takes ~10 seconds)")
    print("=" * 80)
    response = input("Fetch all? (y/n): ")

    if response.lower() == 'y':
        manager.fetch_all_depth_charts()

        print("\n" + "=" * 80)
        print("Sample: All RB depth charts")
        print("=" * 80)

        for team_abbr in sorted(manager.depth_charts.keys())[:5]:  # Show first 5 teams
            depth_chart = manager.depth_charts[team_abbr]
            if 'RB' in depth_chart:
                print(f"\n{team_abbr} RBs:")
                for player in depth_chart['RB']:
                    print(f"  {player['depth']}. {player['name']}")
