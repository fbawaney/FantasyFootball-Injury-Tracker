"""
Injury Risk Scoring Module
Calculates risk scores for players based on injury history and patterns
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import math
from injury_database import InjuryDatabase


class InjuryRiskScorer:
    """Calculates injury risk scores for players"""

    def __init__(self, db: InjuryDatabase):
        """
        Initialize risk scorer

        Args:
            db: InjuryDatabase instance
        """
        self.db = db

        # Risk weights for different factors
        self.weights = {
            'frequency': 0.30,      # How often player gets injured
            'recurrence': 0.25,     # Same injury multiple times
            'severity': 0.20,       # How severe current injury is
            'recency': 0.15,        # Recent vs old injuries
            'recovery': 0.10        # Slow recovery patterns
        }

        # Severity scores for injury statuses
        self.severity_scores = {
            'Questionable': 20,
            'Doubtful': 40,
            'Out': 60,
            'PUP': 80,
            'IR': 100,
            'Suspended': 0  # Different category
        }

    def calculate_risk_score(self, player_name: str,
                            current_injury: Optional[Dict] = None) -> Dict:
        """
        Calculate comprehensive injury risk score for a player

        Args:
            player_name: Player's full name
            current_injury: Optional current injury data

        Returns:
            Dictionary with risk score and breakdown
        """
        # Get player's injury history
        history = self.db.get_player_injury_history(player_name)
        summary = self.db.get_player_summary(player_name)

        if not history and not current_injury:
            return {
                'risk_score': 0,
                'risk_level': 'Low',
                'breakdown': {},
                'message': 'No injury history'
            }

        # Calculate individual risk factors
        frequency_score = self._calculate_frequency_score(history)
        recurrence_score = self._calculate_recurrence_score(player_name, current_injury)
        severity_score = self._calculate_severity_score(current_injury)
        recency_score = self._calculate_recency_score(history)
        recovery_score = self._calculate_recovery_score(history)

        # Weighted total
        total_score = (
            frequency_score * self.weights['frequency'] +
            recurrence_score * self.weights['recurrence'] +
            severity_score * self.weights['severity'] +
            recency_score * self.weights['recency'] +
            recovery_score * self.weights['recovery']
        )

        # Normalize to 0-100
        total_score = min(100, max(0, total_score))

        # Determine risk level
        risk_level = self._get_risk_level(total_score)

        # Generate risk message
        message = self._generate_risk_message(
            total_score, history, current_injury
        )

        return {
            'risk_score': round(total_score, 1),
            'risk_level': risk_level,
            'breakdown': {
                'frequency': round(frequency_score, 1),
                'recurrence': round(recurrence_score, 1),
                'severity': round(severity_score, 1),
                'recency': round(recency_score, 1),
                'recovery': round(recovery_score, 1)
            },
            'message': message,
            'total_injuries': len(history),
            'chronic_areas': self._identify_chronic_areas(player_name)
        }

    def _calculate_frequency_score(self, history: list) -> float:
        """
        Calculate score based on injury frequency

        Args:
            history: List of injury records

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Count injuries in different time periods
        now = datetime.now()
        injuries_6mo = 0
        injuries_1yr = 0
        injuries_all = len(history)

        for injury in history:
            start_date = injury.get('injury_start_date')
            if not start_date:
                continue

            try:
                injury_date = datetime.fromisoformat(start_date)
                days_ago = (now - injury_date).days

                if days_ago <= 180:
                    injuries_6mo += 1
                if days_ago <= 365:
                    injuries_1yr += 1
            except:
                continue

        # Recent injuries count more
        score = (
            injuries_6mo * 30 +
            (injuries_1yr - injuries_6mo) * 15 +
            (injuries_all - injuries_1yr) * 5
        )

        return min(100, score)

    def _calculate_recurrence_score(self, player_name: str,
                                   current_injury: Optional[Dict]) -> float:
        """
        Calculate score based on recurring injuries

        Args:
            player_name: Player name
            current_injury: Current injury data

        Returns:
            Score 0-100
        """
        recurring = self.db.get_recurring_injuries(player_name)

        if not recurring:
            return 0

        # Check if current injury is a recurrence
        current_body_part = None
        if current_injury:
            current_body_part = current_injury.get('injury_body_part')

        # Calculate recurrence penalty
        max_recurrence = max(recurring.values()) if recurring.values() else 0
        total_recurring_injuries = sum(1 for count in recurring.values() if count and count > 1)

        score = (
            max_recurrence * 20 +  # Worst recurring injury
            total_recurring_injuries * 15  # Number of different recurring areas
        )

        # Extra penalty if current injury is a recurrence
        if current_body_part and recurring.get(current_body_part, 0) > 1:
            score += 25

        return min(100, score)

    def _calculate_severity_score(self, current_injury: Optional[Dict]) -> float:
        """
        Calculate score based on current injury severity

        Args:
            current_injury: Current injury data

        Returns:
            Score 0-100
        """
        if not current_injury:
            return 0

        status = current_injury.get('injury_status', 'Questionable')
        return self.severity_scores.get(status, 20)

    def _calculate_recency_score(self, history: list) -> float:
        """
        Calculate score based on how recent injuries are

        Args:
            history: List of injury records

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Find most recent injury
        most_recent = None
        for injury in history:
            start_date = injury.get('injury_start_date')
            if start_date:
                try:
                    injury_date = datetime.fromisoformat(start_date)
                    if not most_recent or injury_date > most_recent:
                        most_recent = injury_date
                except:
                    continue

        if not most_recent:
            return 0

        days_since = (datetime.now() - most_recent).days

        # Handle None or negative values
        if days_since is None or days_since < 0:
            return 0

        # More recent = higher score
        if days_since < 7:
            return 100
        elif days_since < 30:
            return 80
        elif days_since < 90:
            return 60
        elif days_since < 180:
            return 40
        elif days_since < 365:
            return 20
        else:
            return 5

    def _calculate_recovery_score(self, history: list) -> float:
        """
        Calculate score based on recovery time patterns

        Args:
            history: List of injury records

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Look at injuries with known recovery times
        recovery_times = []
        for injury in history:
            days_missed = injury.get('days_missed')
            # Handle None and ensure it's a number
            if days_missed is not None and days_missed > 0:
                try:
                    recovery_times.append(float(days_missed))
                except (ValueError, TypeError):
                    continue

        if not recovery_times:
            return 0

        # Calculate average recovery time
        avg_recovery = sum(recovery_times) / len(recovery_times)

        # Longer average recovery = higher risk
        if avg_recovery > 30:
            score = 100
        elif avg_recovery > 21:
            score = 80
        elif avg_recovery > 14:
            score = 60
        elif avg_recovery > 7:
            score = 40
        else:
            score = 20

        # Bonus penalty for highly variable recovery times
        if len(recovery_times) > 1:
            import statistics
            try:
                std_dev = statistics.stdev(recovery_times)
                if std_dev > 14:  # High variance
                    score += 20
            except:
                pass

        return min(100, score)

    def _get_risk_level(self, score: float) -> str:
        """
        Convert numerical score to risk level

        Args:
            score: Risk score 0-100

        Returns:
            Risk level string
        """
        if score >= 75:
            return 'Critical'
        elif score >= 60:
            return 'High'
        elif score >= 40:
            return 'Moderate'
        elif score >= 20:
            return 'Low'
        else:
            return 'Minimal'

    def _identify_chronic_areas(self, player_name: str) -> list:
        """
        Identify chronic injury areas (recurring injuries)

        Args:
            player_name: Player name

        Returns:
            List of body parts with multiple injuries
        """
        recurring = self.db.get_recurring_injuries(player_name)
        return [body_part for body_part, count in recurring.items() if count > 1]

    def _generate_risk_message(self, score: float, history: list,
                               current_injury: Optional[Dict]) -> str:
        """
        Generate human-readable risk message

        Args:
            score: Risk score
            history: Injury history
            current_injury: Current injury data

        Returns:
            Risk message string
        """
        if score < 20:
            return "Clean injury history - low risk of future problems"

        messages = []

        # Check for recent injuries
        recent_count = sum(1 for inj in history
                          if self._is_recent(inj.get('injury_start_date'), days=180))
        if recent_count > 2:
            messages.append(f"Injury-prone: {recent_count} injuries in last 6 months")

        # Check for recurrence
        if current_injury:
            body_part = current_injury.get('injury_body_part')
            player_name = current_injury.get('name')
            if body_part and player_name:
                recurring = self.db.get_recurring_injuries(player_name)
                count = recurring.get(body_part, 0)
                if count > 1:
                    messages.append(f"Recurring {body_part} injury ({count}x)")

        # Check for slow recovery
        slow_recovery = [inj for inj in history
                        if inj.get('days_missed') is not None and inj.get('days_missed', 0) > 21]
        if len(slow_recovery) > 2:
            messages.append(f"Slow healer: {len(slow_recovery)} injuries took 3+ weeks")

        if not messages:
            return "Elevated risk of future injury problems"

        return "; ".join(messages)

    def _is_recent(self, date_str: Optional[str], days: int = 180) -> bool:
        """
        Check if date is recent

        Args:
            date_str: ISO format date string
            days: Number of days to consider recent

        Returns:
            True if recent
        """
        if not date_str:
            return False

        try:
            injury_date = datetime.fromisoformat(date_str)
            days_ago = (datetime.now() - injury_date).days
            return days_ago <= days
        except:
            return False

    def get_risk_color(self, risk_level: str) -> str:
        """
        Get color code for risk level

        Args:
            risk_level: Risk level string

        Returns:
            Emoji or color indicator
        """
        colors = {
            'Critical': '🔴',
            'High': '🟠',
            'Moderate': '🟡',
            'Low': '🟢',
            'Minimal': '⚪'
        }
        return colors.get(risk_level, '⚪')


def main():
    """Main entry point for standalone testing"""
    from injury_database import InjuryDatabase

    with InjuryDatabase() as db:
        scorer = InjuryRiskScorer(db)

        # Test with a sample injury
        test_injury = {
            'name': 'Test Player',
            'position': 'RB',
            'injury_status': 'Out',
            'injury_body_part': 'Hamstring'
        }

        print("\nCalculating risk score for sample injury...")
        risk = scorer.calculate_risk_score('Test Player', test_injury)

        print(f"\nRisk Assessment:")
        print(f"  Score: {risk['risk_score']}/100")
        print(f"  Level: {risk['risk_level']} {scorer.get_risk_color(risk['risk_level'])}")
        print(f"  Message: {risk['message']}")
        print(f"\nBreakdown:")
        for factor, score in risk['breakdown'].items():
            print(f"  {factor.capitalize()}: {score}")


if __name__ == "__main__":
    main()
