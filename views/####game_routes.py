# views/game_routes.py - Game Scheduling and Assignment Routes
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date, time
from functools import wraps
from models.database import db, User
from models.league import League, Location
from models.game import Game, GameAssignment

game_bp = Blueprint('game', __name__)

def game_manager_required(f):
    """Decorator to require game management permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.can_manage_users and current_user.role not in ['assigner']:
            flash('Access denied. Game management role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/dashboard')
@login_required
@game_manager_required
def dashboard():
    """Game management dashboard"""
    # Get statistics
    total_games = Game.query.count()
    draft_games = Game.query.filter_by(status='draft').count()
    ready_games = Game.query.filter_by(status='ready').count()
    released_games = Game.query.filter_by(status='released').count()
    completed_games = Game.query.filter_by(status='completed').count()
    
    # Recent games
    recent_games = Game.query.order_by(Game.created_at.desc()).limit(10).all()
    
    # Upcoming games (next 7 days)
    next_week = date.today() + timedelta(days=7)
    upcoming_games = Game.query.filter(
        Game.date.between(date.today(), next_week),
        Game.status.in_(['ready', 'released'])
    ).order_by(Game.date, Game.time).limit(10).all()
    
    # Unassigned games
    unassigned_games = Game.query.filter(
        Game.status == 'released',
        ~Game.assignments.any(GameAssignment.is_active == True)
    ).limit(5).all()
    
    return render_template('game/dashboard.html',
                         total_games=total_games,
                         draft_games=draft_games,
                         ready_games=ready_games,
                         released_games=released_games,
                         completed_games=completed_games,
                         recent_games=recent_games,
                         upcoming_games=upcoming_games,
                         unassigned_games=unassigned_games)

@game_bp.route('/manage')
@login_required
@game_manager_required
def manage_games():
    """Game management page with filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    league_filter = request.args.get('league', '')
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    # Build query
    query = Game.query.join(League).join(Location)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Game.home_team.contains(search),
                Game.away_team.contains(search),
                League.name.contains(search),
                Location.name.contains(search)
            )
        )
    
    if league_filter:
        query = query.filter(Game.league_id == league_filter)
    
    if status_filter:
        query = query.filter(Game.status == status_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Game.date == filter_date)
        except ValueError:
            pass
    
    # Paginate results
    games = query.order_by(Game.date.desc(), Game.time.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # Get leagues for filter dropdown
    leagues = League.query.filter_by(is_active=True).all()
    
    return render_template('game/manage_games.html',
                         games=games,
                         leagues=leagues,
                         search=search,
                         league_filter=league_filter,
                         status_filter=status_filter,
                         date_filter=date_filter)

@game_bp.route('/add', methods=['GET', 'POST'])
@login_required
@game_manager_required
def add_game():
    """Add new game"""
    if request.method == 'POST':
        league_id = request.form.get('league_id', type=int)
        location_id = request.form.get('location_id', type=int)
        game_date = request.form.get('date')
        game_time = request.form.get('time')
        field_name = request.form.get('field_name', '').strip()
        home_team = request.form.get('home_team', '').strip()
        away_team = request.form.get('away_team', '').strip()
        level = request.form.get('level', '').strip()
        fee_per_official = request.form.get('fee_per_official', type=float)
        estimated_duration = request.form.get('estimated_duration', 120, type=int)
        notes = request.form.get('notes', '').strip()
        special_instructions = request.form.get('special_instructions', '').strip()
        
        # Validation
        errors = []
        if not league_id:
            errors.append('League is required')
        if not location_id:
            errors.append('Location is required')
        if not game_date:
            errors.append('Date is required')
        if not game_time:
            errors.append('Time is required')
        
        # Validate date and time
        try:
            parsed_date = datetime.strptime(game_date, '%Y-%m-%d').date()
            parsed_time = datetime.strptime(game_time, '%H:%M').time()
        except ValueError:
            errors.append('Invalid date or time format')
            parsed_date = None
            parsed_time = None
        
        if errors:
            for error in errors:
                flash(error, 'error')
            # Get data for form repopulation
            leagues = League.query.filter_by(is_active=True).all()
            locations = Location.query.filter_by(is_active=True).all()
            return render_template('game/add_game.html', leagues=leagues, locations=locations)
        
        # Create game
        game = Game(
            league_id=league_id,
            location_id=location_id,
            date=parsed_date,
            time=parsed_time,
            field_name=field_name if field_name else None,
            home_team=home_team if home_team else None,
            away_team=away_team if away_team else None,
            level=level if level else None,
            fee_per_official=fee_per_official if fee_per_official else None,
            estimated_duration=estimated_duration,
            notes=notes if notes else None,
            special_instructions=special_instructions if special_instructions else None,
            status='draft'
        )
        
        # Check for conflicts
        conflicts = game.check_conflicts()
        if conflicts:
            for conflict in conflicts:
                flash(f"Warning: {conflict['message']}", 'warning')
        
        try:
            db.session.add(game)
            db.session.commit()
            flash(f'Game "{game.game_title}" created successfully!', 'success')
            return redirect(url_for('game.manage_games'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating game: {str(e)}', 'error')
    
    # GET request - show form
    leagues = League.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    
    return render_template('game/add_game.html', leagues=leagues, locations=locations)

@game_bp.route('/<int:game_id>/edit', methods=['GET', 'POST'])
@login_required
@game_manager_required
def edit_game(game_id):
    """Edit game details"""
    game = Game.query.get_or_404(game_id)
    
    # Check if game can be edited
    if not game.can_be_edited:
        flash('This game cannot be edited (either completed or in the past).', 'error')
        return redirect(url_for('game.manage_games'))
    
    if request.method == 'POST':
        # Update game details
        game.league_id = request.form.get('league_id', type=int)
        game.location_id = request.form.get('location_id', type=int)
        
        game_date = request.form.get('date')
        game_time = request.form.get('time')
        
        try:
            game.date = datetime.strptime(game_date, '%Y-%m-%d').date()
            game.time = datetime.strptime(game_time, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format', 'error')
            return render_template('game/edit_game.html', game=game)
        
        game.field_name = request.form.get('field_name', '').strip()
        game.home_team = request.form.get('home_team', '').strip()
        game.away_team = request.form.get('away_team', '').strip()
        game.level = request.form.get('level', '').strip()
        game.fee_per_official = request.form.get('fee_per_official', type=float)
        game.estimated_duration = request.form.get('estimated_duration', 120, type=int)
        game.notes = request.form.get('notes', '').strip()
        game.special_instructions = request.form.get('special_instructions', '').strip()
        game.updated_at = datetime.utcnow()
        
        # Check for conflicts with updated information
        conflicts = game.check_conflicts()
        if conflicts:
            for conflict in conflicts:
                flash(f"Warning: {conflict['message']}", 'warning')
        
        try:
            db.session.commit()
            flash(f'Game "{game.game_title}" updated successfully!', 'success')
            return redirect(url_for('game.manage_games'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating game: {str(e)}', 'error')
    
    # GET request - show form
    leagues = League.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    
    return render_template('game/edit_game.html', game=game, leagues=leagues, locations=locations)

@game_bp.route('/<int:game_id>/change-status', methods=['POST'])
@login_required
@game_manager_required
def change_game_status(game_id):
    """Change game status"""
    game = Game.query.get_or_404(game_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['draft', 'ready', 'released', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status', 'error')
        return redirect(url_for('game.manage_games'))
    
    # Business logic for status changes
    if game.status == 'draft' and new_status == 'released':
        # Must go through 'ready' first
        flash('Games must be marked as "Ready" before being released.', 'error')
        return redirect(url_for('game.manage_games'))
    
    if new_status == 'released' and game.status != 'ready':
        flash('Only games in "Ready" status can be released.', 'error')
        return redirect(url_for('game.manage_games'))
    
    # Update status
    old_status = game.status
    game.status = new_status
    game.updated_at = datetime.utcnow()
    
    if new_status == 'released':
        game.released_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash(f'Game status changed from "{old_status}" to "{new_status}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating game status: {str(e)}', 'error')
    
    return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/assign')
@login_required
@game_manager_required
def assign_officials(game_id):
    """Assign officials to game"""
    game = Game.query.get_or_404(game_id)
    
    # Get available officials (those in the same league)
    available_officials = User.query.filter(
        User.role.in_(['official', 'assigner', 'administrator', 'superadmin']),
        User.is_active == True
    ).all()
    
    # Get current assignments
    current_assignments = GameAssignment.query.filter_by(
        game_id=game_id,
        is_active=True
    ).all()
    
    return render_template('game/assign_officials.html',
                         game=game,
                         available_officials=available_officials,
                         current_assignments=current_assignments)

@game_bp.route('/<int:game_id>/assign-official', methods=['POST'])
@login_required
@game_manager_required
def assign_official_to_game(game_id):
    """Assign a specific official to a game"""
    game = Game.query.get_or_404(game_id)
    user_id = request.form.get('user_id', type=int)
    position = request.form.get('position', '').strip()
    
    if not user_id:
        flash('Official selection is required', 'error')
        return redirect(url_for('game.assign_officials', game_id=game_id))
    
    # Check if user is already assigned to this game
    existing_assignment = GameAssignment.query.filter_by(
        game_id=game_id,
        user_id=user_id,
        is_active=True
    ).first()
    
    if existing_assignment:
        flash('This official is already assigned to this game.', 'error')
        return redirect(url_for('game.assign_officials', game_id=game_id))
    
    # Check for conflicts
    conflicts = game.check_conflicts(user_id=user_id)
    if conflicts:
        for conflict in conflicts:
            if conflict['type'] == 'official_conflict':
                flash(f"Conflict: {conflict['message']}", 'error')
                return redirect(url_for('game.assign_officials', game_id=game_id))
    
    # Create assignment
    assignment = GameAssignment(
        game_id=game_id,
        user_id=user_id,
        position=position if position else None,
        assignment_type='manual',
        status='assigned'
    )
    
    try:
        db.session.add(assignment)
        db.session.commit()
        
        user = User.query.get(user_id)
        flash(f'{user.full_name} assigned to {game.game_title}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning official: {str(e)}', 'error')
    
    return redirect(url_for('game.assign_officials', game_id=game_id))

@game_bp.route('/assignment/<int:assignment_id>/remove', methods=['POST'])
@login_required
@game_manager_required
def remove_assignment(assignment_id):
    """Remove official assignment"""
    assignment = GameAssignment.query.get_or_404(assignment_id)
    game_id = assignment.game_id
    
    try:
        assignment.is_active = False
        assignment.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Official assignment removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing assignment: {str(e)}', 'error')
    
    return redirect(url_for('game.assign_officials', game_id=game_id))

# API endpoints for AJAX calls

@game_bp.route('/api/games')
@login_required
def api_games():
    """API endpoint for game data"""
    games = Game.query.join(League).join(Location).all()
    return jsonify([game.to_dict() for game in games])

@game_bp.route('/api/league/<int:league_id>/fee')
@login_required
def api_league_fee(league_id):
    """Get default fee for a league"""
    league = League.query.get_or_404(league_id)
    return jsonify({'fee': float(league.game_fee)})

@game_bp.route('/api/location/<int:location_id>/fields')
@login_required
def api_location_fields(location_id):
    """Get field information for a location"""
    location = Location.query.get_or_404(location_id)
    fields = []
    
    if location.field_names:
        # Parse field names if stored as JSON or comma-separated
        try:
            import json
            fields = json.loads(location.field_names)
        except:
            # Fallback to comma-separated
            fields = [f.strip() for f in location.field_names.split(',') if f.strip()]
    else:
        # Generate default field names
        for i in range(1, location.field_count + 1):
            fields.append(f"Field {i}")
    
    return jsonify({'fields': fields})
