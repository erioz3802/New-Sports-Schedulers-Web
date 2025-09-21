# models/availability.py - Official Availability System
from models.database import db
from datetime import datetime, date, time, timedelta
from sqlalchemy import UniqueConstraint

class OfficialAvailability(db.Model):
    """Track official availability for scheduling"""
    
    __tablename__ = 'official_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Availability types: 'unavailable_all_day', 'unavailable_hours', 'available'
    availability_type = db.Column(db.String(20), nullable=False, default='available')
    
    # Date range
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Time range (for partial day unavailability)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    
    # Reason for unavailability
    reason = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    # Recurring availability (for future enhancement)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_pattern = db.Column(db.String(50))  # 'weekly', 'monthly', etc.
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='availability_records')
    
    def __repr__(self):
        return f'<OfficialAvailability {self.user_id}: {self.start_date} - {self.end_date}>'
    
    @classmethod
    def is_user_available(cls, user_id, check_date, check_time=None):
        """Check if user is available on a specific date/time"""
        
        # Get all availability records for the user on the given date
        records = cls.query.filter(
            cls.user_id == user_id,
            cls.is_active == True,
            cls.start_date <= check_date,
            cls.end_date >= check_date
        ).all()
        
        # If no records, user is available (default available)
        if not records:
            return True
        
        for record in records:
            if record.availability_type == 'unavailable_all_day':
                return False
            
            elif record.availability_type == 'unavailable_hours' and check_time:
                # Check if the time falls within unavailable hours
                if record.start_time and record.end_time:
                    if record.start_time <= check_time <= record.end_time:
                        return False
        
        return True
    
    @classmethod
    def get_user_conflicts(cls, user_id, start_datetime, end_datetime):
        """Get availability conflicts for a user in a date/time range"""
        conflicts = []
        
        start_date = start_datetime.date()
        end_date = end_datetime.date()
        start_time = start_datetime.time()
        end_time = end_datetime.time()
        
        # Check each date in the range
        current_date = start_date
        while current_date <= end_date:
            if not cls.is_user_available(user_id, current_date, start_time):
                # Find the specific conflict record
                conflict_records = cls.query.filter(
                    cls.user_id == user_id,
                    cls.is_active == True,
                    cls.start_date <= current_date,
                    cls.end_date >= current_date,
                    cls.availability_type.in_(['unavailable_all_day', 'unavailable_hours'])
                ).all()
                
                for record in conflict_records:
                    if (record.availability_type == 'unavailable_all_day' or
                        (record.availability_type == 'unavailable_hours' and 
                         record.start_time and record.end_time and
                         not (end_time <= record.start_time or start_time >= record.end_time))):
                        
                        conflicts.append({
                            'date': current_date,
                            'type': record.availability_type,
                            'reason': record.reason,
                            'time_range': f"{record.start_time} - {record.end_time}" if record.start_time else "All day"
                        })
            
            current_date += timedelta(days=1)
        
        return conflicts
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'availability_type': self.availability_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'reason': self.reason,
            'notes': self.notes,
            'is_recurring': self.is_recurring,
            'recurring_pattern': self.recurring_pattern,
            'is_active': self.is_active
        }


class OfficialRanking(db.Model):
    """Track official rankings within leagues"""
    
    __tablename__ = 'official_rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    
    # Ranking (1-5, where 5 is highest)
    ranking = db.Column(db.Integer, nullable=False, default=3)
    
    # Preferences and certifications
    preferred_positions = db.Column(db.Text)  # JSON string of positions
    certifications = db.Column(db.Text)  # JSON string of certifications
    
    # Experience tracking
    games_worked = db.Column(db.Integer, default=0)
    years_experience = db.Column(db.Integer, default=0)
    
    # Performance metrics (for future enhancement)
    average_rating = db.Column(db.Float)
    last_assignment_date = db.Column(db.Date)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='rankings')
    league = db.relationship('League', backref='official_rankings')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'league_id', name='unique_user_league_ranking'),
    )
    
    def __repr__(self):
        return f'<OfficialRanking User:{self.user_id} League:{self.league_id} Rank:{self.ranking}>'
    
    @classmethod
    def get_user_ranking(cls, user_id, league_id):
        """Get user's ranking in a specific league"""
        ranking = cls.query.filter_by(
            user_id=user_id,
            league_id=league_id,
            is_active=True
        ).first()
        
        return ranking.ranking if ranking else 3  # Default ranking
    
    @classmethod
    def get_ranked_officials(cls, league_id, limit=None):
        """Get officials ranked by their ranking in a league"""
        query = cls.query.filter_by(
            league_id=league_id,
            is_active=True
        ).join(User).filter(
            User.is_active == True
        ).order_by(cls.ranking.desc(), cls.games_worked.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update_games_worked(self):
        """Update the count of games worked"""
        from models.game import GameAssignment
        
        self.games_worked = GameAssignment.query.filter_by(
            user_id=self.user_id,
            is_active=True
        ).join(Game).filter(
            Game.league_id == self.league_id,
            Game.status == 'completed'
        ).count()
        
        # Update last assignment date
        last_assignment = GameAssignment.query.filter_by(
            user_id=self.user_id,
            is_active=True
        ).join(Game).filter(
            Game.league_id == self.league_id
        ).order_by(Game.date.desc()).first()
        
        if last_assignment:
            self.last_assignment_date = last_assignment.game.date
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'league_id': self.league_id,
            'ranking': self.ranking,
            'preferred_positions': self.preferred_positions,
            'certifications': self.certifications,
            'games_worked': self.games_worked,
            'years_experience': self.years_experience,
            'average_rating': self.average_rating,
            'last_assignment_date': self.last_assignment_date.isoformat() if self.last_assignment_date else None,
            'is_active': self.is_active
        }


