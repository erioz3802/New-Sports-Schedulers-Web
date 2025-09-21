"""
Sports Scheduler - Automated Reminder System
Created: September 20, 2025
Purpose: Handle automated 72-hour and 24-hour game reminders

This module provides automated notification scheduling for:
- 72-hour game reminders
- 24-hour game reminders  
- Assignment confirmations
- Game change notifications
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from flask import current_app

# Import models - ensure proper app context
def get_models():
    """Import models within app context to avoid circular imports"""
    from models.game import Game, GameAssignment
    from models.database import User, db
    return Game, GameAssignment, User, db

# Import email service
from utils.email_service_enhanced import send_game_reminder, send_assignment_notification

class ReminderScheduler:
    """
    Automated reminder system for game notifications
    
    Features:
    - 72-hour advance game reminders
    - 24-hour advance game reminders
    - Batch processing for efficiency
    - Error handling and logging
    - Status tracking to prevent duplicates
    """
    
    @staticmethod
    def check_72_hour_reminders() -> int:
        """
        Check for games needing 72-hour reminders
        
        Returns:
            int: Number of reminders sent
        """
        Game, Assignment, User, db = get_models()
        
        # Calculate target time range (72 hours from now, +/- 1 hour buffer)
        target_time = datetime.now() + timedelta(hours=72)
        start_time = target_time - timedelta(hours=1)
        end_time = target_time + timedelta(hours=1)
        
        try:
            # Find games needing 72-hour reminders
            games_needing_reminders = Game.query.filter(
                Game.date_time.between(start_time, end_time),
                Game.reminder_72h_sent == False,
                Game.status == 'Released'  # Only released games get reminders
            ).all()
            
            logging.info(f"Found {len(games_needing_reminders)} games needing 72-hour reminders")
            
            reminders_sent = 0
            for game in games_needing_reminders:
                if ReminderScheduler._send_game_reminders(game, '72_hour'):
                    game.reminder_72h_sent = True
                    reminders_sent += 1
                    
            # Commit all status updates
            db.session.commit()
            
            logging.info(f"Successfully sent {reminders_sent} 72-hour reminders")
            return reminders_sent
            
        except Exception as e:
            logging.error(f"Error in check_72_hour_reminders: {e}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def check_24_hour_reminders() -> int:
        """
        Check for games needing 24-hour reminders
        
        Returns:
            int: Number of reminders sent
        """
        Game, Assignment, User, db = get_models()
        
        # Calculate target time range (24 hours from now, +/- 1 hour buffer)
        target_time = datetime.now() + timedelta(hours=24)
        start_time = target_time - timedelta(hours=1)
        end_time = target_time + timedelta(hours=1)
        
        try:
            # Find games needing 24-hour reminders
            games_needing_reminders = Game.query.filter(
                Game.date_time.between(start_time, end_time),
                Game.reminder_24h_sent == False,
                Game.status == 'Released'  # Only released games get reminders
            ).all()
            
            logging.info(f"Found {len(games_needing_reminders)} games needing 24-hour reminders")
            
            reminders_sent = 0
            for game in games_needing_reminders:
                if ReminderScheduler._send_game_reminders(game, '24_hour'):
                    game.reminder_24h_sent = True
                    reminders_sent += 1
                    
            # Commit all status updates
            db.session.commit()
            
            logging.info(f"Successfully sent {reminders_sent} 24-hour reminders")
            return reminders_sent
            
        except Exception as e:
            logging.error(f"Error in check_24_hour_reminders: {e}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def _send_game_reminders(game, reminder_type: str) -> bool:
        """
        Send reminders to all assigned officials for a specific game
        
        Args:
            game: Game object
            reminder_type: '72_hour' or '24_hour'
            
        Returns:
            bool: True if all reminders sent successfully
        """
        Game, GameAssignment, User, db = get_models()
        
        try:
            # Get all assigned officials for this game
            assignments = GameAssignment.query.filter_by(
                game_id=game.id,
                status='assigned'  # Note: existing system uses 'assigned' not 'Assigned'
            ).all()
            
            if not assignments:
                logging.warning(f"No assigned officials found for game {game.id}")
                return True  # No assignments is not an error
            
            # Send reminder to each assigned official
            successful_sends = 0
            for assignment in assignments:
                try:
                    # Prepare game details for email
                    game_details = {
                        'game_id': game.id,
                        'date': game.date.strftime('%Y-%m-%d') if game.date else 'TBD',
                        'time': game.time.strftime('%H:%M') if game.time else 'TBD',
                        'location_name': game.location.name if game.location else 'TBD',
                        'location_address': getattr(game.location, 'address', '') if game.location else '',
                        'league_name': game.league.name if game.league else 'Unknown League',
                        'level': game.level or 'Not specified',
                        'field': getattr(game, 'field_name', '') or '',  # field_name based on knowledge base
                        'notes': game.notes or '',
                        'reminder_type': reminder_type,
                        'hours_until_game': 72 if reminder_type == '72_hour' else 24
                    }
                    
                    # Get partner information
                    partners = Assignment.query.filter(
                        Assignment.game_id == game.id,
                        Assignment.official_id != assignment.official_id,
                        Assignment.status == 'Assigned'
                    ).all()
                    
                    partner_info = []
                    for partner_assignment in partners:
                        partner_info.append({
                            'name': f"{partner_assignment.official.first_name} {partner_assignment.official.last_name}",
                            'email': partner_assignment.official.email,
                            'phone': getattr(partner_assignment.official, 'phone', 'Not provided')
                        })
                    
                    game_details['partners'] = partner_info
                    
                    # Send the reminder email
                    if send_game_reminder(assignment.official.email, game_details):
                        successful_sends += 1
                        logging.info(f"Sent {reminder_type} reminder to {assignment.official.email} for game {game.id}")
                    else:
                        logging.warning(f"Failed to send {reminder_type} reminder to {assignment.official.email}")
                        
                except Exception as e:
                    logging.error(f"Error sending {reminder_type} reminder to official {assignment.official_id}: {e}")
                    continue
            
            # Consider successful if at least one reminder was sent
            success = successful_sends > 0 or len(assignments) == 0
            
            if success:
                logging.info(f"Successfully sent {successful_sends}/{len(assignments)} {reminder_type} reminders for game {game.id}")
            else:
                logging.error(f"Failed to send any {reminder_type} reminders for game {game.id}")
                
            return success
            
        except Exception as e:
            logging.error(f"Error in _send_game_reminders for game {game.id}: {e}")
            return False
    
    @staticmethod
    def send_assignment_change_notification(game, officials_affected: List, change_type: str):
        """
        Send notifications when game assignments change
        
        Args:
            game: Game object
            officials_affected: List of User objects affected by the change
            change_type: 'assigned', 'unassigned', 'game_changed', 'cancelled'
        """
        try:
            for official in officials_affected:
                game_details = {
                    'game_id': game.id,
                    'date': game.date.strftime('%Y-%m-%d') if game.date else 'TBD',
                    'time': game.time.strftime('%H:%M') if game.time else 'TBD',
                    'location_name': game.location.name if game.location else 'TBD',
                    'league_name': game.league.name if game.league else 'Unknown League',
                    'change_type': change_type,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Send appropriate notification based on change type
                if change_type == 'assigned':
                    send_assignment_notification(official.email, game_details)
                elif change_type in ['unassigned', 'game_changed', 'cancelled']:
                    # Use existing email service for game changes
                    from utils.email_service import send_game_change_notification
                    send_game_change_notification(official.email, game_details)
                    
                logging.info(f"Sent {change_type} notification to {official.email} for game {game.id}")
                
        except Exception as e:
            logging.error(f"Error sending assignment change notifications: {e}")
    
    @staticmethod
    def process_daily_reminders():
        """
        Process all daily reminder tasks
        
        This method should be called by a cron job or background task scheduler
        """
        logging.info("Starting daily reminder processing")
        
        try:
            # Check 72-hour reminders
            reminders_72h = ReminderScheduler.check_72_hour_reminders()
            
            # Check 24-hour reminders  
            reminders_24h = ReminderScheduler.check_24_hour_reminders()
            
            logging.info(f"Daily reminder processing complete: {reminders_72h} 72-hour reminders, {reminders_24h} 24-hour reminders")
            
            return {
                'status': 'success',
                'reminders_72h': reminders_72h,
                'reminders_24h': reminders_24h,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error in daily reminder processing: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    def get_upcoming_games(hours_ahead: int = 168) -> List:
        """
        Get list of upcoming games for monitoring
        
        Args:
            hours_ahead: How many hours ahead to look (default: 1 week)
            
        Returns:
            List of upcoming games with reminder status
        """
        Game, Assignment, User, db = get_models()
        
        try:
            end_time = datetime.now() + timedelta(hours=hours_ahead)
            
            upcoming_games = Game.query.filter(
                Game.date_time.between(datetime.now(), end_time),
                Game.status.in_(['Ready', 'Released'])
            ).order_by(Game.date_time).all()
            
            games_info = []
            for game in upcoming_games:
                games_info.append({
                    'id': game.id,
                    'date_time': game.date_time.isoformat() if game.date_time else None,
                    'league': game.league.name if game.league else 'Unknown',
                    'location': game.location.name if game.location else 'TBD',
                    'status': game.status,
                    'reminder_72h_sent': getattr(game, 'reminder_72h_sent', False),
                    'reminder_24h_sent': getattr(game, 'reminder_24h_sent', False),
                    'assigned_officials': len(game.assignments) if hasattr(game, 'assignments') else 0
                })
            
            return games_info
            
        except Exception as e:
            logging.error(f"Error getting upcoming games: {e}")
            return []

# Utility functions for cron job integration
def run_daily_reminders():
    """
    Standalone function for cron job execution
    
    Usage:
        python -c "from utils.scheduler import run_daily_reminders; run_daily_reminders()"
    """
    from app import app
    
    with app.app_context():
        result = ReminderScheduler.process_daily_reminders()
        print(f"Daily reminders result: {result}")
        return result

def run_72_hour_check():
    """
    Standalone function for 72-hour reminder check
    """
    from app import app
    
    with app.app_context():
        count = ReminderScheduler.check_72_hour_reminders()
        print(f"72-hour reminders sent: {count}")
        return count

def run_24_hour_check():
    """
    Standalone function for 24-hour reminder check
    """
    from app import app
    
    with app.app_context():
        count = ReminderScheduler.check_24_hour_reminders()
        print(f"24-hour reminders sent: {count}")
        return count