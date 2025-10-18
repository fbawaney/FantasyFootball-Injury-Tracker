"""
Yahoo Fantasy Sports API Client
Handles authentication and data retrieval from Yahoo Fantasy Football
"""
import os
import json
from typing import Dict, List, Optional
from yfpy.query import YahooFantasySportsQuery
from dotenv import load_dotenv

load_dotenv()


class YahooFantasyClient:
    """Client for interacting with Yahoo Fantasy Sports API"""

    def __init__(self):
        """Initialize Yahoo Fantasy client with OAuth credentials"""
        self.client_id = os.getenv('YAHOO_CLIENT_ID')
        self.client_secret = os.getenv('YAHOO_CLIENT_SECRET')
        self.league_id = os.getenv('YAHOO_LEAGUE_ID')
        self.game_key = os.getenv('YAHOO_GAME_KEY', 'nfl')

        if not all([self.client_id, self.client_secret, self.league_id]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, and YAHOO_LEAGUE_ID"
            )

        # Initialize YFPY query object
        self.query = YahooFantasySportsQuery(
            auth_dir=os.getcwd(),
            league_id=self.league_id,
            game_code=self.game_key,
            consumer_key=self.client_id,
            consumer_secret=self.client_secret
        )

    def get_league_teams(self) -> List[Dict]:
        """
        Get all teams in the league

        Returns:
            List of team dictionaries with owner and roster information
        """
        try:
            teams = self.query.get_league_teams()
            team_list = []

            for team in teams:
                team_data = {
                    'team_id': team.team_id,
                    'team_key': team.team_key,
                    'name': team.name,
                    'manager': team.managers[0].nickname if team.managers else 'Unknown'
                }
                team_list.append(team_data)

            return team_list
        except Exception as e:
            print(f"Error fetching league teams: {e}")
            return []

    def get_team_roster(self, team_key: str) -> List[Dict]:
        """
        Get roster for a specific team

        Args:
            team_key: Yahoo team key (full key like "461.l.880035.t.1")

        Returns:
            List of player dictionaries
        """
        try:
            # Extract just the team_id from the team_key
            # team_key format: "461.l.880035.t.1" -> we need just "1"
            team_id = team_key.split('.t.')[-1]

            # get_team_roster_by_week returns a Roster object
            roster_obj = self.query.get_team_roster_by_week(team_id, chosen_week='current')
            players = []

            # The Roster object has a players attribute which is a list of Player objects
            if hasattr(roster_obj, 'players') and roster_obj.players:
                for player in roster_obj.players:
                    player_data = {
                        'player_id': player.player_id if hasattr(player, 'player_id') else None,
                        'player_key': player.player_key if hasattr(player, 'player_key') else None,
                        'name': player.name.full if hasattr(player, 'name') else 'Unknown',
                        'position': player.primary_position if hasattr(player, 'primary_position') else 'Unknown',
                        'team': player.editorial_team_abbr if hasattr(player, 'editorial_team_abbr') else 'Unknown',
                        'status': player.status if hasattr(player, 'status') else None,
                        'injury_note': player.injury_note if hasattr(player, 'injury_note') else None
                    }
                    players.append(player_data)

            return players
        except Exception as e:
            print(f"Error fetching team roster for {team_key}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_league_players(self) -> List[Dict]:
        """
        Get all players owned by teams in the league

        Returns:
            List of all owned players with team ownership info
        """
        teams = self.get_league_teams()
        all_players = []

        for team in teams:
            roster = self.get_team_roster(team['team_key'])
            for player in roster:
                player['owned_by_team'] = team['name']
                player['owned_by_manager'] = team['manager']
                all_players.append(player)

        return all_players

    def get_free_agents(self, position: Optional[str] = None, count: int = 50) -> List[Dict]:
        """
        Get available free agents

        Args:
            position: Filter by position (QB, RB, WR, TE, K, DEF)
            count: Number of free agents to retrieve

        Returns:
            List of free agent player dictionaries
        """
        try:
            # get_league_players signature: (player_count_limit=None, player_count_start=0)
            # Returns List[Player] - all players, need to filter for free agents manually
            all_players = self.query.get_league_players(
                player_count_limit=count * 3,  # Get extra to account for filtering
                player_count_start=0
            )

            players = []
            for player in all_players:
                if len(players) >= count:
                    break

                # Filter by position if specified
                if position and hasattr(player, 'primary_position') and player.primary_position != position:
                    continue

                # Check if player is available (not owned)
                # If they have ownership data and it's not empty, skip them
                if hasattr(player, 'ownership') and player.ownership:
                    continue

                player_data = {
                    'player_id': player.player_id if hasattr(player, 'player_id') else None,
                    'player_key': player.player_key if hasattr(player, 'player_key') else None,
                    'name': player.name.full if hasattr(player, 'name') else 'Unknown',
                    'position': player.primary_position if hasattr(player, 'primary_position') else 'Unknown',
                    'team': player.editorial_team_abbr if hasattr(player, 'editorial_team_abbr') else 'Unknown',
                    'status': player.status if hasattr(player, 'status') else None,
                    'injury_note': player.injury_note if hasattr(player, 'injury_note') else None,
                    'owned_by_team': 'Free Agent',
                    'owned_by_manager': None
                }
                players.append(player_data)

            return players
        except Exception as e:
            print(f"Error fetching free agents: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_relevant_players(self) -> List[Dict]:
        """
        Get all players relevant to the league (owned + top free agents)

        Returns:
            Combined list of owned players and top free agents
        """
        owned_players = self.get_all_league_players()
        free_agents = self.get_free_agents(count=100)  # Top 100 free agents

        return owned_players + free_agents


if __name__ == "__main__":
    # Test the client
    try:
        client = YahooFantasyClient()
        print("Yahoo Fantasy Client initialized successfully!")
        print(f"League ID: {client.league_id}")

        teams = client.get_league_teams()
        print(f"\nFound {len(teams)} teams in league:")
        for team in teams:
            print(f"  - {team['name']} (Manager: {team['manager']})")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your Yahoo API credentials")
        print("3. Run 'pip install -r requirements.txt'")
