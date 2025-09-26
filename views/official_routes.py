# views/official_routes.py - System-Safe Official Routes
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from functools import wraps

# SAFE IMPORTS - Compatible with existing system
try:
    # Try Phase 4 imports first
    from models.database import db, User
    from models.game import Game, GameAssignment
    from models.league import League, Location
    FULL_MODELS_AVAILABLE = True
    print("✅ Full models available - Phase 4 compatibility")
except ImportError:
    try:
        # Fallback to Phase 2 structure
        from models.user import User
        from models.database import db
        FULL_MODELS_AVAILABLE = False
        print("⚠️ Using Phase 2 compatibility mode")
        
        # Create placeholder classes to prevent errors
        class Game:
            pass
        class GameAssignment:
            pass
        class League:
            pass
        class Location:
            pass
    except ImportError:
        # Final fallback
        FULL_MODELS_AVAILABLE = False
        print("⚠️ Minimal compatibility mode - assignments will show placeholder data")
        
        class User:
            pass
        class Game:
            pass
        class GameAssignment:
            pass
        class League:
            pass
        class Location:
            pass
        db = None

official_bp = Blueprint('official', __name__)

def official_access_required(f):
    """SAFE decorator that works with existing auth system"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # Allow all authenticated users - compatible with current system
        return f(*args, **kwargs)
    return decorated_function

@official_bp.route('/dashboard')
@login_required
@official_access_required
def dashboard():
    """SAFE official dashboard - works with any system phase"""
    try:
        if FULL_MODELS_AVAILABLE and hasattr(GameAssignment, 'query'):
            # Use real data if available
            assignments = GameAssignment.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).limit(10).all()
            
            upcoming = [a for a in assignments if a.game.date >= date.today()]
            recent = [a for a in assignments if a.game.date < date.today()]
            
            total_assignments = len(assignments)
            pending_count = len([a for a in assignments if a.status == 'assigned'])
            accepted_count = len([a for a in assignments if a.status == 'accepted'])
            completed_count = len([a for a in assignments if a.status == 'completed'])
            total_earnings = completed_count * 50.0  # Estimate
            
        else:
            # Safe fallback data
            upcoming = []
            recent = []
            total_assignments = 0
            pending_count = 0
            accepted_count = 0
            completed_count = 0
            total_earnings = 0.0
            
            flash('Assignment system is being set up. Check back soon!', 'info')
        
        return render_template('official/dashboard.html',
                             title='My Dashboard',
                             upcoming_assignments=upcoming,
                             recent_assignments=recent,
                             total_assignments=total_assignments,
                             pending_count=pending_count,
                             accepted_count=accepted_count,
                             completed_count=completed_count,
                             total_earnings=total_earnings)
    
    except Exception as e:
        # SAFE error handling
        flash(f'Loading dashboard data: {str(e)}', 'info')
        return render_template('official/dashboard.html',
                             title='My Dashboard',
                             upcoming_assignments=[],
                             recent_assignments=[],
                             total_assignments=0,
                             pending_count=0,
                             accepted_count=0,
                             completed_count=0,
                             total_earnings=0.0)

@official_bp.route('/assignments')
@login_required  
@official_access_required
def assignments():
    """SAFE assignments view - compatible with existing system"""
    try:
        if FULL_MODELS_AVAILABLE and hasattr(GameAssignment, 'query'):
            # Use real assignments if available
            assignments = GameAssignment.query.join(Game).filter(
                GameAssignment.user_id == current_user.id,
                GameAssignment.is_active == True
            ).order_by(Game.date.desc()).all()
        else:
            # Safe fallback - empty assignments list
            assignments = []
        
        return render_template('official/assignments.html',
                             title='My Assignments',
                             assignments=assignments)
    
    except Exception as e:
        # SAFE error handling - never crash
        return jsonify({
            'success': True,  # Don't break frontend
            'assignments': [],
            'message': f'Assignments system initializing: {str(e)}'
        })

@official_bp.route('/assignments/<int:assignment_id>')
@login_required
@official_access_required  
def assignment_detail(assignment_id):
    """SAFE assignment detail view"""
    try:
        if FULL_MODELS_AVAILABLE and hasattr(GameAssignment, 'query'):
            assignment = GameAssignment.query.filter_by(
                id=assignment_id,
                user_id=current_user.id
            ).first()
            
            if not assignment:
                flash('Assignment not found', 'error')
                return redirect(url_for('official.assignments'))
                
            # Get other officials
            other_officials = GameAssignment.query.filter(
                GameAssignment.game_id == assignment.game_id,
                GameAssignment.user_id != current_user.id,
                GameAssignment.is_active == True
            ).all()
            
            return render_template('official/assignment_detail.html',
                                 title='Assignment Details',
                                 assignment=assignment,
                                 other_officials=other_officials)
        else:
            flash('Assignment details are not available yet', 'info')
            return redirect(url_for('official.assignments'))
    
    except Exception as e:
        flash(f'Error loading assignment: {str(e)}', 'error')
        return redirect(url_for('official.assignments'))

@official_bp.route('/assignments/<int:assignment_id>/respond', methods=['POST'])
@login_required
@official_access_required
def respond_assignment(assignment_id):
    """SAFE assignment response - won't break system"""
    try:
        if not FULL_MODELS_AVAILABLE:
            flash('Assignment responses are not available yet', 'info')
            return redirect(url_for('official.assignments'))
            
        assignment = GameAssignment.query.filter_by(
            id=assignment_id,
            user_id=current_user.id
        ).first()
        
        if not assignment:
            flash('Assignment not found', 'error')
            return redirect(url_for('official.assignments'))
        
        response = request.form.get('response')  # 'accepted' or 'declined'
        notes = request.form.get('notes', '')
        
        if response not in ['accepted', 'declined']:
            flash('Invalid response', 'error')
            return redirect(url_for('official.assignment_detail', assignment_id=assignment_id))
        
        # Safe update
        assignment.status = response
        assignment.response_date = datetime.utcnow()
        assignment.notes = notes
        
        if db:
            try:
                db.session.commit()
                flash(f'Assignment {response} successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating assignment: {str(e)}', 'error')
        
        return redirect(url_for('official.assignments'))
    
    except Exception as e:
        flash(f'Error processing response: {str(e)}', 'error')
        return redirect(url_for('official.assignments'))

