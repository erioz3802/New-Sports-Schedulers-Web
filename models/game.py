# models/game.py - Enhanced Game Model with Bug Fixes and Improvements
from models.database import db
from datetime import datetime, timedelta, date
from sqlalchemy import UniqueConstraint, and_, or_
from sqlalchemy.orm import validates
import logging

# Configure logging for debugging
logger = logging.getLogger(__name__)

class Game(db.Model):
    """
    Game model for scheduling and assignment with enhanced error handling
    and conflict detection capabilities
    """
    
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
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Soft delete flag
    
    # Financial
    fee_per_official = db.Column(db.Numeric(10, 2))  # Can override league default
    
    # Additional information
    notes = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    
    # Timing
    estimated_duration = db.Column(db.Integer, default=120)  # minutes
    
    # Rankings
    game_ranking = db.Column(db.Integer, default=3, nullable=True)  # 1-5 scale
    ranking_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    released_at = db.Column(db.DateTime)
    status_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('GameAssignment', backref='game', lazy=True, 
                                cascade='all, delete-orphan')
    league = db.relationship('League', backref='games')
    location = db.relationship('Location', backref='games')
    
    # Validation methods
    @validates('status')
    def validate_status(self, key, status):
        """Validate status transitions"""
        valid_statuses = ['draft', 'ready', 'released', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('game_ranking')
    def validate_ranking(self, key, ranking):
        """Validate game ranking is within acceptable range"""
        if ranking is not None and (ranking < 1 or ranking > 5):
            raise ValueError("Game ranking must be between 1 and 5")
        return ranking
    
    @validates('estimated_duration')
    def validate_duration(self, key, duration):
        """Validate game duration is reasonable"""
        if duration is not None and (duration < 30 or duration > 480):  # 30 min to 8 hours
            raise ValueError("Game duration must be between 30 and 480 minutes")
        return duration or 120  # Default to 2 hours
    
    # Enhanced Property Methods
    @property
    def datetime(self):
        """Combine date and time into datetime object with error handling"""
        if self.date and self.time:
            try:
                return datetime.combine(self.date, self.time)
            except (TypeError, ValueError) as e:
                logger.error(f"Error combining date {self.date} and time {self.time}: {e}")
                return None
        return None
    
    @property
    def end_datetime(self):
        """Calculate estimated end time with error handling"""
        game_datetime = self.datetime
        if game_datetime and self.estimated_duration:
            try:
                return game_datetime + timedelta(minutes=self.estimated_duration)
            except (TypeError, ValueError) as e:
                logger.error(f"Error calculating end time: {e}")
                return None
        return None
    
    @property
    def is_in_past(self):
        """Check if game is in the past with error handling"""
        if not self.date:
            return False
        try:
            return self.date < date.today()
        except (TypeError, ValueError):
            return False
    
    @property
    def is_today_game(self):
        """Check if game is today with error handling"""
        if not self.date:
            return False
        try:
            return self.date == date.today()
        except (TypeError, ValueError):
            return False
    
    @property
    def is_future_game(self):
        """Check if game is in the future with error handling"""
        if not self.date:
            return False
        try:
            return self.date > date.today()
        except (TypeError, ValueError):
            return False
    
    @property
    def can_be_edited(self):
        """
        Enhanced editing rules:
        - All games can be edited regardless of date (per requirements)
        - But completed games have restricted editing
        """
        if not self.is_active:
            return False
        # Allow editing of all games except completed ones
        return self.status != 'completed'
    
    @property  
    def can_be_deleted(self):
        """
        Enhanced deletion rules:
        - Draft games with no assignments can be deleted
        - Other games should be cancelled instead
        """
        if not self.is_active or self.status == 'completed':
            return False
        
        # Check if game has any active assignments
        if self.assigned_officials_count > 0:
            return False
        
        # Only draft games with no assignments can be truly deleted
        return self.status == 'draft'
    
    @property
    def can_be_cancelled(self):
        """Check if game can be cancelled"""
        return self.is_active and self.status in ['draft', 'ready', 'released']
    
    @property
    def can_be_restored(self):
        """Check if cancelled game can be restored"""
        return self.is_active and self.status == 'cancelled'
    
    @property
    def assigned_officials_count(self):
        """Count of assigned officials with error handling"""
        try:
            return GameAssignment.query.filter_by(
                game_id=self.id, 
                is_active=True
            ).count()
        except Exception as e:
            logger.error(f"Error counting assigned officials for game {self.id}: {e}")
            return 0
    
    @property
    def game_title(self):
        """Generate game title with better formatting"""
        if self.home_team and self.away_team:
            return f"{self.home_team} vs {self.away_team}"
        elif self.home_team:
            return f"{self.home_team} (Game)"
        elif self.away_team:
            return f"vs {self.away_team} (Game)"
        else:
            return f"Game #{self.id}"
    
    @property
    def time_period_class(self):
        """CSS class based on game timing for template use"""
        if self.status == 'cancelled':
            return 'cancelled-game'
        elif self.is_in_past:
            return 'past-game'
        elif self.is_today_game:
            return 'today-game'
        else:
            return 'future-game'
    
    # Enhanced Methods
    def get_ranking_description(self):
        """Get human-readable ranking description with error handling"""
        rankings = {
            1: "Basic/Training Game",
            2: "Regular Season - Low Priority", 
            3: "Regular Season - Standard",
            4: "Important Game/Playoff",
            5: "Championship/High Priority"
        }
        try:
            return rankings.get(self.game_ranking or 3, "Standard Priority")
        except Exception:
            return "Standard Priority"
    
    def get_assigned_officials(self):
        """Get list of assigned officials with error handling"""
        try:
            return GameAssignment.query.filter_by(
                game_id=self.id, 
                is_active=True
            ).all()
        except Exception as e:
            logger.error(f"Error getting assigned officials for game {self.id}: {e}")
            return []
    
    def check_conflicts(self, user_id=None, check_location=True, check_officials=True):
        """
        Enhanced conflict detection with comprehensive error handling
        
        Args:
            user_id: Optional - check conflicts for specific user
            check_location: Whether to check location conflicts
            check_officials: Whether to check official conflicts
    
        Returns:
            List of conflict dictionaries with 'type', 'message', and additional data
        """
        conflicts = []
        
        # Input validation
        if not self.date or not self.time or not self.location_id:
            return conflicts
        
        try:
            # Calculate game time window with buffer
            game_start = self.datetime
            if not game_start:
                return conflicts
            
            game_end = game_start + timedelta(minutes=self.estimated_duration or 120)
            
            # 2-hour buffer before and after
            buffer_start = game_start - timedelta(hours=2)
            buffer_end = game_end + timedelta(hours=2)
            
            # Check location conflicts if requested
            if check_location:
                conflicts.extend(self._check_location_conflicts(buffer_start, buffer_end))
            
            # Check official conflicts if user_id provided and requested
            if user_id and check_officials:
                conflicts.extend(self._check_official_conflicts(user_id, buffer_start, buffer_end))
            
            return conflicts
        
        except Exception as e:
            logger.error(f"Error checking conflicts for game {self.id}: {e}")
            return [{'type': 'system_error', 'message': 'Error checking conflicts'}]
    
    def _check_location_conflicts(self, buffer_start, buffer_end):
        """Check for location/field conflicts"""
        conflicts = []
        try:
            # Build query for potential conflicts
            conflict_query = Game.query.filter(
                Game.id != self.id,  # Exclude current game
                Game.date == self.date,
                Game.location_id == self.location_id,
                Game.status.notin_(['cancelled', 'completed']),  # Exclude inactive games
                Game.is_active == True
            )
            
            # Add field-specific conflict if field specified
            if self.field_name:
                conflict_query = conflict_query.filter(Game.field_name == self.field_name)
            
            # Get games that might conflict
            potential_conflicts = conflict_query.all()
            
            for conflict_game in potential_conflicts:
                if not conflict_game.datetime:
                    continue
                
                other_start = conflict_game.datetime
                other_end = other_start + timedelta(minutes=conflict_game.estimated_duration or 120)
                
                # Check for time overlap with buffer
                if not (buffer_end <= other_start or buffer_start >= other_end):
                    conflict_type = 'field_conflict' if self.field_name else 'location_conflict'
                    conflicts.append({
                        'type': conflict_type,
                        'message': f'{"Field" if self.field_name else "Location"} conflict with {conflict_game.game_title} at {conflict_game.time.strftime("%I:%M %p") if conflict_game.time else "unknown time"}',
                        'game': conflict_game,
                        'conflict_time': conflict_game.time
                    })
        
        except Exception as e:
            logger.error(f"Error checking location conflicts: {e}")
        
        return conflicts
    
    def _check_official_conflicts(self, user_id, buffer_start, buffer_end):
        """Check for official assignment conflicts"""
        conflicts = []
        try:
            # Get all assignments for this official on the same date
            from models.database import User  # Import here to avoid circular imports
            
            official_assignments = GameAssignment.query.filter(
                GameAssignment.user_id == user_id,
                GameAssignment.is_active == True
            ).join(Game).filter(
                Game.id != self.id,  # Exclude current game
                Game.date == self.date,
                Game.status.notin_(['cancelled', 'completed']),
                Game.is_active == True
            ).all()
            
            for assignment in official_assignments:
                assigned_game = assignment.game
                if not assigned_game.datetime:
                    continue
                
                assigned_start = assigned_game.datetime
                assigned_end = assigned_start + timedelta(minutes=assigned_game.estimated_duration or 120)
                
                # Check if times overlap (with buffer)
                if not (buffer_end <= assigned_start or buffer_start >= assigned_end):
                    user = User.query.get(user_id)
                    user_name = user.full_name if user else f"Official #{user_id}"
                    
                    conflicts.append({
                        'type': 'official_conflict',
                        'message': f'{user_name} is already assigned to {assigned_game.game_title} at {assigned_game.time.strftime("%I:%M %p") if assigned_game.time else "unknown time"}',
                        'assignment': assignment,
                        'conflicting_game': assigned_game
                    })
        
        except Exception as e:
            logger.error(f"Error checking official conflicts: {e}")
        
        return conflicts
    
    # Status Management Methods
    def change_status(self, new_status, user_id=None):
        """
        Change game status with validation and logging
        
        Args:
            new_status: New status to set
            user_id: Optional ID of user making the change
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            old_status = self.status
            
            # Validate status transition
            valid_transitions = {
                'draft': ['ready', 'cancelled'],
                'ready': ['draft', 'released', 'cancelled'],
                'released': ['completed', 'cancelled'],
                'completed': [],  # Completed games cannot change status
                'cancelled': ['draft']  # Can restore cancelled games
            }
            
            if old_status not in valid_transitions:
                return False, f"Invalid current status: {old_status}"
            
            if new_status not in valid_transitions[old_status]:
                return False, f"Cannot change from {old_status} to {new_status}"
            
            # Special handling for release
            if new_status == 'released':
                if self.assigned_officials_count == 0:
                    return False, "Cannot release game without assigned officials"
                self.released_at = datetime.utcnow()
            
            # Update status
            self.status = new_status
            self.status_changed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Game {self.id} status changed from {old_status} to {new_status} by user {user_id}")
            return True, f"Game status changed to {new_status}"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing game status: {e}")
            return False, f"Error changing status: {str(e)}"
    
    def release(self):
        """Release game for official assignment (legacy method)"""
        return self.change_status('released')
    
    def cancel(self, reason=None):
        """Cancel the game"""
        success, message = self.change_status('cancelled')
        if success and reason:
            if self.notes:
                self.notes += f"\n\nCancellation reason: {reason}"
            else:
                self.notes = f"Cancellation reason: {reason}"
            db.session.commit()
        return success, message
    
    def restore(self):
        """Restore cancelled game to draft"""
        return self.change_status('draft')
    
    # Official Assignment Methods
    def add_official_assignment(self, user_id, position=None, assignment_type='manual'):
        """
        Add official assignment with conflict checking
        
        Args:
            user_id: ID of user to assign
            position: Optional position name
            assignment_type: 'manual' or 'auto'
            
        Returns:
            tuple: (success: bool, message: str, assignment: GameAssignment or None)
        """
        try:
            # Check for existing assignment
            existing = GameAssignment.query.filter_by(
                game_id=self.id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if existing:
                return False, "Official is already assigned to this game", None
            
            # Check for conflicts
            conflicts = self.check_conflicts(user_id=user_id)
            if conflicts:
                conflict_messages = [c['message'] for c in conflicts]
                return False, f"Assignment conflicts: {'; '.join(conflict_messages)}", None
            
            # Create assignment
            assignment = GameAssignment(
                game_id=self.id,
                user_id=user_id,
                position=position or f"Official {self.assigned_officials_count + 1}",
                assignment_type=assignment_type,
                status='assigned'
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            logger.info(f"Official {user_id} assigned to game {self.id}")
            return True, "Official assigned successfully", assignment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning official to game: {e}")
            return False, f"Error assigning official: {str(e)}", None
    
    def remove_official_assignment(self, user_id):
        """Remove official assignment"""
        try:
            assignment = GameAssignment.query.filter_by(
                game_id=self.id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "Official is not assigned to this game"
            
            assignment.is_active = False
            assignment.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Official {user_id} removed from game {self.id}")
            return True, "Official removed successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing official from game: {e}")
            return False, f"Error removing official: {str(e)}"
    
    # Utility Methods
    def to_dict(self, include_relationships=False):
        """
        Convert game to dictionary for API responses with error handling
        
        Args:
            include_relationships: Whether to include related data
            
        Returns:
            dict: Game data
        """
        try:
            data = {
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
                'is_active': self.is_active,
                'fee_per_official': float(self.fee_per_official) if self.fee_per_official else None,
                'notes': self.notes,
                'special_instructions': self.special_instructions,
                'estimated_duration': self.estimated_duration,
                'game_ranking': self.game_ranking,
                'ranking_description': self.get_ranking_description(),
                'assigned_officials': self.assigned_officials_count,
                'can_be_edited': self.can_be_edited,
                'can_be_deleted': self.can_be_deleted,
                'can_be_cancelled': self.can_be_cancelled,
                'is_in_past': self.is_in_past,
                'is_today': self.is_today_game,
                'is_future': self.is_future_game,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
            
            # Include relationships if requested
            if include_relationships:
                if self.league:
                    data['league'] = {
                        'id': self.league.id,
                        'name': self.league.name,
                        'level': self.league.level
                    }
                
                if self.location:
                    data['location'] = {
                        'id': self.location.id,
                        'name': self.location.name,
                        'city': self.location.city,
                        'state': self.location.state
                    }
                
                # Include assigned officials
                data['officials'] = []
                for assignment in self.get_assigned_officials():
                    if assignment.user:
                        data['officials'].append({
                            'id': assignment.user.id,
                            'name': assignment.user.full_name,
                            'position': assignment.position,
                            'status': assignment.status
                        })
            
            return data
            
        except Exception as e:
            logger.error(f"Error converting game {self.id} to dict: {e}")
            return {'id': self.id, 'error': 'Error retrieving game data'}
    
    def soft_delete(self):
        """Soft delete the game"""
        try:
            self.is_active = False
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True, "Game deleted successfully"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error soft deleting game {self.id}: {e}")
            return False, f"Error deleting game: {str(e)}"
    
    def __repr__(self):
        return f'<Game {self.game_title} on {self.date} - {self.status}>'


class GameAssignment(db.Model):
    """
    Enhanced Game assignment model for officials with improved error handling
    """
    
    __tablename__ = 'game_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Assignment details
    position = db.Column(db.String(50), default='Official')  # referee, umpire, etc.
    assignment_type = db.Column(db.String(20), default='manual')  # manual, auto
    
    # Status tracking
    status = db.Column(db.String(20), default='assigned')  # assigned, accepted, declined
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Response tracking
    response_date = db.Column(db.DateTime)
    decline_reason = db.Column(db.String(500))
    response_notes = db.Column(db.Text)
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='game_assignments')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('game_id', 'user_id', 'is_active', name='unique_active_game_user_assignment'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate assignment status"""
        valid_statuses = ['assigned', 'accepted', 'declined', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    def accept(self, notes=None):
        """Accept the assignment with enhanced tracking"""
        try:
            self.status = 'accepted'
            self.response_date = datetime.utcnow()
            self.response_notes = notes
            self.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Assignment {self.id} accepted by user {self.user_id}")
            return True, "Assignment accepted successfully"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error accepting assignment {self.id}: {e}")
            return False, f"Error accepting assignment: {str(e)}"
    
    def decline(self, reason=None, notes=None):
        """Decline the assignment with enhanced tracking"""
        try:
            self.status = 'declined'
            self.response_date = datetime.utcnow()
            self.decline_reason = reason
            self.response_notes = notes
            self.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Assignment {self.id} declined by user {self.user_id}")
            return True, "Assignment declined"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error declining assignment {self.id}: {e}")
            return False, f"Error declining assignment: {str(e)}"
    
    def cancel(self, reason=None):
        """Cancel the assignment"""
        try:
            self.status = 'cancelled'
            self.decline_reason = reason
            self.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Assignment {self.id} cancelled")
            return True, "Assignment cancelled"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling assignment {self.id}: {e}")
            return False, f"Error cancelling assignment: {str(e)}"
    
    @property
    def can_respond(self):
        """Check if assignment can still be responded to"""
        return (self.is_active and 
                self.status == 'assigned' and 
                self.game and 
                self.game.status in ['released', 'ready'])
    
    def to_dict(self, include_relationships=False):
        """Convert assignment to dictionary"""
        try:
            data = {
                'id': self.id,
                'game_id': self.game_id,
                'user_id': self.user_id,
                'position': self.position,
                'assignment_type': self.assignment_type,
                'status': self.status,
                'is_active': self.is_active,
                'response_date': self.response_date.isoformat() if self.response_date else None,
                'decline_reason': self.decline_reason,
                'response_notes': self.response_notes,
                'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
                'can_respond': self.can_respond
            }
            
            if include_relationships:
                if self.user:
                    data['user'] = {
                        'id': self.user.id,
                        'name': self.user.full_name,
                        'email': self.user.email
                    }
                
                if self.game:
                    data['game'] = self.game.to_dict()
            
            return data
        except Exception as e:
            logger.error(f"Error converting assignment {self.id} to dict: {e}")
            return {'id': self.id, 'error': 'Error retrieving assignment data'}
    
    def __repr__(self):
        return f'<GameAssignment Game:{self.game_id} User:{self.user_id} Status:{self.status}>'

# Add to models/game.py at the end:
def safe_migrate_database():
    """Safely add new fields without breaking existing installations"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Check games table
        games_columns = [col['name'] for col in inspector.get_columns('games')]
        
        migrations = []
        if 'is_active' not in games_columns:
            migrations.append('ALTER TABLE games ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL')
        if 'status_changed_at' not in games_columns:
            migrations.append('ALTER TABLE games ADD COLUMN status_changed_at DATETIME')
        # Add other missing fields...
        
        for migration in migrations:
            db.engine.execute(text(migration))
            
        return True, f"Applied {len(migrations)} database migrations"
    except Exception as e:
        return False, f"Migration error: {str(e)}"

# Database Migration Helper
def migrate_add_missing_fields():
    """
    Helper function to add missing fields to existing database
    Run this if upgrading from an older version
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Check games table
        games_columns = [col['name'] for col in inspector.get_columns('games')]
        
        missing_fields = []
        if 'is_active' not in games_columns:
            missing_fields.append('ALTER TABLE games ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL')
        if 'status_changed_at' not in games_columns:
            missing_fields.append('ALTER TABLE games ADD COLUMN status_changed_at DATETIME')
        if 'game_ranking' not in games_columns:
            missing_fields.append('ALTER TABLE games ADD COLUMN game_ranking INTEGER DEFAULT 3')
        if 'ranking_notes' not in games_columns:
            missing_fields.append('ALTER TABLE games ADD COLUMN ranking_notes TEXT')
            
        # Check assignments table
        assignments_columns = [col['name'] for col in inspector.get_columns('game_assignments')]
        
        if 'response_notes' not in assignments_columns:
            missing_fields.append('ALTER TABLE game_assignments ADD COLUMN response_notes TEXT')
        
        # Execute missing field additions
        for sql in missing_fields:
            db.engine.execute(sql)
            print(f"✅ Executed: {sql}")
        
        if missing_fields:
            print(f"✅ Added {len(missing_fields)} missing database fields")
        else:
            print("✅ All database fields are up to date")
            
    except Exception as e:
        print(f"❌ Error migrating database fields: {e}")


# Export classes for easy importing
__all__ = ['Game', 'GameAssignment', 'migrate_add_missing_fields']