"""
Injury Tracker Module
Fetches injury data from multiple sources including Sleeper API and ESPN
Includes depth chart integration to identify backup players
Includes rule-based injury risk assessment
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import time
import feedparser
from textblob import TextBlob
from risk_scorer import InjuryRiskScorer
from injury_database import InjuryDatabase
from news_analyzer import NewsAnalyzer


class InjuryTracker:
    """Tracks NFL player injuries from multiple sources with risk assessment"""

    def __init__(self, depth_chart_manager=None):
        """
        Initialize injury tracker with API endpoints

        Args:
            depth_chart_manager: Optional DepthChartManager instance for backup lookups
        """
        self.sleeper_players_url = "https://api.sleeper.app/v1/players/nfl"
        self.espn_injuries_base = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
        self.rss_feeds = [
            "https://sports.yahoo.com/nfl/rss.xml",
            "https://www.rotoworld.com/rss/feed.aspx?sport=nfl&ftype=news"
        ]
        self.player_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 3600  # Cache for 1 hour
        self.depth_chart_manager = depth_chart_manager
        self.news_cache = {}  # Cache for RSS news by player name

        # Initialize injury database for historical tracking
        try:
            self.db = InjuryDatabase()
            self.risk_scorer = InjuryRiskScorer(db=self.db)
            print("Rule-based injury risk assessment enabled with historical data")
        except Exception as e:
            print(f"Warning: Could not initialize injury database: {e}")
            print("Risk assessment will use session-only tracking")
            self.db = None
            self.risk_scorer = InjuryRiskScorer()

        # Initialize news analyzer for timeline extraction
        self.news_analyzer = NewsAnalyzer()
        print("News-based timeline extraction enabled")

    def fetch_sleeper_players(self) -> Dict:
        """
        Fetch all NFL players from Sleeper API including injury status

        Returns:
            Dictionary of player data keyed by player_id
        """
        try:
            print("Fetching player data from Sleeper API...")
            response = requests.get(self.sleeper_players_url, timeout=30)
            response.raise_for_status()

            players = response.json()
            print(f"Successfully fetched {len(players)} players from Sleeper")
            return players

        except requests.RequestException as e:
            print(f"Error fetching Sleeper data: {e}")
            return {}

    def get_injured_players_from_sleeper(self) -> List[Dict]:
        """
        Get all currently injured NFL players from Sleeper API

        Returns:
            List of injured players with their injury details
        """
        players = self.fetch_sleeper_players()
        injured_players = []

        for player_id, player_data in players.items():
            # Check if player has an injury status
            injury_status = player_data.get('injury_status')

            if injury_status and injury_status in ['Out', 'Doubtful', 'Questionable', 'IR', 'PUP', 'Suspended']:
                injured_player = {
                    'player_id': player_id,
                    'name': f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                    'position': player_data.get('position'),
                    'team': player_data.get('team'),
                    'injury_status': injury_status,
                    'injury_start_date': player_data.get('injury_start_date'),
                    'injury_body_part': player_data.get('injury_body_part'),
                    'injury_notes': player_data.get('injury_notes'),
                    'source': 'Sleeper API',
                    'last_updated': datetime.now().isoformat()
                }
                injured_players.append(injured_player)

        print(f"Found {len(injured_players)} injured players")
        return injured_players

    def fetch_espn_team_injuries(self, team_id: int) -> List[Dict]:
        """
        Fetch injuries for a specific NFL team from ESPN API

        Args:
            team_id: ESPN team ID (1-32)

        Returns:
            List of injured players for the team
        """
        url = f"{self.espn_injuries_base}/teams/{team_id}/injuries"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_espn_injuries(data, team_id)
            else:
                return []
        except requests.RequestException as e:
            print(f"Error fetching ESPN injuries for team {team_id}: {e}")
            return []

    def _parse_espn_injuries(self, data: Dict, team_id: int) -> List[Dict]:
        """
        Parse ESPN injury data response

        Args:
            data: Raw ESPN API response
            team_id: ESPN team ID

        Returns:
            List of parsed injury records
        """
        injured_players = []

        if 'items' in data:
            for item in data['items']:
                try:
                    injured_player = {
                        'espn_id': item.get('id'),
                        'team_id': team_id,
                        'injury_status': item.get('status'),
                        'injury_details': item.get('details'),
                        'source': 'ESPN API',
                        'last_updated': datetime.now().isoformat()
                    }
                    injured_players.append(injured_player)
                except Exception as e:
                    print(f"Error parsing ESPN injury record: {e}")
                    continue

        return injured_players

    def get_all_espn_injuries(self) -> List[Dict]:
        """
        Fetch injuries from all NFL teams via ESPN API

        Returns:
            Combined list of all NFL injuries from ESPN
        """
        print("Fetching injuries from ESPN API (32 teams)...")
        all_injuries = []

        # NFL has 32 teams (IDs 1-32 typically, but may vary)
        for team_id in range(1, 33):
            injuries = self.fetch_espn_team_injuries(team_id)
            all_injuries.extend(injuries)
            time.sleep(0.1)  # Rate limiting

        print(f"Found {len(all_injuries)} injuries from ESPN")
        return all_injuries

    def normalize_player_name(self, name: str) -> str:
        """
        Normalize player name for matching

        Args:
            name: Player name to normalize

        Returns:
            Normalized name (lowercase, no extra spaces)
        """
        return ' '.join(name.lower().split())

    def fetch_rss_news(self) -> Dict[str, List[Dict]]:
        """
        Fetch news from RSS feeds and organize by player mentions

        Returns:
            Dictionary mapping player names to their news items
        """
        news_by_player = {}

        print("Fetching RSS news feeds...")
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                print(f"Processing {len(feed.entries)} entries from {feed_url}")

                for entry in feed.entries:
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    link = entry.get('link', '')
                    published = entry.get('published', '')

                    # Combine title and description for analysis
                    full_text = f"{title} {description}"

                    # Store the news item
                    news_item = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'published': published,
                        'source': feed_url,
                        'full_text': full_text
                    }

                    # Try to extract player names from the text
                    # Store for later matching with injured players
                    if 'rss_news' not in self.news_cache:
                        self.news_cache['rss_news'] = []
                    self.news_cache['rss_news'].append(news_item)

            except Exception as e:
                print(f"Error fetching RSS feed {feed_url}: {e}")
                continue

        print(f"Fetched {len(self.news_cache.get('rss_news', []))} total news items")
        return news_by_player

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text using TextBlob

        Args:
            text: Text to analyze (headline or description)

        Returns:
            Dictionary with sentiment score and severity flag
        """
        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity  # -1 to 1

            # Flag as severe if sentiment is very negative
            is_severe = sentiment_score < -0.5

            # Determine severity label
            if sentiment_score < -0.5:
                severity = "Severe"
            elif sentiment_score < -0.2:
                severity = "Moderate"
            elif sentiment_score < 0.2:
                severity = "Neutral"
            else:
                severity = "Positive"

            return {
                'sentiment_score': round(sentiment_score, 3),
                'is_severe': is_severe,
                'severity_label': severity
            }
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0.0,
                'is_severe': False,
                'severity_label': 'Unknown'
            }

    def match_news_to_player(self, player_name: str) -> List[Dict]:
        """
        Find news items that mention a specific player

        Args:
            player_name: Name of the player to search for

        Returns:
            List of relevant news items with sentiment analysis
        """
        matched_news = []

        if 'rss_news' not in self.news_cache:
            return matched_news

        # Split player name into parts for better matching
        name_parts = player_name.lower().split()

        # Look for player mentions in news items
        for news_item in self.news_cache['rss_news']:
            full_text = news_item['full_text'].lower()

            # Check if player name appears in the text
            # Require at least last name match, or full name
            if len(name_parts) >= 2:
                last_name = name_parts[-1]
                first_name = name_parts[0]

                # Check for full name or last name match
                if (player_name.lower() in full_text or
                    last_name in full_text):

                    # Perform sentiment analysis on the headline/title
                    sentiment = self.analyze_sentiment(news_item['title'])

                    news_with_sentiment = {
                        'title': news_item['title'],
                        'description': news_item['description'][:200] + '...' if len(news_item['description']) > 200 else news_item['description'],
                        'link': news_item['link'],
                        'published': news_item['published'],
                        'sentiment_score': sentiment['sentiment_score'],
                        'severity_label': sentiment['severity_label'],
                        'is_severe': sentiment['is_severe']
                    }

                    matched_news.append(news_with_sentiment)

        # Sort by severity (most severe first) and limit to top 3
        matched_news.sort(key=lambda x: x['sentiment_score'])
        return matched_news[:3]

    def match_yahoo_to_injury_data(self, yahoo_players: List[Dict],
                                   injury_data: List[Dict]) -> List[Dict]:
        """
        Match Yahoo players with injury data from external sources

        Args:
            yahoo_players: List of players from Yahoo Fantasy
            injury_data: List of injured players from external sources

        Returns:
            List of matched players with injury updates
        """
        # Create lookup dictionary for injured players
        injured_lookup = {}
        for injured in injury_data:
            normalized_name = self.normalize_player_name(injured['name'])
            team = (injured.get('team') or '').upper()
            key = (normalized_name, team)

            # Keep the most severe injury status if duplicate
            if key not in injured_lookup:
                injured_lookup[key] = injured
            else:
                # Priority: Out > Doubtful > Questionable
                severity = {'IR': 5, 'Out': 4, 'Doubtful': 3, 'Questionable': 2, 'PUP': 4, 'Suspended': 4}
                current_severity = severity.get(injured_lookup[key].get('injury_status', ''), 0)
                new_severity = severity.get(injured.get('injury_status', ''), 0)

                if new_severity > current_severity:
                    injured_lookup[key] = injured

        # Match Yahoo players with injury data
        matched_players = []

        for player in yahoo_players:
            normalized_name = self.normalize_player_name(player['name'])
            team = (player.get('team') or '').upper()
            key = (normalized_name, team)

            if key in injured_lookup:
                injury_info = injured_lookup[key]

                # Create matched player record
                matched_player = {
                    'yahoo_player_id': player.get('player_id'),
                    'name': player['name'],
                    'position': player['position'],
                    'team': player['team'],
                    'owned_by_team': player.get('owned_by_team'),
                    'owned_by_manager': player.get('owned_by_manager'),
                    'injury_status': injury_info.get('injury_status'),
                    'injury_body_part': injury_info.get('injury_body_part'),
                    'injury_notes': injury_info.get('injury_notes'),
                    'injury_start_date': injury_info.get('injury_start_date'),
                    'source': injury_info.get('source'),
                    'last_updated': injury_info.get('last_updated')
                }

                matched_players.append(matched_player)

        return matched_players

    def get_injury_updates(self, yahoo_players: List[Dict]) -> List[Dict]:
        """
        Get injury updates for Yahoo fantasy players with RSS news and sentiment analysis

        Args:
            yahoo_players: List of players from Yahoo Fantasy league

        Returns:
            List of players with current injury information (including news and sentiment)
        """
        # Fetch RSS news feeds
        self.fetch_rss_news()

        # Fetch injury data from Sleeper (most comprehensive)
        sleeper_injuries = self.get_injured_players_from_sleeper()

        # Match Yahoo players with injury data
        matched_players = self.match_yahoo_to_injury_data(yahoo_players, sleeper_injuries)

        # Enrich with news and sentiment analysis
        for player in matched_players:
            news_items = self.match_news_to_player(player['name'])
            player['news'] = news_items

            # Get the most severe news item for summary
            if news_items:
                most_severe = news_items[0]  # Already sorted by sentiment score
                player['top_news_headline'] = most_severe['title']
                player['top_news_sentiment'] = most_severe['sentiment_score']
                player['top_news_severity'] = most_severe['severity_label']
                player['top_news_link'] = most_severe['link']

                # Extract timeline from news if available
                timeline_data = self.news_analyzer.analyze_news_for_timeline(news_items)
                if timeline_data.get('has_override'):
                    player['projected_return'] = {
                        'has_projection': True,
                        'timeline_type': timeline_data.get('override_type', 'Unknown'),
                        'timeline_text': timeline_data.get('reason', ''),
                        'estimated_weeks': timeline_data.get('weeks_out'),
                        'estimated_days': timeline_data.get('predicted_days'),
                        'source': 'News Analysis'
                    }
                else:
                    player['projected_return'] = {'has_projection': False}
            else:
                player['top_news_headline'] = 'No recent news'
                player['top_news_sentiment'] = 0.0
                player['top_news_severity'] = 'N/A'
                player['top_news_link'] = ''
                player['projected_return'] = {'has_projection': False}

        # Add backup player information if depth chart manager available
        if self.depth_chart_manager:
            matched_players = self.enrich_with_backup_info(matched_players, yahoo_players)

        # Save injuries to database for historical tracking
        if self.db:
            self._save_injuries_to_database(matched_players)

        # Add rule-based risk assessment (uses historical data from database)
        matched_players = self.enrich_with_risk_assessment(matched_players)

        return matched_players

    def enrich_with_backup_info(self, injured_players: List[Dict],
                                 all_yahoo_players: List[Dict]) -> List[Dict]:
        """
        Add backup player information to injury records, including backup injury status

        Args:
            injured_players: List of injured players
            all_yahoo_players: All players in Yahoo league (for availability check)

        Returns:
            Injured players enriched with backup player info
        """
        # Create a lookup of all injured players for quick checking
        injured_lookup = {}
        if 'rss_news' in self.news_cache:
            # Get fresh injury data from Sleeper
            all_sleeper_injuries = self.get_injured_players_from_sleeper()
            for inj in all_sleeper_injuries:
                normalized_name = self.normalize_player_name(inj['name'])
                injured_lookup[normalized_name] = {
                    'injury_status': inj.get('injury_status'),
                    'injury_body_part': inj.get('injury_body_part')
                }

        for injury in injured_players:
            # Only look up backups for fantasy-relevant positions
            if injury['position'] not in ['QB', 'RB', 'WR', 'TE']:
                continue

            # Get backup player from depth chart
            backup = self.depth_chart_manager.get_backup_for_player(
                injury['name'],
                injury['team'],
                injury['position']
            )

            if backup:
                # Check if backup is owned or available
                availability = self.depth_chart_manager.check_player_availability(
                    backup['name'],
                    all_yahoo_players
                )

                # Check if backup is also injured
                backup_normalized = self.normalize_player_name(backup['name'])
                backup_injury_info = injured_lookup.get(backup_normalized)

                injury['backup_player'] = {
                    'name': backup['name'],
                    'position': backup['position'],
                    'team': backup['team'],
                    'depth': backup['depth'],
                    'available': availability['available'],
                    'owned_by_team': availability['owned_by_team'],
                    'owned_by_manager': availability['owned_by_manager'],
                    'is_injured': backup_injury_info is not None,
                    'injury_status': backup_injury_info.get('injury_status') if backup_injury_info else None,
                    'injury_body_part': backup_injury_info.get('injury_body_part') if backup_injury_info else None
                }
            else:
                injury['backup_player'] = None

        return injured_players

    def get_new_injuries(self, current_injuries: List[Dict],
                        previous_injuries: List[Dict],
                        alert_window_hours: int = 24) -> List[Dict]:
        """
        Compare current and previous injury lists to find new injuries
        Only alerts on injuries within the alert window (default 24 hours)

        Args:
            current_injuries: Current injury data
            previous_injuries: Previous injury data
            alert_window_hours: Only alert on injuries first seen within this many hours

        Returns:
            List of newly injured players or status changes (within alert window)
        """
        from datetime import datetime, timedelta

        # Create lookup of previous injuries with timestamps
        prev_lookup = {}
        for injury in previous_injuries:
            key = (injury['name'], injury['team'])
            prev_lookup[key] = {
                'status': injury['injury_status'],
                'first_seen': injury.get('first_seen'),
                'last_updated': injury.get('last_updated')
            }

        # Find new or worsened injuries
        new_injuries = []
        severity = {'IR': 5, 'Out': 4, 'Doubtful': 3, 'Questionable': 2, 'PUP': 4, 'Suspended': 4}
        now = datetime.now()

        for injury in current_injuries:
            key = (injury['name'], injury['team'])
            current_status = injury['injury_status']

            if key not in prev_lookup:
                # Brand new injury - set first_seen timestamp
                injury['alert_type'] = 'NEW_INJURY'
                injury['first_seen'] = now.isoformat()
                new_injuries.append(injury)
            else:
                prev_data = prev_lookup[key]
                prev_status = prev_data['status']
                first_seen = prev_data.get('first_seen')

                # Preserve first_seen timestamp
                if first_seen:
                    injury['first_seen'] = first_seen
                else:
                    # Old data didn't have first_seen, set it now
                    injury['first_seen'] = now.isoformat()

                # Check if injury worsened
                current_severity = severity.get(current_status, 0)
                prev_severity = severity.get(prev_status, 0)

                if current_severity > prev_severity:
                    # Check if within alert window
                    if first_seen:
                        first_seen_dt = datetime.fromisoformat(first_seen)
                        hours_since_first = (now - first_seen_dt).total_seconds() / 3600

                        if hours_since_first <= alert_window_hours:
                            injury['alert_type'] = 'INJURY_WORSENED'
                            injury['previous_status'] = prev_status
                            injury['hours_since_first'] = hours_since_first
                            new_injuries.append(injury)
                    else:
                        # No timestamp, treat as new
                        injury['alert_type'] = 'INJURY_WORSENED'
                        injury['previous_status'] = prev_status
                        new_injuries.append(injury)

        return new_injuries

    def _save_injuries_to_database(self, injured_players: List[Dict]):
        """
        Save current injuries to database for historical tracking

        Args:
            injured_players: List of injured players
        """
        if not self.db:
            return

        # Deduplicate the input list first to prevent adding the same injury multiple times
        # Use player name + team + body part + status as the unique key
        seen = set()
        deduplicated_players = []

        for player in injured_players:
            # Create unique key for this injury
            key = (
                player['name'].lower().strip(),
                (player.get('team') or '').upper().strip(),
                (player.get('injury_body_part') or '').lower().strip(),
                (player.get('injury_status') or '').strip()
            )

            if key not in seen:
                seen.add(key)
                deduplicated_players.append(player)

        # Process deduplicated list
        for player in deduplicated_players:
            try:
                # Check if this is a new injury or status change
                history = self.db.get_player_injury_history(player['name'])

                # Find ALL active injuries (no end date)
                active_injuries = [inj for inj in history if not inj.get('injury_end_date')]

                # Normalize current injury info for comparison
                current_body_part = (player.get('injury_body_part') or '').lower().strip()
                current_status = player.get('injury_status', '').strip()

                # Look for an active injury matching the current body part
                matching_injury = None
                for active_inj in active_injuries:
                    active_body_part = (active_inj.get('injury_body_part') or '').lower().strip()
                    if current_body_part and active_body_part and current_body_part == active_body_part:
                        matching_injury = active_inj
                        break

                if matching_injury:
                    # Found an active injury for the same body part
                    # Check if status changed
                    if matching_injury.get('injury_status') != current_status:
                        self.db.update_injury_status(
                            matching_injury['id'],
                            current_status,
                            matching_injury.get('injury_status')
                        )
                    # Otherwise, same body part and same status - no action needed
                else:
                    # No active injury for this body part - add new injury
                    self.db.add_injury_record(player)

                # Update player summary
                self.db.update_player_summary(player['name'])

            except Exception as e:
                print(f"Error saving injury for {player['name']}: {e}")
                continue

    def enrich_with_risk_assessment(self, injured_players: List[Dict]) -> List[Dict]:
        """
        Add rule-based injury risk assessment to injury data

        Args:
            injured_players: List of injured players

        Returns:
            Injured players enriched with risk scores
        """
        print("Adding rule-based risk assessments...")

        for player in injured_players:
            try:
                # Calculate risk score using rule-based heuristics
                risk = self.risk_scorer.calculate_risk_score(
                    player['name'],
                    player
                )
                player['risk_assessment'] = risk
            except Exception as e:
                print(f"Error calculating risk for {player['name']}: {e}")
                player['risk_assessment'] = None

        return injured_players

    def save_injury_news_to_markdown(self, injured_players: List[Dict],
                                     output_file: str = 'injury_news.md') -> None:
        """
        Save injury report with news and sentiment to markdown file

        Args:
            injured_players: List of injured players with news and sentiment data
            output_file: Path to output markdown file
        """
        try:
            with open(output_file, 'w') as f:
                # Write header
                f.write("# Injury News Report\n\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

                if not injured_players:
                    f.write("No injured players found.\n")
                    return

                # Write summary statistics
                f.write(f"## Summary\n\n")
                f.write(f"- **Total Injured Players**: {len(injured_players)}\n")

                severe_news = sum(1 for p in injured_players if p.get('top_news_severity') == 'Severe')
                moderate_news = sum(1 for p in injured_players if p.get('top_news_severity') == 'Moderate')

                f.write(f"- **Players with Severe News**: {severe_news}\n")
                f.write(f"- **Players with Moderate News**: {moderate_news}\n\n")

                # Write detailed table
                f.write("## Detailed Injury Report\n\n")
                f.write("| Player | Team | Position | Status | Top News | Sentiment | Severity | Owner |\n")
                f.write("|--------|------|----------|--------|----------|-----------|----------|-------|\n")

                # Sort by severity (Severe first, then Moderate, etc.)
                severity_order = {'Severe': 0, 'Moderate': 1, 'Neutral': 2, 'Positive': 3, 'N/A': 4}
                sorted_players = sorted(injured_players,
                                       key=lambda x: severity_order.get(x.get('top_news_severity', 'N/A'), 5))

                for player in sorted_players:
                    name = player.get('name', 'Unknown')
                    team = player.get('team', 'N/A')
                    position = player.get('position', 'N/A')
                    status = player.get('injury_status', 'Unknown')
                    headline = player.get('top_news_headline', 'No recent news')
                    sentiment = player.get('top_news_sentiment', 0.0)
                    severity = player.get('top_news_severity', 'N/A')
                    owner = player.get('owned_by_manager', 'Free Agent')
                    news_link = player.get('top_news_link', '')

                    # Truncate headline if too long and add link if available
                    if len(headline) > 50:
                        headline = headline[:47] + "..."

                    if news_link:
                        headline = f"[{headline}]({news_link})"

                    # Add emoji indicators for severity
                    severity_icon = ""
                    if severity == "Severe":
                        severity_icon = "🔴 Severe"
                    elif severity == "Moderate":
                        severity_icon = "🟡 Moderate"
                    elif severity == "Neutral":
                        severity_icon = "⚪ Neutral"
                    elif severity == "Positive":
                        severity_icon = "🟢 Positive"
                    else:
                        severity_icon = severity

                    f.write(f"| {name} | {team} | {position} | {status} | {headline} | {sentiment:.2f} | {severity_icon} | {owner} |\n")

                # Write detailed news section
                f.write("\n## Detailed News by Player\n\n")

                for player in sorted_players:
                    name = player.get('name', 'Unknown')
                    news_items = player.get('news', [])

                    if news_items or player.get('backup_player') or player.get('risk_assessment') or player.get('projected_return', {}).get('has_projection'):
                        f.write(f"### {name} ({player.get('team', 'N/A')}) - {player.get('injury_status', 'Unknown')}\n\n")
                        f.write(f"**Owner**: {player.get('owned_by_manager', 'Free Agent')}\n\n")

                        # Show injury body part if available
                        body_part = player.get('injury_body_part')
                        if body_part:
                            f.write(f"**Injury**: {body_part}\n\n")

                        # Show latest news headline
                        latest_headline = player.get('top_news_headline', 'No recent news')
                        if latest_headline and latest_headline != 'No recent news':
                            news_link = player.get('top_news_link', '')
                            if news_link:
                                f.write(f"**📰 Latest Update**: [{latest_headline}]({news_link})\n\n")
                            else:
                                f.write(f"**📰 Latest Update**: {latest_headline}\n\n")

                        # Show projected return if available
                        projected_return = player.get('projected_return', {})
                        if projected_return.get('has_projection'):
                            timeline_text = projected_return.get('timeline_text', '')
                            weeks = projected_return.get('estimated_weeks')
                            days = projected_return.get('estimated_days')

                            f.write(f"**📅 Projected Return**:\n")
                            if timeline_text:
                                f.write(f"- {timeline_text}\n")
                            if weeks:
                                time_str = f"{weeks} weeks"
                                if days:
                                    time_str += f" (~{days} days)"
                                f.write(f"- Estimated: {time_str}\n")
                            elif days:
                                f.write(f"- Estimated: {days} days\n")
                            f.write("\n")

                        # Show risk assessment if available
                        risk = player.get('risk_assessment')
                        if risk:
                            risk_color = self._get_risk_emoji(risk.get('risk_level', 'Low'))
                            f.write(f"**⚠️ Re-Injury Risk**: {risk_color} {risk.get('risk_level', 'Unknown')} (Score: {risk.get('risk_score', 0)}/100)\n")
                            f.write(f"- {risk.get('message', 'No details')}\n")
                            if risk.get('chronic_areas'):
                                f.write(f"- Chronic issues: {', '.join(risk['chronic_areas'])}\n")
                            f.write("\n")

                        # Show backup player info if available
                        backup = player.get('backup_player')
                        if backup:
                            f.write(f"**Backup Player**: {backup['name']} ({backup['position']}, {backup['team']})\n")
                            if backup.get('is_injured'):
                                backup_status = backup.get('injury_status', 'Unknown')
                                backup_body_part = backup.get('injury_body_part', '')
                                injury_detail = f" - {backup_body_part}" if backup_body_part else ""
                                f.write(f"- 🚑 **WARNING**: Backup is also injured ({backup_status}{injury_detail})\n")
                            elif backup.get('available'):
                                f.write(f"- ✅ **Available** as free agent\n")
                            else:
                                f.write(f"- Owned by {backup['owned_by_team']}\n")
                            f.write("\n")

                        for idx, news in enumerate(news_items, 1):
                            f.write(f"**News {idx}**: {news['title']}\n\n")
                            f.write(f"- **Sentiment Score**: {news['sentiment_score']:.3f}\n")
                            f.write(f"- **Severity**: {news['severity_label']}\n")
                            if news.get('published'):
                                f.write(f"- **Published**: {news['published']}\n")
                            if news.get('link'):
                                f.write(f"- **Link**: {news['link']}\n")
                            if news.get('description'):
                                f.write(f"- **Details**: {news['description']}\n")
                            f.write("\n")

                        f.write("---\n\n")

            print(f"Injury news report saved to {output_file}")

        except Exception as e:
            print(f"Error saving injury news to markdown: {e}")

    def _get_risk_emoji(self, risk_level: str) -> str:
        """Get emoji for risk level"""
        emojis = {
            'Critical': '🔴',
            'High': '🟠',
            'Moderate': '🟡',
            'Low': '🟢',
            'Minimal': '⚪'
        }
        return emojis.get(risk_level, '⚪')

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


if __name__ == "__main__":
    # Test the injury tracker
    tracker = InjuryTracker()

    # Test Sleeper API
    injuries = tracker.get_injured_players_from_sleeper()

    print(f"\n=== INJURY REPORT ===")
    print(f"Total injured players: {len(injuries)}\n")

    # Group by injury status
    by_status = {}
    for injury in injuries:
        status = injury['injury_status']
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(injury)

    for status, players in sorted(by_status.items()):
        print(f"\n{status} ({len(players)} players):")
        for player in players[:5]:  # Show first 5 of each status
            print(f"  - {player['name']} ({player['position']}, {player['team']})")
            if player.get('injury_body_part'):
                print(f"    Body part: {player['injury_body_part']}")
