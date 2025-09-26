# models/reports.py - Financial and Reporting Models
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import relationship
from models.database import db

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

# Invoice and Paysheet Models (moved outside NotificationTemplate class)
class Invoice(db.Model):
    """Invoice model for league billing"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Invoice details
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    billing_recipient = db.Column(db.String(200), nullable=False)
    billing_address = db.Column(db.Text)
    
    # Date information
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Financial information
    subtotal = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid, overdue
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    league = relationship("League", backref="invoices")
    creator = relationship("User", backref="created_invoices")
    invoice_items = relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date and self.invoice_date:
            self.due_date = self.invoice_date + timedelta(days=30)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        today = date.today()
        prefix = f"INV-{today.year}{today.month:02d}"
        last_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        self.subtotal = sum(item.total_amount for item in self.invoice_items)
        self.total_amount = self.subtotal
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == 'sent' and self.due_date < date.today()

class InvoiceItem(db.Model):
    """Individual items on an invoice"""
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_total()
    
    def calculate_total(self):
        """Calculate total amount"""
        self.total_amount = (self.quantity or 0) * (self.unit_price or 0)

class Paysheet(db.Model):
    """Paysheet model for official payments"""
    __tablename__ = 'paysheets'
    
    id = db.Column(db.Integer, primary_key=True)
    paysheet_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Paysheet details
    official_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Date information
    paysheet_date = db.Column(db.Date, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Financial information
    gross_earnings = db.Column(db.Float, default=0.0)
    total_additions = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    net_pay = db.Column(db.Float, default=0.0)
    
    # Filter criteria used to generate this paysheet
    league_filter = db.Column(db.String(200))  # "ALL" or comma-separated league IDs
    level_filter = db.Column(db.String(200))   # "ALL" or comma-separated levels
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, approved, paid
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    official = relationship("User", backref="paysheets", foreign_keys=[official_id])
    creator = relationship("User", backref="created_paysheets", foreign_keys=[created_by])
    game_payments = relationship("GamePayment", backref="paysheet", cascade="all, delete-orphan")
    paysheet_adjustments = relationship("PaysheetAdjustment", backref="paysheet", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.paysheet_number:
            self.paysheet_number = self.generate_paysheet_number()
    
    def generate_paysheet_number(self):
        """Generate unique paysheet number"""
        today = date.today()
        prefix = f"PAY-{today.year}{today.month:02d}"
        last_paysheet = Paysheet.query.filter(
            Paysheet.paysheet_number.like(f"{prefix}%")
        ).order_by(Paysheet.paysheet_number.desc()).first()
        
        if last_paysheet:
            try:
                last_num = int(last_paysheet.paysheet_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def calculate_totals(self):
        """Calculate paysheet totals"""
        self.gross_earnings = sum(payment.amount for payment in self.game_payments)
        self.total_additions = sum(
            adj.amount for adj in self.paysheet_adjustments 
            if adj.adjustment_type == 'addition'
        )
        self.total_deductions = sum(
            adj.amount for adj in self.paysheet_adjustments 
            if adj.adjustment_type == 'deduction'
        )
        self.net_pay = self.gross_earnings + self.total_additions - self.total_deductions

class GamePayment(db.Model):
    """Individual game payments on a paysheet"""
    __tablename__ = 'game_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    paysheet_id = db.Column(db.Integer, db.ForeignKey('paysheets.id'), nullable=False)
    
    game_date = db.Column(db.Date, nullable=False)
    game_description = db.Column(db.String(500))
    league_name = db.Column(db.String(200))
    level = db.Column(db.String(50))
    position = db.Column(db.String(100))  # Referee, Umpire, etc.
    amount = db.Column(db.Float, nullable=False)

class PaysheetAdjustment(db.Model):
    """Additions and deductions on paysheets"""
    __tablename__ = 'paysheet_adjustments'
    
    id = db.Column(db.Integer, primary_key=True)
    paysheet_id = db.Column(db.Integer, db.ForeignKey('paysheets.id'), nullable=False)
    
    adjustment_type = db.Column(db.String(20), nullable=False)  # 'addition' or 'deduction'
    description = db.Column(db.String(500), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))  # 'bonus', 'travel', 'tax', 'equipment', etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    creator = relationship("User", backref="created_adjustments")