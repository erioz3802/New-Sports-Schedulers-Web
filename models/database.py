# models/database.py - Real SQLAlchemy Database Models (FIXED)
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# This will be initialized by the main app
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with SQLAlchemy database storage"""
    
    __tablename__ = 'users'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    
    # Role and status
    role = db.Column(db.String(20), nullable=False, default='official')
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Rankings
    default_ranking = db.Column(db.Integer, default=3, nullable=True)
    ranking_notes = db.Column(db.Text, nullable=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_superadmin(self):
        """Check if user is superadmin"""
        return self.role == 'superadmin'
    
    @property 
    def is_administrator(self):
        """Check if user is administrator or higher"""
        return self.role in ['superadmin', 'administrator']
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['superadmin', 'administrator']
    
    # ADD THIS NEW METHOD:
    def get_ranking_description(self):
        """Get human-readable ranking description"""
        rankings = {
            1: "Beginner Official",
            2: "Developing Official", 
            3: "Competent Official",
            4: "Experienced Official",
            5: "Expert Official"
        }
        return rankings.get(self.default_ranking or 3, "Competent")
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

def create_demo_users():
    """Create demo users if they don't exist"""
    # Check if users already exist
    if User.query.first():
        print("Users already exist in database")
        return
    
    # Create superadmin user
    admin_user = User(
        email='admin@sportsscheduler.com',
        first_name='Super',
        last_name='Admin',
        phone='555-0001',
        role='superadmin',
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    
    # Create demo official
    official_user = User(
        email='official@sportsscheduler.com',
        first_name='John',
        last_name='Official',
        phone='555-0002',
        role='official',
        is_active=True
    )
    official_user.set_password('official123')
    db.session.add(official_user)
    
    # Create demo administrator
    admin_demo = User(
        email='administrator@sportsscheduler.com',
        first_name='League',
        last_name='Administrator',
        phone='555-0003',
        role='administrator',
        is_active=True
    )
    admin_demo.set_password('admin123')
    db.session.add(admin_demo)
    
    # Create demo assigner
    assigner_user = User(
        email='assigner@sportsscheduler.com',
        first_name='Game',
        last_name='Assigner',
        phone='555-0004',
        role='assigner',
        is_active=True
    )
    assigner_user.set_password('assigner123')
    db.session.add(assigner_user)
    
    try:
        db.session.commit()
        print("✅ Demo users created successfully!")
        print("   Superadmin: admin@sportsscheduler.com / admin123")
        print("   Administrator: administrator@sportsscheduler.com / admin123")
        print("   Assigner: assigner@sportsscheduler.com / assigner123")
        print("   Official: official@sportsscheduler.com / official123")
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        db.session.rollback()