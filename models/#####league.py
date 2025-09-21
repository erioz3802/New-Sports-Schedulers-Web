# models/league.py - League and Location Models (FIXED - No Game dependency)
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
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # NOTE: Game relationship will be added when Game model is created in Phase 4
    # games = db.relationship('Game', backref='league', lazy=True, cascade='all, delete-orphan')
    memberships = db.relationship('LeagueMembership', backref='league', lazy=True, cascade='all, delete-orphan')
    
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
        """Count of games in this league - placeholder until Game model exists"""
        # TODO: Replace with actual count when Game model is added
        return 0
    
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
            'is_active': self.is_active,
            'description': self.description,
            'active_members': self.active_members_count,
            'games_count': self.games_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
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
    
    # NOTE: Game relationship will be added when Game model is created in Phase 4
    # games = db.relationship('Game', backref='location', lazy=True)
    
    @property
    def full_address(self):
        """Get complete address"""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ', '.join(filter(None, parts))
    
    @property
    def games_count(self):
        """Count of games at this location - placeholder until Game model exists"""
        # TODO: Replace with actual count when Game model is added
        return 0
    
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
    
    # Membership details
    role_in_league = db.Column(db.String(50), default='official')  # admin, assigner, official
    ranking = db.Column(db.Integer)  # 1-5 ranking within league
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='league_memberships')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'league_id', name='unique_user_league'),
    )
    
    def __repr__(self):
        return f'<LeagueMembership User:{self.user_id} League:{self.league_id}>'
