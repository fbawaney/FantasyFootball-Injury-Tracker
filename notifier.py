"""
Notification Module
Sends alerts about player injuries via multiple channels
"""
import os
import platform
import subprocess
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class Notifier:
    """Handles notifications for injury alerts"""

    def __init__(self, method: str = 'console'):
        """
        Initialize notifier

        Args:
            method: Notification method ('console', 'desktop', 'email')
        """
        self.method = os.getenv('NOTIFICATION_METHOD', method)
        self.system = platform.system()

    def send_alert(self, injuries: List[Dict], alert_mode: bool = True):
        """
        Send injury alerts using configured method

        Args:
            injuries: List of injury records to alert on
            alert_mode: If True, show targeted alerts (new/worsened only)
                       If False, show comprehensive report (all injuries)
        """
        if not injuries:
            return

        if self.method == 'console':
            self._console_alert(injuries, alert_mode=alert_mode)
        elif self.method == 'desktop':
            self._desktop_alert(injuries)
        elif self.method == 'email':
            self._email_alert(injuries)
        else:
            print(f"Unknown notification method: {self.method}")
            self._console_alert(injuries, alert_mode=alert_mode)

    def _console_alert(self, injuries: List[Dict], alert_mode: bool = True):
        """
        Display alerts in console

        Args:
            injuries: List of injury records
            alert_mode: If True, show as alerts. If False, show as comprehensive report
        """
        print("\n" + "=" * 80)
        if alert_mode:
            print("🚨 INJURY ALERT 🚨")
            print("=" * 80)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"New/Updated Injuries: {len(injuries)}")
            print("(Recent injuries requiring immediate attention)\n")
        else:
            print("📊 COMPREHENSIVE INJURY REPORT 📊")
            print("=" * 80)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Injured Players: {len(injuries)}")
            print("(All current injuries with ML predictions)\n")

        for injury in injuries:
            alert_type = injury.get('alert_type', 'UPDATE')
            status = injury.get('injury_status', 'Unknown')

            # Format alert based on type
            if alert_type == 'NEW_INJURY':
                icon = "🆕"
                alert_msg = "NEW INJURY"
            elif alert_type == 'INJURY_WORSENED':
                icon = "⚠️"
                prev_status = injury.get('previous_status', 'Unknown')
                alert_msg = f"WORSENED: {prev_status} → {status}"
                # Show how long ago it was first reported
                hours_since = injury.get('hours_since_first')
                if hours_since:
                    alert_msg += f" (first reported {hours_since:.1f} hours ago)"
            else:
                icon = "ℹ️"
                alert_msg = "UPDATE"

            print(f"{icon} {alert_msg}")
            print(f"   Player: {injury['name']}")
            print(f"   Position: {injury['position']} | Team: {injury['team']}")
            print(f"   Status: {status}")

            if injury.get('injury_body_part'):
                print(f"   Injury: {injury['injury_body_part']}")

            if injury.get('injury_notes'):
                print(f"   Notes: {injury['injury_notes']}")

            # Fantasy ownership info
            owned_by = injury.get('owned_by_team')
            if owned_by and owned_by != 'Free Agent':
                manager = injury.get('owned_by_manager', 'Unknown')
                print(f"   🏈 OWNED BY: {owned_by} (Manager: {manager})")
            else:
                print(f"   📍 Available as Free Agent")

            # ML Prediction information
            ml_pred = injury.get('ml_prediction')
            if ml_pred and not ml_pred.get('error'):
                print(f"\n   🤖 ML PREDICTION:")

                # Check if overridden by news
                if ml_pred.get('overridden_by_news'):
                    print(f"      📰 NEWS-ADJUSTED TIMELINE:")
                    return_week = ml_pred.get('return_week', '?')
                    weeks_out = ml_pred.get('weeks_out', '?')
                    print(f"      Expected return: NFL Week {return_week} ({weeks_out} weeks from now)")
                    print(f"      Predicted days out: {ml_pred.get('predicted_days', '?')} days")
                    print(f"      Confidence range: {ml_pred.get('confidence_low', '?')}-{ml_pred.get('confidence_high', '?')} days")

                    # Show original ML prediction
                    ml_orig = ml_pred.get('ml_original', {})
                    if ml_orig:
                        print(f"\n      📊 ML Model (before news): NFL Week {ml_orig.get('return_week', '?')} ({ml_orig.get('predicted_days', '?')} days)")

                    # Show override reason
                    print(f"\n      ⚠️  Override reason:")
                    print(f"         {ml_pred.get('override_reason', 'News reports different timeline')}")
                    if ml_pred.get('news_source'):
                        print(f"         Source: {ml_pred['news_source']}")
                else:
                    print(f"      ML Model prediction:")
                    current_week = ml_pred.get('current_week', '?')
                    return_week = ml_pred.get('return_week', '?')
                    weeks_out = ml_pred.get('weeks_out', '?')
                    print(f"      Expected return: NFL Week {return_week} ({weeks_out} weeks from now)")
                    print(f"      Predicted days out: {ml_pred.get('predicted_days', '?')} days")
                    print(f"      Confidence range: {ml_pred.get('confidence_low', '?')}-{ml_pred.get('confidence_high', '?')} days")

                print(f"      Return date: {ml_pred.get('expected_return_date', 'Unknown')}")

            # Injury Risk Assessment
            risk = injury.get('risk_assessment')
            if risk:
                risk_level = risk.get('risk_level', 'Unknown')
                risk_score = risk.get('risk_score', 0)
                risk_msg = risk.get('message', '')

                # Color-coded risk indicator
                if risk_level == 'Critical':
                    risk_icon = "🔴"
                elif risk_level == 'High':
                    risk_icon = "🟠"
                elif risk_level == 'Moderate':
                    risk_icon = "🟡"
                elif risk_level == 'Low':
                    risk_icon = "🟢"
                else:
                    risk_icon = "⚪"

                print(f"\n   {risk_icon} INJURY RISK: {risk_level} ({risk_score}/100)")
                if risk_msg:
                    print(f"      {risk_msg}")
                if risk.get('chronic_areas'):
                    print(f"      Chronic issues: {', '.join(risk['chronic_areas'])}")

            # News sentiment information
            severity = injury.get('top_news_severity', 'N/A')
            if severity != 'N/A':
                sentiment_score = injury.get('top_news_sentiment', 0.0)

                # Color-coded severity indicator
                if severity == 'Severe':
                    severity_icon = "🔴"
                elif severity == 'Moderate':
                    severity_icon = "🟡"
                elif severity == 'Neutral':
                    severity_icon = "⚪"
                elif severity == 'Positive':
                    severity_icon = "🟢"
                else:
                    severity_icon = "⚫"

                print(f"\n   {severity_icon} NEWS SENTIMENT: {severity} (Score: {sentiment_score:.2f})")

            # Backup player information
            backup = injury.get('backup_player')
            if backup:
                print(f"\n   💡 DIRECT BACKUP:")
                print(f"      {backup['name']} ({backup['position']}, {backup['team']})")

                # Check if backup is injured
                if backup.get('is_injured'):
                    backup_status = backup.get('injury_status', 'Unknown')
                    backup_body_part = backup.get('injury_body_part', '')
                    injury_detail = f" - {backup_body_part}" if backup_body_part else ""
                    print(f"      🚑 BACKUP IS ALSO INJURED: {backup_status}{injury_detail}")
                    print(f"      ⚠️  NOT RECOMMENDED as replacement!")
                elif backup['available']:
                    if backup['owned_by_team'] == 'Not in League':
                        print(f"      ⚠️  Not on any roster (deep backup)")
                    else:
                        print(f"      ✅ AVAILABLE as Free Agent - ADD NOW!")
                else:
                    print(f"      ❌ Owned by {backup['owned_by_team']}")
                    if backup.get('owned_by_manager'):
                        print(f"         (Manager: {backup['owned_by_manager']})")
            elif injury['position'] in ['QB', 'RB', 'WR', 'TE']:
                print(f"\n   💡 DIRECT BACKUP: Not listed on depth chart")

            print(f"\n   Source: {injury.get('source', 'Unknown')}")
            print()

        print("=" * 80 + "\n")

    def _desktop_alert(self, injuries: List[Dict]):
        """
        Send desktop notification

        Args:
            injuries: List of injury records
        """
        # First show console alert
        self._console_alert(injuries)

        # Then send desktop notification
        count = len(injuries)
        title = f"🚨 {count} Injury Alert{'s' if count > 1 else ''}"

        # Create message with top injuries
        messages = []
        for injury in injuries[:3]:  # Show max 3 in notification
            status = injury.get('injury_status', 'Unknown')
            name = injury['name']
            owned = injury.get('owned_by_team', 'Free Agent')
            messages.append(f"{name} - {status} ({owned})")

        if count > 3:
            messages.append(f"...and {count - 3} more")

        message = "\n".join(messages)

        try:
            if self.system == 'Darwin':  # macOS
                self._send_macos_notification(title, message)
            elif self.system == 'Linux':
                self._send_linux_notification(title, message)
            elif self.system == 'Windows':
                self._send_windows_notification(title, message)
            else:
                print(f"Desktop notifications not supported on {self.system}")
        except Exception as e:
            print(f"Error sending desktop notification: {e}")

    def _send_macos_notification(self, title: str, message: str):
        """Send notification on macOS using osascript"""
        script = f'display notification "{message}" with title "{title}" sound name "default"'
        subprocess.run(['osascript', '-e', script], check=False)

    def _send_linux_notification(self, title: str, message: str):
        """Send notification on Linux using notify-send"""
        subprocess.run(['notify-send', title, message], check=False)

    def _send_windows_notification(self, title: str, message: str):
        """Send notification on Windows using PowerShell"""
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $toastXml = [xml] $template.GetXml()
        $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) > $null
        $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{message}")) > $null
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($toastXml.OuterXml)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Fantasy Football Injury Tracker")
        $notifier.Show($toast)
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=False)

    def _email_alert(self, injuries: List[Dict]):
        """
        Send email alert (placeholder - requires SMTP configuration)

        Args:
            injuries: List of injury records
        """
        print("Email notifications require SMTP configuration.")
        print("For now, showing console alert instead:\n")
        self._console_alert(injuries)

        # TODO: Implement email sending
        # This would require:
        # 1. SMTP server configuration (Gmail, SendGrid, etc.)
        # 2. Email credentials in .env
        # 3. HTML email template
        # 4. smtplib or similar library

    def format_summary_report(self, all_injuries: List[Dict], show_all: bool = True) -> str:
        """
        Format a summary report of all current injuries with ML predictions

        Args:
            all_injuries: All current injuries
            show_all: If True, show comprehensive report with ML predictions for all

        Returns:
            Formatted report string
        """
        if not all_injuries:
            return "No injuries to report."

        # Group by ownership
        owned = [i for i in all_injuries if i.get('owned_by_team') and i['owned_by_team'] != 'Free Agent']
        free_agents = [i for i in all_injuries if i.get('owned_by_team') == 'Free Agent']

        # Count severe news
        severe_count = sum(1 for i in all_injuries if i.get('top_news_severity') == 'Severe')
        moderate_count = sum(1 for i in all_injuries if i.get('top_news_severity') == 'Moderate')

        report = []
        report.append("\n" + "=" * 80)
        report.append("📊 INJURY SUMMARY REPORT WITH NEWS SENTIMENT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Injuries: {len(all_injuries)}")
        report.append(f"  - Owned Players: {len(owned)}")
        report.append(f"  - Free Agents: {len(free_agents)}")
        if severe_count > 0:
            report.append(f"  - 🔴 Players with SEVERE negative news: {severe_count}")
        if moderate_count > 0:
            report.append(f"  - 🟡 Players with MODERATE negative news: {moderate_count}")

        if owned:
            report.append("\n" + "-" * 80)
            report.append("⚠️  OWNED PLAYERS WITH INJURIES")
            report.append("-" * 80)

            # Group by team
            by_team = {}
            for injury in owned:
                team = injury.get('owned_by_team', 'Unknown')
                if team not in by_team:
                    by_team[team] = []
                by_team[team].append(injury)

            for team, players in sorted(by_team.items()):
                report.append(f"\n{team}:")
                for injury in players:
                    report.append(f"\n  • {injury['name']} ({injury['position']}, {injury['team']})")
                    report.append(f"    ├─ Status: {injury['injury_status']}")
                    if injury.get('injury_body_part'):
                        report.append(f"    ├─ Injury: {injury['injury_body_part']}")

                    # Show sentiment analysis
                    severity = injury.get('top_news_severity', 'N/A')
                    sentiment_score = injury.get('top_news_sentiment', 0.0)

                    # Color-coded severity indicator
                    if severity == 'Severe':
                        severity_icon = "🔴"
                    elif severity == 'Moderate':
                        severity_icon = "🟡"
                    elif severity == 'Neutral':
                        severity_icon = "⚪"
                    elif severity == 'Positive':
                        severity_icon = "🟢"
                    else:
                        severity_icon = "⚫"

                    report.append(f"    ├─ {severity_icon} News Sentiment: {severity} ({sentiment_score:.2f})")

                    # Show ML prediction if available and show_all is True
                    if show_all:
                        ml_pred = injury.get('ml_prediction')
                        if ml_pred and not ml_pred.get('error'):
                            return_week = ml_pred.get('return_week', '?')
                            weeks_out = ml_pred.get('weeks_out', '?')
                            days = ml_pred.get('predicted_days', '?')

                            report.append(f"    │")
                            if ml_pred.get('overridden_by_news'):
                                report.append(f"    ├─ 📰 NEWS-ADJUSTED TIMELINE:")
                                report.append(f"    │    Expected return: NFL Week {return_week} ({weeks_out} weeks, ~{days} days)")
                                ml_orig = ml_pred.get('ml_original', {})
                                if ml_orig:
                                    report.append(f"    │    ML model said: Week {ml_orig.get('return_week', '?')} ({ml_orig.get('predicted_days', '?')} days)")
                                    override_reason = ml_pred.get('override_reason', 'News reports different timeline')
                                    # Truncate long override reasons (increased to 160 chars)
                                    if len(override_reason) > 160:
                                        override_reason = override_reason[:157] + "..."
                                    report.append(f"    │    Override: {override_reason}")
                            else:
                                report.append(f"    ├─ 🤖 ML PREDICTION:")
                                report.append(f"    │    Expected return: NFL Week {return_week} ({weeks_out} weeks, ~{days} days)")

                        # Show risk assessment
                        risk = injury.get('risk_assessment')
                        if risk:
                            risk_level = risk.get('risk_level', 'Unknown')
                            risk_score = risk.get('risk_score', 0)
                            risk_icon = self._get_risk_icon(risk_level)
                            risk_message = risk.get('message', '')
                            chronic_areas = risk.get('chronic_areas', [])

                            report.append(f"    │")
                            report.append(f"    ├─ ⚠️  FUTURE INJURY RISK: {risk_icon} {risk_level} ({risk_score}/100)")
                            if risk_message and risk_message != 'Clean injury history - low risk of future problems':
                                report.append(f"    │    {risk_message}")
                            if chronic_areas:
                                report.append(f"    │    Chronic areas: {', '.join(chronic_areas)}")

                    # Show backup info in summary
                    backup = injury.get('backup_player')
                    if backup:
                        report.append(f"    │")
                        if backup.get('is_injured'):
                            backup_status = backup.get('injury_status', 'Unknown')
                            report.append(f"    └─ 👉 Backup: {backup['name']} - 🚑 INJURED ({backup_status})")
                        elif backup['available']:
                            report.append(f"    └─ 👉 Backup: {backup['name']} - ✅ AVAILABLE")
                        else:
                            report.append(f"    └─ 👉 Backup: {backup['name']} - Owned by {backup['owned_by_team']}")
                    else:
                        report.append("")  # Add spacing between players

        # Removed free agents section per user request

        report.append("\n" + "=" * 80)
        report.append("📊 LEGEND:")
        report.append("-" * 80)
        report.append("News Sentiment: 🔴 Severe (<-0.5) | 🟡 Moderate (-0.5 to -0.2) | ⚪ Neutral | 🟢 Positive (>0.2)")
        report.append("")
        report.append("Future Injury Risk: Predicts likelihood of future injury problems based on:")
        report.append("  • Injury frequency (how often they get hurt)")
        report.append("  • Recurrence (same body part injured multiple times)")
        report.append("  • Current injury severity")
        report.append("  • Recovery patterns (slow vs. fast healers)")
        report.append("  Risk Levels: 🔴 Critical (75+) | 🟠 High (60-74) | 🟡 Moderate (40-59) | 🟢 Low (<40)")
        report.append("=" * 80 + "\n")

        return "\n".join(report)

    def _get_risk_icon(self, risk_level: str) -> str:
        """Get emoji for risk level"""
        emojis = {
            'Critical': '🔴',
            'High': '🟠',
            'Moderate': '🟡',
            'Low': '🟢',
            'Minimal': '⚪'
        }
        return emojis.get(risk_level, '⚪')


if __name__ == "__main__":
    # Test notifier
    notifier = Notifier('console')

    # Create test injury data
    test_injuries = [
        {
            'name': 'Christian McCaffrey',
            'position': 'RB',
            'team': 'SF',
            'injury_status': 'Out',
            'injury_body_part': 'Achilles',
            'owned_by_team': 'Team Alpha',
            'owned_by_manager': 'John Doe',
            'alert_type': 'NEW_INJURY',
            'source': 'Sleeper API'
        },
        {
            'name': 'Justin Jefferson',
            'position': 'WR',
            'team': 'MIN',
            'injury_status': 'Questionable',
            'injury_body_part': 'Hamstring',
            'owned_by_team': 'Free Agent',
            'alert_type': 'UPDATE',
            'source': 'Sleeper API'
        }
    ]

    print("Testing console notification:")
    notifier.send_alert(test_injuries)

    print("\nTesting summary report:")
    print(notifier.format_summary_report(test_injuries))
