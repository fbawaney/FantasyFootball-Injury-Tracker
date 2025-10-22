"""
Injury Risk Scoring Module
Calculates risk scores for players based on injury history and patterns
Uses rule-based heuristics instead of machine learning
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import math


class InjuryRiskScorer:
    """Calculates injury risk scores for players using rule-based analysis"""

    def __init__(self, db=None):
        """
        Initialize risk scorer with rule-based heuristics

        Args:
            db: Optional InjuryDatabase instance for historical data
        """
        self.db = db
        # Track injury history in memory during session (if no DB)
        self.injury_history: Dict[str, List[Dict]] = {}

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

    def add_injury_to_history(self, player_name: str, injury: Dict):
        """
        Add an injury to player's history for tracking

        Args:
            player_name: Player's full name
            injury: Injury data dictionary
        """
        if player_name not in self.injury_history:
            self.injury_history[player_name] = []

        # Add timestamp if not present
        if 'timestamp' not in injury:
            injury['timestamp'] = datetime.now().isoformat()

        self.injury_history[player_name].append(injury)

    def calculate_risk_score(self, player_name: str,
                            current_injury: Optional[Dict] = None) -> Dict:
        """
        Calculate comprehensive injury risk score for a player using rule-based heuristics

        Args:
            player_name: Player's full name
            current_injury: Optional current injury data

        Returns:
            Dictionary with risk score and breakdown
        """
        # Get player's injury history - prefer database if available
        # NOTE: We only READ from database here, not add. Adding happens in injury_tracker._save_injuries_to_database()
        if self.db:
            try:
                history = self.db.get_player_injury_history(player_name)
            except Exception as e:
                print(f"Warning: Could not access injury database: {e}")
                history = self.injury_history.get(player_name, [])
        else:
            # Fallback to in-memory tracking (only for session without database)
            history = self.injury_history.get(player_name, [])

        if not history and not current_injury:
            return {
                'risk_score': 0,
                'risk_level': 'Low',
                'breakdown': {},
                'message': 'No injury history - first injury this season'
            }

        # Calculate individual risk factors using rule-based heuristics
        frequency_score = self._calculate_frequency_score(history)
        recurrence_score = self._calculate_recurrence_score(history, current_injury)
        severity_score = self._calculate_severity_score(current_injury)
        recency_score = self._calculate_recency_score(history)
        recovery_score = self._calculate_recovery_score(history, current_injury)

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
            'chronic_areas': self._identify_chronic_areas(history)
        }

    def _calculate_frequency_score(self, history: List[Dict]) -> float:
        """
        Calculate score based on injury frequency using rule-based heuristics

        Args:
            history: List of injury records

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Count total injuries
        injuries_all = len(history)

        # Simple rule-based frequency scoring
        # 1 injury = 15 points, 2 = 35, 3 = 60, 4+ = 90+
        if injuries_all == 1:
            score = 15
        elif injuries_all == 2:
            score = 35
        elif injuries_all == 3:
            score = 60
        elif injuries_all == 4:
            score = 85
        else:
            score = min(100, 85 + (injuries_all - 4) * 5)

        return score

    def _calculate_recurrence_score(self, history: List[Dict],
                                   current_injury: Optional[Dict]) -> float:
        """
        Calculate score based on recurring injuries (same body part injured multiple times)

        Args:
            history: List of injury records
            current_injury: Current injury data

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Count injuries by body part
        body_part_counts = {}
        for injury in history:
            body_part = injury.get('injury_body_part')
            if body_part:
                body_part_counts[body_part] = body_part_counts.get(body_part, 0) + 1

        if not body_part_counts:
            return 0

        # Get current injury body part
        current_body_part = None
        if current_injury:
            current_body_part = current_injury.get('injury_body_part')

        # Calculate recurrence penalty
        max_recurrence = max(body_part_counts.values())
        total_recurring_areas = sum(1 for count in body_part_counts.values() if count > 1)

        # Rule-based scoring
        score = 0

        # Penalty for worst recurring injury
        if max_recurrence == 2:
            score += 30
        elif max_recurrence == 3:
            score += 60
        elif max_recurrence >= 4:
            score += 90

        # Penalty for multiple chronic areas
        score += total_recurring_areas * 10

        # Extra penalty if current injury is a recurrence
        if current_body_part and body_part_counts.get(current_body_part, 0) > 1:
            score += 20

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

    def _calculate_recency_score(self, history: List[Dict]) -> float:
        """
        Calculate score based on how recent injuries are (currently injured = highest risk)

        Args:
            history: List of injury records

        Returns:
            Score 0-100
        """
        if not history:
            return 0

        # Rule: Currently injured = maximum recency risk
        # Since we're calculating risk while player is injured, they are by definition recently injured
        # Just return high score to reflect current injury status
        return 90

    def _calculate_recovery_score(self, history: List[Dict], current_injury: Optional[Dict]) -> float:
        """
        Calculate score based on injury severity (more severe = longer recovery = higher risk)

        Args:
            history: List of injury records
            current_injury: Current injury data

        Returns:
            Score 0-100
        """
        if not current_injury:
            return 0

        # Rule-based severity assessment based on injury status and body part
        injury_status = current_injury.get('injury_status', 'Questionable')
        body_part = current_injury.get('injury_body_part', '').lower()

        # Base score from injury status
        status_scores = {
            'Questionable': 20,
            'Doubtful': 35,
            'Out': 50,
            'PUP': 75,
            'IR': 90,
            'Suspended': 0
        }
        score = status_scores.get(injury_status, 20)

        # Adjust based on body part (known problematic injuries)
        high_risk_parts = ['achilles', 'acl', 'mcl', 'pcl', 'meniscus', 'concussion', 'back', 'neck']
        moderate_risk_parts = ['hamstring', 'groin', 'quad', 'calf', 'shoulder', 'ankle']

        if any(part in body_part for part in high_risk_parts):
            score = min(100, score + 20)
        elif any(part in body_part for part in moderate_risk_parts):
            score = min(100, score + 10)

        return score

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

    def _identify_chronic_areas(self, history: List[Dict]) -> List[str]:
        """
        Identify chronic injury areas (recurring injuries)

        Args:
            history: List of injury records

        Returns:
            List of body parts with multiple injuries
        """
        if not history:
            return []

        # Count injuries by body part
        body_part_counts = {}
        for injury in history:
            body_part = injury.get('injury_body_part')
            if body_part:
                body_part_counts[body_part] = body_part_counts.get(body_part, 0) + 1

        # Return body parts with 2+ injuries
        return [body_part for body_part, count in body_part_counts.items() if count > 1]

    def _generate_risk_message(self, score: float, history: List[Dict],
                               current_injury: Optional[Dict]) -> str:
        """
        Generate human-readable risk message using rule-based analysis

        Args:
            score: Risk score
            history: Injury history
            current_injury: Current injury data

        Returns:
            Risk message string
        """
        if score < 20:
            return "First injury or clean history - low re-injury risk"

        messages = []
        injuries_count = len(history)

        # Check frequency
        if injuries_count >= 4:
            messages.append(f"Injury-prone: {injuries_count} injuries tracked")
        elif injuries_count >= 2:
            messages.append(f"Multiple injuries this season ({injuries_count}x)")

        # Check for recurrence
        if current_injury:
            body_part = current_injury.get('injury_body_part')
            if body_part:
                body_part_counts = {}
                for injury in history:
                    bp = injury.get('injury_body_part')
                    if bp:
                        body_part_counts[bp] = body_part_counts.get(bp, 0) + 1

                count = body_part_counts.get(body_part, 0)
                if count > 1:
                    messages.append(f"Recurring {body_part} injury ({count}x)")

        # Check for severity
        if current_injury:
            status = current_injury.get('injury_status')
            if status in ['IR', 'PUP']:
                messages.append(f"Serious injury status ({status})")

        if not messages:
            return "Elevated risk of future injury problems"

        return "; ".join(messages)

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
    scorer = InjuryRiskScorer()

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

    # Test with multiple injuries
    print("\n\n--- Testing with recurring injury ---")
    test_injury2 = {
        'name': 'Test Player 2',
        'position': 'WR',
        'injury_status': 'Out',
        'injury_body_part': 'Hamstring'
    }

    scorer.add_injury_to_history('Test Player 2', {
        'injury_status': 'Questionable',
        'injury_body_part': 'Hamstring'
    })
    scorer.add_injury_to_history('Test Player 2', {
        'injury_status': 'Out',
        'injury_body_part': 'Ankle'
    })

    risk2 = scorer.calculate_risk_score('Test Player 2', test_injury2)

    print(f"\nRisk Assessment:")
    print(f"  Score: {risk2['risk_score']}/100")
    print(f"  Level: {risk2['risk_level']} {scorer.get_risk_color(risk2['risk_level'])}")
    print(f"  Message: {risk2['message']}")
    print(f"  Chronic areas: {risk2['chronic_areas']}")


if __name__ == "__main__":
    main()
