from models.database import db
from datetime import datetime

class LocalUserList(db.Model):
    """Local user list for administrators"""
    
    __tablename__ = 'local_user_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Metadata
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships - FIXED with explicit foreign_keys and NO backrefs
    admin = db.relationship('User', foreign_keys=[admin_id])
    user = db.relationship('User', foreign_keys=[user_id])
    added_by_user = db.relationship('User', foreign_keys=[added_by])
    
    __table_args__ = (
        db.UniqueConstraint('admin_id', 'user_id', name='unique_admin_user'),
    )
    
    def __repr__(self):
        return f'<LocalUserList Admin:{self.admin_id} User:{self.user_id}>'