# models/league.py - League and Location Models (FINAL CIRCULAR DEPENDENCY FIX)
from models.database import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class League(db.Model):
    """League model for organizing games by sport/level"""
    
    __tablename__ = 'leagues'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)  # e.g., High School, College, 11U
    
    # Financial settings
    game_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    billing_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    billing_recipient = db.Column(db.String(100))  # Who gets billed
    default_officials_count = db.Column(db.Integer, default=2, nullable=False)
    default_scheduling_fee = db.Column(db.Numeric(10, 2), default=0.00)
    
    #League creator tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - SAFE IMPLEMENTATION (NO CIRCULAR DEPENDENCIES)
    memberships = db.relationship('LeagueMembership', lazy=True, cascade='all, delete-orphan')
    # NOTE: Game relationship is handled dynamically to prevent circular imports
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'level', name='unique_league_level'),
    )
    
    @property
    def full_name(self):
        """Get full league name with level"""
        return f"{self.name} - {self.level}"
    
    @property
    def active_members_count(self):
        """Count of active league members"""
        return LeagueMembership.query.filter_by(
            league_id=self.id, 
            is_active=True
        ).count()
    
    @property
    def games_count(self):
        """Count of games in this league - safe circular-dependency-free implementation"""
        try:
            # Try to import and query Game model if it exists
            from models.game import Game
            return Game.query.filter_by(league_id=self.id).count()
        except ImportError:
            # Graceful fallback when Game model doesn't exist
            return 0
    
    @property
    def games(self):
        """Get games for this league - safe implementation"""
        try:
            # Try to import and query Game model if it exists
            from models.game import Game
            return Game.query.filter_by(league_id=self.id).all()
        except ImportError:
            # Graceful fallback when Game model doesn't exist
            return []
    
    def to_dict(self):
        """Convert league to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'full_name': self.full_name,
            'game_fee': float(self.game_fee),
            'billing_amount': float(self.billing_amount),
            'billing_recipient': self.billing_recipient,
            # ADD THESE TWO LINES:
            'default_officials_count': self.default_officials_count,
            'default_scheduling_fee': float(self.default_scheduling_fee),
            'is_active': self.is_active,
            'description': self.description,
            'active_members': self.active_members_count,
            'games_count': self.games_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def create_default_assignment_slots(self, game):
        """Create default assignment slots for a new game."""
        try:
            from models.assignment import Assignment
        
            slots_created = []
            for i in range(self.default_officials_count):
                slot = Assignment(
                    game_id=game.id,
                    status='unassigned',
                    position=f"Official {i + 1}" if self.default_officials_count > 1 else "Official"
                )
                db.session.add(slot)
                slots_created.append(slot)
        
            return slots_created
        except ImportError:
            return []  # Graceful fallback

    def __repr__(self):
        return f'<League {self.full_name}>'

class Location(db.Model):
    """Master location database for game venues"""
    
    __tablename__ = 'locations'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    place_id = db.Column(db.String(255))
    
    # Contact information
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    
    # Facility details
    field_count = db.Column(db.Integer, default=1)
    field_names = db.Column(db.Text)  # JSON or comma-separated list
    notes = db.Column(db.Text)
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # NOTE: Game relationship handled dynamically to prevent circular imports
    
    @property
    def full_address(self):
        """Get complete address"""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ', '.join(filter(None, parts))
    
    @property
    def games_count(self):
        """Count of games at this location - safe implementation"""
        try:
            # Try to import and query Game model if it exists
            from models.game import Game
            return Game.query.filter_by(location_id=self.id).count()
        except ImportError:
            # Graceful fallback when Game model doesn't exist
            return 0
    
    @property
    def games(self):
        """Get games at this location - safe implementation"""
        try:
            # Try to import and query Game model if it exists
            from models.game import Game
            return Game.query.filter_by(location_id=self.id).all()
        except ImportError:
            # Graceful fallback when Game model doesn't exist
            return []
    
    @property
    def google_maps_link(self):
        """Generate Google Maps link"""
        if self.full_address:
            return f"https://www.google.com/maps/search/?api=1&query={self.full_address.replace(' ', '+')}"
        return None
    
    def to_dict(self):
        """Convert location to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'full_address': self.full_address,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'field_count': self.field_count,
            'field_names': self.field_names,
            'notes': self.notes,
            'is_active': self.is_active,
            'games_count': self.games_count,
            'google_maps_link': self.google_maps_link
        }
    
    def __repr__(self):
        return f'<Location {self.name}>'

class LeagueMembership(db.Model):
    """League membership for users - many-to-many relationship"""
    
    __tablename__ = 'league_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    
    # Membership details (EXISTING)
    role_in_league = db.Column(db.String(50), default='official')
    ranking = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    permission_level = db.Column(db.String(20), default='admin')  
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    removed_at = db.Column(db.DateTime)                          
    
    # Timestamps (EXISTING)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (EXISTING + NEW)
    user = db.relationship('User', foreign_keys=[user_id])
    league = db.relationship('League', foreign_keys=[league_id])
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by])
    removed_by_user = db.relationship('User', foreign_keys=[removed_by])
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('user_id', 'league_id', name='unique_user_league'),
    )
    
    def __repr__(self):
        return f'<LeagueMembership User:{self.user_id} League:{self.league_id} Role:{self.role_in_league}>'
