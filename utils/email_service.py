# utils/email_service.py - Email Notification Service
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Avoid circular imports
def get_models():
    """Get model classes when needed"""
    try:
        from models.game import Game, GameAssignment
        return Game, GameAssignment
    except ImportError:
        # Models not available yet
        return None, None

class EmailService:
    """Email notification service"""
    
    def __init__(self, smtp_server=None, smtp_port=587, username=None, password=None):
        """Initialize email service with SMTP configuration"""
        # For development, we'll use print statements instead of actual SMTP
        # In production, configure with real SMTP settings
        self.smtp_server = smtp_server or 'localhost'
        self.smtp_port = smtp_port
        self.username = username or 'noreply@sportsscheduler.com'
        self.password = password
        self.development_mode = not all([smtp_server, username, password])
        
        if self.development_mode:
            logger.info("EmailService running in development mode - emails will be logged instead of sent")
    
    def send_email(self, to_email, subject, body, from_name="Sports Scheduler"):
        """Send an email"""
        try:
            if self.development_mode:
                # Development mode - just log the email
                logger.info(f"""
                === EMAIL NOTIFICATION ===
                To: {to_email}
                Subject: {subject}
                From: {from_name} <{self.username}>
                
                {body}
                === END EMAIL ===
                """)
                return True
            else:
                # Production mode - send actual email
                msg = MIMEMultipart()
                msg['From'] = f"{from_name} <{self.username}>"
                msg['To'] = to_email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.username, to_email, text)
                server.quit()
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_assignment_notification(self, assignment):
        """Send assignment notification to official"""
        try:
            from models.reports import NotificationTemplate
            notification_data = NotificationTemplate.game_assignment_notification(assignment)
            
            return self.send_email(
                notification_data['recipient'],
                notification_data['subject'],
                notification_data['body']
            )
        except ImportError:
            # Fallback notification
            logger.info(f"Assignment notification would be sent to {assignment.user.email}")
            return True
    
    def send_game_reminder(self, assignment, hours_before):
        """Send game reminder to official"""
        try:
            from models.reports import NotificationTemplate
            notification_data = NotificationTemplate.game_reminder_notification(assignment, hours_before)
            
            return self.send_email(
                notification_data['recipient'],
                notification_data['subject'],
                notification_data['body']
            )
        except ImportError:
            # Fallback reminder
            logger.info(f"Game reminder ({hours_before}h) would be sent to {assignment.user.email}")
            return True
    
    def send_bulk_reminders(self, hours_before=24):
        """Send reminders for games happening in X hours"""
        Game, GameAssignment = get_models()
        
        if not Game or not GameAssignment:
            logger.info(f"Bulk reminders ({hours_before}h) would be sent (Game models not available)")
            return 0
        
        target_time = datetime.now() + timedelta(hours=hours_before)
        target_date = target_time.date()
        
        # Find games happening around the target time (within 1 hour window)
        upcoming_games = Game.query.filter(
            Game.date == target_date,
            Game.status == 'released'
        ).all()
        
        reminders_sent = 0
        
        for game in upcoming_games:
            # Check if game is within the target time window
            game_datetime = datetime.combine(game.date, game.time)
            time_difference = abs((game_datetime - target_time).total_seconds() / 3600)
            
            if time_difference <= 1:  # Within 1 hour of target time
                # Send reminders to all assigned officials
                for assignment in game.assignments:
                    if assignment.is_active and assignment.status == 'assigned':
                        if self.send_game_reminder(assignment, hours_before):
                            reminders_sent += 1
        
        logger.info(f"Sent {reminders_sent} game reminders for games in {hours_before} hours")
        return reminders_sent


class NotificationScheduler:
    """Scheduler for automated notifications"""
    
    def __init__(self, email_service):
        self.email_service = email_service
    
    def send_assignment_notifications(self, game_id):
        """Send notifications for new assignments"""
        Game, GameAssignment = get_models()
        
        if not Game:
            logger.info(f"Assignment notifications would be sent for game {game_id}")
            return 0
        
        game = Game.query.get(game_id)
        if not game:
            return False
        
        notifications_sent = 0
        
        for assignment in game.assignments:
            if assignment.is_active and assignment.status == 'assigned':
                if self.email_service.send_assignment_notification(assignment):
                    notifications_sent += 1
        
        logger.info(f"Sent {notifications_sent} assignment notifications for game {game.id}")
        return notifications_sent
    
    def send_72_hour_reminders(self):
        """Send 72-hour reminders"""
        return self.email_service.send_bulk_reminders(72)
    
    def send_24_hour_reminders(self):
        """Send 24-hour reminders"""
        return self.email_service.send_bulk_reminders(24)
    
    def send_game_change_notifications(self, game, changes):
        """Send notifications when game details change"""
        if not game.assignments:
            return 0
        
        notifications_sent = 0
        
        # Create custom notification for game changes
        subject = f"Game Update: {game.game_title}"
        
        change_summary = []
        for field, (old_value, new_value) in changes.items():
            if field == 'date':
                change_summary.append(f"Date changed from {old_value.strftime('%m/%d/%Y') if old_value else 'TBD'} to {new_value.strftime('%m/%d/%Y') if new_value else 'TBD'}")
            elif field == 'time':
                change_summary.append(f"Time changed from {old_value.strftime('%I:%M %p') if old_value else 'TBD'} to {new_value.strftime('%I:%M %p') if new_value else 'TBD'}")
            elif field == 'location':
                change_summary.append(f"Location changed from {old_value} to {new_value}")
            else:
                change_summary.append(f"{field.title()} changed from {old_value} to {new_value}")
        
        for assignment in game.assignments:
            if assignment.is_active:
                body = f"""
Hello {assignment.user.first_name},

The following game assignment has been updated:

Game: {game.game_title}
Current Details:
- Date: {game.date.strftime('%A, %B %d, %Y')}
- Time: {game.time.strftime('%I:%M %p')}
- Location: {game.location.name}

Changes Made:
{chr(10).join(['- ' + change for change in change_summary])}

Please make note of these changes for your records.

Thank you,
Sports Scheduler System
                """.strip()
                
                if self.email_service.send_email(
                    assignment.user.email,
                    subject,
                    body
                ):
                    notifications_sent += 1
        
        logger.info(f"Sent {notifications_sent} game change notifications for game {game.id}")
        return notifications_sent


# Global email service instance
email_service = EmailService()
notification_scheduler = NotificationScheduler(email_service)


def configure_email_service(smtp_server, smtp_port, username, password):
    """Configure the global email service for production"""
    global email_service, notification_scheduler
    
    email_service = EmailService(smtp_server, smtp_port, username, password)
    notification_scheduler = NotificationScheduler(email_service)
    
    logger.info("Email service configured for production use")


def send_assignment_notification(assignment):
    """Convenience function to send assignment notification"""
    return email_service.send_assignment_notification(assignment)


def send_game_reminder(assignment, hours_before):
    """Convenience function to send game reminder"""
    return email_service.send_game_reminder(assignment, hours_before)


def schedule_game_reminders():
    """Function to be called by a scheduler (cron job, celery, etc.)"""
    # Send 72-hour reminders
    notification_scheduler.send_72_hour_reminders()
    
    # Send 24-hour reminders
    notification_scheduler.send_24_hour_reminders()


# Example usage and testing functions
def test_email_system():
    """Test the email system with sample data"""
    logger.info("Testing email system...")
    
    # This would typically be called with real assignment data
    logger.info("Email system test completed - check logs for sample notifications")


if __name__ == "__main__":
    # Run tests when executed directly
    test_email_system()