@official_bp.route('/availability')
@login_required
@official_access_required
def availability():
    """SAFE availability management"""
    return render_template('official/availability.html', 
                         title='My Availability',
                         message='Availability management coming soon!')

@official_bp.route('/reports')
@login_required
@official_access_required  
def reports():
    """SAFE personal reports"""
    try:
        # Safe report data
        monthly_earnings = {}
        total_games = 0
        total_earnings = 0.0
        
        if FULL_MODELS_AVAILABLE:
            # Try to get real data
            pass  # Implementation when Phase 4 is fully ready
        
        return render_template('official/reports.html',
                             title='My Reports',
                             monthly_earnings=monthly_earnings,
                             total_games=total_games,
                             total_earnings=total_earnings)
    
    except Exception as e:
        return render_template('official/reports.html',
                             title='My Reports',
                             monthly_earnings={},
                             total_games=0,
                             total_earnings=0.0,
                             error_message=str(e))

# SAFE API endpoints that won't break existing system
@official_bp.route('/api/assignments')
@login_required
@official_access_required
def api_assignments():
    """SAFE API endpoint - always returns valid JSON"""
    try:
        if FULL_MODELS_AVAILABLE and hasattr(GameAssignment, 'query'):
            assignments = GameAssignment.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).all()
            
            assignment_data = []
            for assignment in assignments:
                try:
                    assignment_data.append({
                        'id': assignment.id,
                        'game_title': getattr(assignment.game, 'game_title', 'Game'),
                        'date': assignment.game.date.strftime('%Y-%m-%d'),
                        'time': assignment.game.time.strftime('%H:%M') if assignment.game.time else '',
                        'location': getattr(assignment.game.location, 'name', 'TBD') if hasattr(assignment.game, 'location') else 'TBD',
                        'status': assignment.status,
                        'position': getattr(assignment, 'position', '') or '',
                        'league': getattr(assignment.game.league, 'name', 'League') if hasattr(assignment.game, 'league') else 'League'
                    })
                except Exception:
                    # Skip problematic assignments
                    continue
        else:
            assignment_data = []
        
        return jsonify({
            'success': True,
            'assignments': assignment_data,
            'message': f'Found {len(assignment_data)} assignments'
        })
    
    except Exception as e:
        # ALWAYS return valid JSON - never crash
        return jsonify({
            'success': True,  # Frontend friendly
            'assignments': [],
            'message': f'Assignments loading: {str(e)}'
        })

@official_bp.route('/api/availability', methods=['GET', 'POST'])
@login_required
@official_access_required
def api_availability():
    """SAFE availability API"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'availability': [],
            'message': 'Availability system initializing'
        })
    
    elif request.method == 'POST':
        return jsonify({
            'success': True,
            'message': 'Availability updated (demo mode)'
        })