def create_default_availability():
    """Create default availability records (all users available by default)"""
    from models.database import User
    
    # This function can be called to initialize availability records
    # In this implementation, we assume users are available unless specified otherwise
    print("Default availability: Users are available unless unavailability is explicitly set")


def get_assignment_conflicts(user_id, game_datetime, duration_minutes=120):
    """Check for assignment conflicts for a user at a specific time"""
    from models.game import Game, GameAssignment
    
    conflicts = []
    
    # Calculate time window (game time + buffer)
    buffer_time = timedelta(hours=2)
    game_start = game_datetime
    game_end = game_datetime + timedelta(minutes=duration_minutes)
    window_start = game_start - buffer_time
    window_end = game_end + buffer_time
    
    # Check for other game assignments in the time window
    conflicting_assignments = GameAssignment.query.filter(
        GameAssignment.user_id == user_id,
        GameAssignment.is_active == True
    ).join(Game).filter(
        Game.date == game_datetime.date(),
        Game.status.in_(['ready', 'released', 'completed'])
    ).all()
    
    for assignment in conflicting_assignments:
        other_game = assignment.game
        other_start = datetime.combine(other_game.date, other_game.time)
        other_end = other_start + timedelta(minutes=other_game.estimated_duration)
        
        # Check for overlap with buffer
        if not (window_end <= other_start or window_start >= other_end):
            conflicts.append({
                'type': 'game_assignment',
                'game': other_game,
                'assignment': assignment,
                'message': f'Already assigned to {other_game.game_title} at {other_game.time}'
            })
    
    # Check availability records
    availability_conflicts = OfficialAvailability.get_user_conflicts(
        user_id, game_start, game_end
    )
    
    for conflict in availability_conflicts:
        conflicts.append({
            'type': 'availability',
            'conflict': conflict,
            'message': f'Unavailable on {conflict["date"]}: {conflict["reason"] or "No reason given"}'
        })
    
    return conflicts

def get_assignment_conflicts(user_id, game_datetime, duration_minutes=120):
    """Check for assignment conflicts for a user at a specific date/time"""
    conflicts = []
    
    try:
        from models.game import Game, GameAssignment
        
        # Calculate game end time
        game_end = game_datetime + timedelta(minutes=duration_minutes)
        
        # Add 2-hour buffer
        buffer_start = game_datetime - timedelta(hours=2)
        buffer_end = game_end + timedelta(hours=2)
        
        # Check for existing game assignments in the time window
        existing_assignments = GameAssignment.query.filter(
            GameAssignment.user_id == user_id,
            GameAssignment.is_active == True
        ).join(Game).filter(
            Game.date == game_datetime.date()
        ).all()
        
        for assignment in existing_assignments:
            assigned_game = assignment.game
            assigned_start = datetime.combine(assigned_game.date, assigned_game.time)
            assigned_end = assigned_start + timedelta(minutes=assigned_game.estimated_duration or 120)
            
            # Check if times overlap (with buffer)
            if (buffer_start <= assigned_end and buffer_end >= assigned_start):
                conflicts.append({
                    'type': 'assignment_conflict',
                    'message': f'Already assigned to {assigned_game.game_title} at {assigned_game.time.strftime("%I:%M %p")}',
                    'conflicting_game': assigned_game,
                    'assignment': assignment
                })
        
        return conflicts
        
    except Exception as e:
        print(f"Error checking assignment conflicts: {e}")
        return []
