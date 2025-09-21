# models/league.py - League and Location Models
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
    
    # Relationships
    games = db.relationship('Game', back_populates='league', lazy=True, cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'level', name='unique_league_level'),
    )
    
    @property
    def full_name(self):
        """Get full league name with level"""
        return f"{self.name} - {self.level}"
    
    @property
    def games_count(self):
        """Count of games in this league"""
        return len(self.games)
    
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
    
    # Location details
    field_count = db.Column(db.Integer, default=1)
    field_names = db.Column(db.Text)  # JSON string of field names
    notes = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    games = db.relationship('Game', back_populates='location', lazy=True)
    
    @property
    def full_address(self):
        """Get complete address"""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ', '.join([part for part in parts if part])
    
    @property
    def games_count(self):
        """Count of games at this location"""
        return len(self.games)
    
    def to_dict(self):
        """Convert location to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'full_address': self.full_address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'field_count': self.field_count,
            'field_names': self.field_names,
            'notes': self.notes,
            'is_active': self.is_active,
            'games_count': self.games_count
        }
    
    def __repr__(self):
        return f'<Location {self.name}>'