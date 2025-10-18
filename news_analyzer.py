"""
News Analyzer Module
Analyzes NFL injury news to extract timelines and override ML predictions
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class NewsAnalyzer:
    """Analyzes injury news for timeline information and prediction overrides"""

    def __init__(self):
        """Initialize news analyzer with keyword patterns"""

        # Season-ending keywords (override to rest of season)
        self.season_ending_keywords = [
            'season-ending',
            'out for season',
            'done for year',
            'ruled out for remainder',
            'will not return this season',
            'season is over',
            'shut down for season'
        ]

        # Surgery keywords (typically 6-12 weeks)
        self.surgery_keywords = [
            'surgery scheduled',
            'underwent surgery',
            'will undergo surgery',
            'surgical procedure',
            'went under knife',
            'requires surgery'
        ]

        # Severe injury keywords (extended timeline)
        self.severe_injury_keywords = {
            'torn acl': 270,           # 9+ months
            'ruptured achilles': 270,  # 9+ months
            'achilles tear': 270,
            'torn achilles': 270,
            'fractured': 42,           # 6+ weeks
            'broken': 42,
            'torn ligament': 180,      # 6+ months
            'mcl tear': 42,            # 6+ weeks
            'pcl tear': 90,            # 3+ months
        }

        # Return imminent keywords (override to very soon)
        self.return_keywords = [
            'activated from',
            'designated to return',
            'removed from ir',
            'expected to play',
            'cleared to play',
            'will play',
            'practicing fully',
            'full participant',
            'ready to return'
        ]

        # Week-to-week keywords (1-3 weeks)
        self.week_to_week_keywords = [
            'week-to-week',
            'week to week',
            'evaluated weekly',
            'no timetable',
            'indefinite',
            'day-to-day for now'
        ]

        # Day-to-day keywords (1-7 days)
        self.day_to_day_keywords = [
            'day-to-day',
            'day to day',
            'game-time decision',
            'gametime decision',
            'questionable for',
            'doubtful for'
        ]

        # Timeline extraction patterns (regex)
        self.timeline_patterns = [
            (r'out (\d+)-(\d+) weeks?', 'range_weeks'),
            (r'out (\d+) to (\d+) weeks?', 'range_weeks'),
            (r'miss (\d+)-(\d+) weeks?', 'range_weeks'),
            (r'miss (\d+) to (\d+) weeks?', 'range_weeks'),
            (r'out (\d+) weeks?', 'exact_weeks'),
            (r'miss (\d+) weeks?', 'exact_weeks'),
            (r'(\d+)-(\d+) week', 'range_weeks'),
            (r'out (\d+)-(\d+) games?', 'range_games'),
            (r'miss (\d+)-(\d+) games?', 'range_games'),
            (r'out (\d+) games?', 'exact_games'),
            (r'miss (\d+) games?', 'exact_games'),
            (r'(\d+) weeks? out', 'exact_weeks'),
            (r'(\d+) games? out', 'exact_games'),
        ]

    def analyze_news_for_timeline(self, news_items: List[Dict]) -> Dict:
        """
        Analyze news items to extract injury timeline information

        Args:
            news_items: List of news items with title, description, etc.

        Returns:
            Dictionary with override information
        """
        if not news_items:
            return {'has_override': False}

        # Combine all news text for analysis
        all_text = ''
        most_recent = news_items[0] if news_items else None

        for news in news_items:
            title = news.get('title', '').lower()
            description = news.get('description', '').lower()
            all_text += f"{title} {description} "

        # Check for specific override scenarios (priority order)

        # 1. Return imminent (highest priority - player is coming back)
        return_override = self._check_return_imminent(all_text, most_recent)
        if return_override['has_override']:
            return return_override

        # 2. Season-ending (second priority - definitive timeline)
        season_override = self._check_season_ending(all_text, most_recent)
        if season_override['has_override']:
            return season_override

        # 3. Severe specific injuries (ACL, Achilles, etc.)
        severe_override = self._check_severe_injury(all_text, most_recent)
        if severe_override['has_override']:
            return severe_override

        # 4. Surgery (major medical procedure)
        surgery_override = self._check_surgery(all_text, most_recent)
        if surgery_override['has_override']:
            return surgery_override

        # 5. Extract specific timeline from text (e.g., "4-6 weeks")
        timeline_override = self._extract_timeline(all_text, most_recent)
        if timeline_override['has_override']:
            return timeline_override

        # 6. Week-to-week (vague but indicates uncertainty)
        week_to_week_override = self._check_week_to_week(all_text, most_recent)
        if week_to_week_override['has_override']:
            return week_to_week_override

        # 7. Day-to-day (very short-term)
        day_to_day_override = self._check_day_to_day(all_text, most_recent)
        if day_to_day_override['has_override']:
            return day_to_day_override

        return {'has_override': False}

    def _check_season_ending(self, text: str, news_item: Dict) -> Dict:
        """Check for season-ending keywords"""
        for keyword in self.season_ending_keywords:
            if keyword in text:
                current_week = self._get_current_week()
                weeks_remaining = max(1, 18 - current_week)

                return {
                    'has_override': True,
                    'override_type': 'season_ending',
                    'predicted_days': weeks_remaining * 7,
                    'weeks_out': weeks_remaining,
                    'confidence_low': weeks_remaining * 7,
                    'confidence_high': 365,  # Could extend to next season
                    'reason': f"News reports season-ending injury: \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'critical',
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _check_severe_injury(self, text: str, news_item: Dict) -> Dict:
        """Check for severe injury keywords with known timelines"""
        for keyword, days in self.severe_injury_keywords.items():
            if keyword in text:
                weeks = days // 7
                return {
                    'has_override': True,
                    'override_type': 'severe_injury',
                    'predicted_days': days,
                    'weeks_out': weeks,
                    'confidence_low': days - 14,
                    'confidence_high': days + 30,
                    'reason': f"Severe injury reported ({keyword}): \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'critical',
                    'injury_type': keyword,
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _check_surgery(self, text: str, news_item: Dict) -> Dict:
        """Check for surgery keywords"""
        # Ignore minor procedures
        if 'minor surgery' in text or 'arthroscopic' in text:
            min_days = 21  # 3 weeks for minor surgery
        else:
            min_days = 42  # 6 weeks for major surgery

        for keyword in self.surgery_keywords:
            if keyword in text:
                weeks = min_days // 7
                return {
                    'has_override': True,
                    'override_type': 'surgery',
                    'predicted_days': min_days,
                    'weeks_out': weeks,
                    'confidence_low': min_days,
                    'confidence_high': min_days + 28,
                    'reason': f"Surgery reported: \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'high',
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _check_return_imminent(self, text: str, news_item: Dict) -> Dict:
        """Check for imminent return keywords"""
        for keyword in self.return_keywords:
            if keyword in text:
                return {
                    'has_override': True,
                    'override_type': 'return_imminent',
                    'predicted_days': 3,  # Could play within days
                    'weeks_out': 1,
                    'confidence_low': 0,
                    'confidence_high': 7,
                    'reason': f"Return imminent: \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'low',
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _check_week_to_week(self, text: str, news_item: Dict) -> Dict:
        """Check for week-to-week keywords"""
        for keyword in self.week_to_week_keywords:
            if keyword in text:
                return {
                    'has_override': True,
                    'override_type': 'week_to_week',
                    'predicted_days': 14,  # 2 weeks average
                    'weeks_out': 2,
                    'confidence_low': 7,
                    'confidence_high': 21,
                    'reason': f"Timeline uncertain (week-to-week): \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'moderate',
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _check_day_to_day(self, text: str, news_item: Dict) -> Dict:
        """Check for day-to-day keywords"""
        for keyword in self.day_to_day_keywords:
            if keyword in text:
                return {
                    'has_override': True,
                    'override_type': 'day_to_day',
                    'predicted_days': 3,  # Few days
                    'weeks_out': 1,
                    'confidence_low': 1,
                    'confidence_high': 7,
                    'reason': f"Short-term (day-to-day): \"{news_item.get('title', 'Unknown')}\"",
                    'severity': 'low',
                    'news_source': news_item.get('link', '')
                }
        return {'has_override': False}

    def _extract_timeline(self, text: str, news_item: Dict) -> Dict:
        """Extract specific timeline from text using regex"""
        for pattern, pattern_type in self.timeline_patterns:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'range_weeks':
                    low = int(match.group(1))
                    high = int(match.group(2))
                    avg_weeks = (low + high) / 2
                    predicted_days = int(avg_weeks * 7)

                    return {
                        'has_override': True,
                        'override_type': 'timeline_extracted',
                        'predicted_days': predicted_days,
                        'weeks_out': int(avg_weeks),
                        'confidence_low': low * 7,
                        'confidence_high': high * 7,
                        'reason': f"Timeline reported: {low}-{high} weeks: \"{news_item.get('title', 'Unknown')}\"",
                        'severity': 'moderate',
                        'news_source': news_item.get('link', '')
                    }

                elif pattern_type == 'exact_weeks':
                    weeks = int(match.group(1))
                    predicted_days = weeks * 7

                    return {
                        'has_override': True,
                        'override_type': 'timeline_extracted',
                        'predicted_days': predicted_days,
                        'weeks_out': weeks,
                        'confidence_low': max(1, predicted_days - 7),
                        'confidence_high': predicted_days + 7,
                        'reason': f"Timeline reported: {weeks} weeks: \"{news_item.get('title', 'Unknown')}\"",
                        'severity': 'moderate',
                        'news_source': news_item.get('link', '')
                    }

                elif pattern_type == 'range_games':
                    low_games = int(match.group(1))
                    high_games = int(match.group(2))
                    avg_weeks = (low_games + high_games) / 2
                    predicted_days = int(avg_weeks * 7)

                    return {
                        'has_override': True,
                        'override_type': 'timeline_extracted',
                        'predicted_days': predicted_days,
                        'weeks_out': int(avg_weeks),
                        'confidence_low': low_games * 7,
                        'confidence_high': high_games * 7,
                        'reason': f"Timeline reported: {low_games}-{high_games} games: \"{news_item.get('title', 'Unknown')}\"",
                        'severity': 'moderate',
                        'news_source': news_item.get('link', '')
                    }

                elif pattern_type == 'exact_games':
                    games = int(match.group(1))
                    weeks = games
                    predicted_days = weeks * 7

                    return {
                        'has_override': True,
                        'override_type': 'timeline_extracted',
                        'predicted_days': predicted_days,
                        'weeks_out': weeks,
                        'confidence_low': max(1, predicted_days - 7),
                        'confidence_high': predicted_days + 7,
                        'reason': f"Timeline reported: {games} games: \"{news_item.get('title', 'Unknown')}\"",
                        'severity': 'moderate',
                        'news_source': news_item.get('link', '')
                    }

        return {'has_override': False}

    def _get_current_week(self) -> int:
        """Get current NFL week"""
        now = datetime.now()
        season_start = datetime(now.year if now.month >= 9 else now.year - 1, 9, 1)

        if now < season_start:
            return 1

        weeks_elapsed = (now - season_start).days // 7
        return min(weeks_elapsed + 1, 18)


if __name__ == "__main__":
    # Test the news analyzer
    analyzer = NewsAnalyzer()

    test_cases = [
        {
            'title': "Christian McCaffrey ruled out for season with Achilles injury",
            'description': "49ers RB will undergo season-ending surgery"
        },
        {
            'title': "Justin Jefferson expected to miss 4-6 weeks with hamstring",
            'description': "Vikings WR suffered grade 2 hamstring strain"
        },
        {
            'title': "Joe Mixon designated to return from IR",
            'description': "Texans RB practicing and could play this week"
        },
        {
            'title': "Cooper Kupp listed as day-to-day with ankle injury",
            'description': "Rams WR is a game-time decision for Sunday"
        },
        {
            'title': "Derrick Henry week-to-week with foot injury",
            'description': "Titans RB has no timetable for return"
        }
    ]

    print("\nNews Analyzer Test Cases:\n")
    for test in test_cases:
        print(f"Title: {test['title']}")
        result = analyzer.analyze_news_for_timeline([test])

        if result['has_override']:
            print(f"  ✅ Override: {result['override_type']}")
            print(f"  📅 Timeline: {result['predicted_days']} days ({result['weeks_out']} weeks)")
            print(f"  📊 Range: {result['confidence_low']}-{result['confidence_high']} days")
            print(f"  💬 Reason: {result['reason']}")
        else:
            print(f"  ❌ No override detected")
        print()
