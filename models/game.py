# models/game.py - Game Model with Scheduling Logic
from models.database import db
from datetime import datetime, timedelta
from sqlalchemy import UniqueConstraint

class Game(db.Model):
    """Game model for scheduling and assignment"""
    
    __tablename__ = 'games'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Game details
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    field_name = db.Column(db.String(50))  # Which field at the location
    
    # Teams/Competition
    home_team = db.Column(db.String(100))
    away_team = db.Column(db.String(100))
    level = db.Column(db.String(50))  # Game level (can override league level)
    
    # Game status workflow
    status = db.Column(db.String(20), default='draft')  # draft, ready, released, completed, cancelled
    
    # Financial
    fee_per_official = db.Column(db.Numeric(10, 2))  # Can override league default
    
    # Additional information
    notes = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    
    # Timing
    estimated_duration = db.Column(db.Integer, default=120)  # minutes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    released_at = db.Column(db.DateTime)
    
    # Relationships
    assignments = db.relationship('GameAssignment', backref='game', lazy=True, cascade='all, delete-orphan')
    league = db.relationship('League')
    location = db.relationship('Location')

    #Rankings
    game_ranking = db.Column(db.Integer, default=3, nullable=True)
    ranking_notes = db.Column(db.Text, nullable=True)
    
    @property
    def datetime(self):
        """Combine date and time into datetime object"""
        return datetime.combine(self.date, self.time)
    
    @property
    def end_datetime(self):
        """Calculate estimated end time"""
        return self.datetime + timedelta(minutes=self.estimated_duration)
    
    @property
    def is_in_past(self):
        """Check if game is in the past"""
        return self.datetime < datetime.now()
    
    @property
    def can_be_edited(self):
        """Check if game can still be edited"""
        return self.status in ['draft', 'ready'] and not self.is_in_past
    
    @property
    def assigned_officials_count(self):
        """Count of assigned officials"""
        return GameAssignment.query.filter_by(game_id=self.id, is_active=True).count()
    
    def get_ranking_description(self):
        """Get human-readable ranking description"""
        rankings = {
            1: "Basic/Training Game",
            2: "Regular Season - Low Priority", 
            3: "Regular Season - Standard",
            4: "Important Game/Playoff",
            5: "Championship/High Priority"
        }
        return rankings.get(self.game_ranking or 3, "Standard")

    @property
    def game_title(self):
        """Generate game title"""
        if self.home_team and self.away_team:
            return f"{self.home_team} vs {self.away_team}"
        return f"Game #{self.id}"
    
    # Fixed check_conflicts method for models/game.py

    def check_conflicts(self, user_id=None):
        """
        Check for conflicts with this game
        Args:
            user_id: Optional - check conflicts for specific user
    
        Returns:
            List of conflict dictionaries with 'type' and 'message' keys
        """
        conflicts = []
        try:
            # Calculate game time window with 2-hour buffer
            from datetime import datetime, timedelta
    
            game_start = datetime.combine(self.date, self.time)
            game_end = game_start + timedelta(minutes=self.estimated_duration or 120)
    
            # 2-hour buffer before and after
            buffer_start = game_start - timedelta(hours=2)
            buffer_end = game_end + timedelta(hours=2)
    
            # Convert back to date and time for database queries
            buffer_start_time = buffer_start.time()
            buffer_end_time = buffer_end.time()
    
            # Check for location conflicts (same field at same time)
            # FIXED: Exclude cancelled games from conflict detection
            location_conflicts = Game.query.filter(
                Game.id != self.id,  # Exclude current game
                Game.date == self.date,
                Game.location_id == self.location_id,
                Game.field_name == self.field_name if self.field_name else True,
                Game.time >= buffer_start_time,
                Game.time <= buffer_end_time,
                Game.status != 'cancelled'  # ADD THIS LINE - exclude cancelled games
            ).all()
    
            if location_conflicts:
                for conflict_game in location_conflicts:
                    conflicts.append({
                        'type': 'location_conflict',
                        'message': f'Field conflict with game: {conflict_game.game_title} at {conflict_game.time.strftime("%I:%M %p")}',
                        'game': conflict_game
                    })
    
            # Check for official conflicts if user_id provided
            if user_id:
                # Get all assignments for this official on the same date
                from models.database import User
        
                official_assignments = GameAssignment.query.filter(
                    GameAssignment.user_id == user_id,
                    GameAssignment.is_active == True
                ).join(Game).filter(
                    Game.id != self.id,  # Exclude current game
                    Game.date == self.date,
                    Game.status != 'cancelled'  # ADD THIS LINE - exclude cancelled games
                ).all()
        
                for assignment in official_assignments:
                    assigned_game = assignment.game
                    assigned_start = datetime.combine(assigned_game.date, assigned_game.time)
                    assigned_end = assigned_start + timedelta(minutes=assigned_game.estimated_duration or 120)
            
                    # Check if times overlap (with buffer)
                    if (game_start <= assigned_end + timedelta(hours=2) and 
                        game_end >= assigned_start - timedelta(hours=2)):
                
                        user = User.query.get(user_id)
                        conflicts.append({
                            'type': 'official_conflict',
                            'message': f'{user.full_name} is already assigned to {assigned_game.game_title} at {assigned_game.time.strftime("%I:%M %p")}',
                            'assignment': assignment
                        })
    
            return conflicts
    
        except Exception as e:
            # Log error but don't crash - return empty conflicts list
            print(f"Error checking conflicts for game {self.id}: {str(e)}")
            return []
    
    def release(self):
        """Release game for official assignment"""
        if self.status == 'ready':
            self.status = 'released'
            self.released_at = datetime.utcnow()
            return True
        return False
    
    def to_dict(self):
        """Convert game to dictionary for API responses"""
        return {
            'id': self.id,
            'league_id': self.league_id,
            'location_id': self.location_id,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.strftime('%H:%M') if self.time else None,
            'datetime': self.datetime.isoformat() if self.datetime else None,
            'field_name': self.field_name,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'game_title': self.game_title,
            'level': self.level,
            'status': self.status,
            'fee_per_official': float(self.fee_per_official) if self.fee_per_official else None,
            'notes': self.notes,
            'special_instructions': self.special_instructions,
            'estimated_duration': self.estimated_duration,
            'assigned_officials': self.assigned_officials_count,
            'can_be_edited': self.can_be_edited,
            'is_in_past': self.is_in_past
        }
    
    def __repr__(self):
        return f'<Game {self.game_title} on {self.date}>'


class GameAssignment(db.Model):
    """Game assignment for officials"""
    
    __tablename__ = 'game_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Assignment details
    position = db.Column(db.String(50))  # referee, umpire, etc.
    assignment_type = db.Column(db.String(20), default='manual')  # manual, auto
    
    # Status tracking
    status = db.Column(db.String(20), default='assigned')  # assigned, accepted, declined
    is_active = db.Column(db.Boolean, default=True)
    
    # Response tracking
    response_date = db.Column(db.DateTime)
    decline_reason = db.Column(db.String(200))
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='game_assignments')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('game_id', 'user_id', name='unique_game_user_assignment'),
    )
    
    def accept(self):
        """Accept the assignment"""
        self.status = 'accepted'
        self.response_date = datetime.utcnow()
    
    def decline(self, reason=None):
        """Decline the assignment"""
        self.status = 'declined'
        self.response_date = datetime.utcnow()
        self.decline_reason = reason
    
    def __repr__(self):
        return f'<GameAssignment Game:{self.game_id} User:{self.user_id}>'