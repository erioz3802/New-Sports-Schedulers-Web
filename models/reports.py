# models/reports.py - Financial and Reporting Models
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

# Import models - avoiding circular imports
def get_db():
    """Get database instance - imported when needed"""
    from models.database import db
    return db

def get_models():
    """Get model classes - imported when needed"""
    from models.database import User
    # Note: Game, GameAssignment, League models will be imported when Phase 4 is integrated
    # For Phase 5, we'll use placeholder implementations
    return User

class FinancialReport:
    """Financial reporting utilities"""
    
    @staticmethod
    def get_official_earnings(user_id, start_date=None, end_date=None, league_id=None):
        """Get earnings for an official - placeholder for Phase 5"""
        # This will be fully implemented when Phase 4 Game models are integrated
        # For now, return demo data for testing
        return {
            'total_earnings': 450.00,
            'games_count': 15,
            'games_worked': [
                {
                    'date': date.today() - timedelta(days=7),
                    'time': datetime.now().time(),
                    'league': 'Demo Basketball League',
                    'game_title': 'Team A vs Team B',
                    'position': 'Referee',
                    'fee': 75.00
                },
                {
                    'date': date.today() - timedelta(days=14),
                    'time': datetime.now().time(),
                    'league': 'Demo Football League',
                    'game_title': 'Team C vs Team D',
                    'position': 'Umpire',
                    'fee': 50.00
                }
            ]
        }
    
    @staticmethod
    def get_league_financials(league_id, start_date=None, end_date=None):
        """Get financial summary for a league - placeholder for Phase 5"""
        return {
            'total_fees_paid': 1500.00,
            'total_billing': 3000.00,
            'profit_margin': 1500.00,
            'games_count': 20,
            'games_summary': [
                {
                    'date': date.today() - timedelta(days=3),
                    'game_title': 'Demo Game 1',
                    'officials_count': 2,
                    'fee_per_official': 75.00,
                    'total_cost': 150.00,
                    'billing_amount': 300.00
                }
            ]
        }
    
    @staticmethod
    def get_global_financials(start_date=None, end_date=None):
        """Get global financial summary across all leagues - placeholder for Phase 5"""
        return {
            'total_revenue': 10000.00,
            'total_costs': 6000.00,
            'total_profit': 4000.00,
            'league_summaries': [
                {
                    'league_id': 1,
                    'league_name': 'Demo Basketball',
                    'league_level': 'High School',
                    'games_count': 15,
                    'total_fees_paid': 2250.00,
                    'total_billing': 4500.00,
                    'profit': 2250.00
                }
            ]
        }


class GameReport:
    """Game reporting utilities"""
    
    @staticmethod
    def get_official_game_history(user_id, limit=50):
        """Get game history for an official - placeholder for Phase 5"""
        return [
            {
                'date': date.today() - timedelta(days=7),
                'time': datetime.now().time(),
                'league': 'Demo Basketball League',
                'game_title': 'Team A vs Team B',
                'position': 'Referee',
                'game_status': 'completed',
                'assignment_status': 'accepted',
                'fee': 75.00
            },
            {
                'date': date.today() - timedelta(days=14),
                'time': datetime.now().time(),
                'league': 'Demo Football League',
                'game_title': 'Team C vs Team D',
                'position': 'Umpire',
                'game_status': 'completed',
                'assignment_status': 'accepted',
                'fee': 50.00
            }
        ]
    
    @staticmethod
    def get_league_statistics(league_id):
        """Get comprehensive statistics for a league - placeholder for Phase 5"""
        return {
            'status_counts': {
                'draft': 2,
                'ready': 1,
                'released': 3,
                'completed': 15
            },
            'total_assignments': 45,
            'unique_officials': 12,
            'recent_games': [
                {
                    'date': date.today() - timedelta(days=2),
                    'game_title': 'Recent Game 1',
                    'status': 'completed',
                    'officials_count': 2
                },
                {
                    'date': date.today() - timedelta(days=5),
                    'game_title': 'Recent Game 2',
                    'status': 'released',
                    'officials_count': 2
                }
            ]
        }
    
    @staticmethod
    def get_workload_distribution(league_id, days_back=30):
        """Get workload distribution for officials in a league - placeholder for Phase 5"""
        return [
            {
                'user_id': 1,
                'name': 'John Official',
                'assignments': 8,
                'earnings': 600.00
            },
            {
                'user_id': 2,
                'name': 'Jane Referee',
                'assignments': 12,
                'earnings': 900.00
            },
            {
                'user_id': 3,
                'name': 'Mike Umpire',
                'assignments': 6,
                'earnings': 450.00
            }
        ]


class NotificationTemplate:
    """Email/SMS notification templates"""
    
    @staticmethod
    def game_assignment_notification(assignment):
        """Generate assignment notification content"""
        game = assignment.game
        official = assignment.user
        
        subject = f"Game Assignment: {game.game_title}"
        
        body = f"""
Hello {official.first_name},

You have been assigned to officiate the following game:

Game: {game.game_title}
Date: {game.date.strftime('%A, %B %d, %Y')}
Time: {game.time.strftime('%I:%M %p')}
Location: {game.location.name}
{f'Field: {game.field_name}' if game.field_name else ''}

League: {game.league.full_name}
{f'Position: {assignment.position}' if assignment.position else ''}
{f'Fee: ${game.fee_per_official or game.league.game_fee}' if game.fee_per_official or game.league.game_fee else ''}

{f'Special Instructions: {game.special_instructions}' if game.special_instructions else ''}

Please log in to the Sports Scheduler to accept or decline this assignment.

Thank you,
Sports Scheduler System
        """
        
        return {
            'subject': subject,
            'body': body.strip(),
            'recipient': official.email,
            'sms_body': f"Game Assignment: {game.game_title} on {game.date.strftime('%m/%d')} at {game.time.strftime('%I:%M %p')} - {game.location.name}. Please check Sports Scheduler."
        }
    
    @staticmethod
    def game_reminder_notification(assignment, hours_before):
        """Generate game reminder notification"""
        game = assignment.game
        official = assignment.user
        
        subject = f"Game Reminder: {game.game_title} in {hours_before} hours"
        
        body = f"""
Hello {official.first_name},

This is a reminder that you have a game assignment in {hours_before} hours:

Game: {game.game_title}
Date: {game.date.strftime('%A, %B %d, %Y')}
Time: {game.time.strftime('%I:%M %p')}
Location: {game.location.name}
{f'Field: {game.field_name}' if game.field_name else ''}

{f'Partners:' if len(game.assignments) > 1 else ''}
{''.join([f'- {a.user.full_name} ({a.user.phone or a.user.email})' for a in game.assignments if a.user_id != official.id and a.is_active]) if len(game.assignments) > 1 else ''}

Location Address: {game.location.full_address if game.location.full_address else 'See location details in system'}

{f'Special Instructions: {game.special_instructions}' if game.special_instructions else ''}

Safe travels and good luck!

Sports Scheduler System
        """
        
        return {
            'subject': subject,
            'body': body.strip(),
            'recipient': official.email,
            'sms_body': f"Reminder: {game.game_title} in {hours_before}hrs at {game.time.strftime('%I:%M %p')} - {game.location.name}"
        }
