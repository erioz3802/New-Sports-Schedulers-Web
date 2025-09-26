# views/game_routes.py - Complete Game Routes Based on Knowledge Base and Chat History
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date, time
from functools import wraps
from sqlalchemy import or_, and_
import logging
import csv
from io import StringIO

# Import models with error handling to prevent circular imports
try:
    from models.database import db, User
    from models.league import League, Location
    from models.game import Game, GameAssignment
except ImportError as e:
    print(f"Import error in game_routes: {e}")
    # Set up fallbacks to prevent complete failure
    db = None
    User = None
    League = None
    Location = None
    Game = None
    GameAssignment = None

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint (NO url_prefix to maintain compatibility)
game_bp = Blueprint('game', __name__)

def game_manager_required(f):
    """Decorator to require game management permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['assigner', 'administrator', 'superadmin']:
            flash('Access denied. Game management role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/dashboard')
@login_required
@game_manager_required
def dashboard():
    """Game management dashboard"""
    try:
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
        
        # Unassigned games - handle cases where assigned_officials_count might not exist
        unassigned_games = []
        try:
            all_released = Game.query.filter_by(status='released').all()
            for game in all_released:
                count = 0
                try:
                    count = game.assigned_officials_count
                except:
                    # Fallback count method
                    count = GameAssignment.query.filter_by(game_id=game.id, is_active=True).count()
                if count == 0:
                    unassigned_games.append(game)
                if len(unassigned_games) >= 5:
                    break
        except Exception as e:
            logger.error(f"Error getting unassigned games: {e}")
        
        return render_template('game/dashboard.html',
                             total_games=total_games,
                             draft_games=draft_games,
                             ready_games=ready_games,
                             released_games=released_games,
                             completed_games=completed_games,
                             recent_games=recent_games,
                             upcoming_games=upcoming_games,
                             unassigned_games=unassigned_games)
    except Exception as e:
        logger.error(f"Error in game dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('game/dashboard.html', error=True)

@game_bp.route('/manage')
@login_required
@game_manager_required
def manage_games():
    """Game management page with filtering - SAFE VERSION"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        league_filter = request.args.get('league', '')
        status_filter = request.args.get('status', '')
        date_filter = request.args.get('date', '')
        time_period = request.args.get('time_period', 'future')  # Default to future
        
        # Build base query with safety checks
        if not Game or not League or not Location:
            flash('Game management not available - models not loaded', 'error')
            return render_template('game/manage_games.html', games=None, leagues=[])
        
        query = Game.query.join(League).join(Location)
        
        # Apply filters safely
        if search:
            query = query.filter(
                or_(
                    Game.home_team.contains(search),
                    Game.away_team.contains(search),
                    League.name.contains(search),
                    Location.name.contains(search)
                )
            )
        
        if league_filter:
            try:
                query = query.filter(Game.league_id == int(league_filter))
            except (ValueError, TypeError):
                pass
        
        if status_filter:
            query = query.filter(Game.status == status_filter)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(Game.date == filter_date)
            except ValueError:
                pass
        
        # Apply time period filter with safety
        today = date.today()
        if time_period == 'future':
            query = query.filter(Game.date >= today)
            query = query.order_by(Game.date.asc(), Game.time.asc())
        elif time_period == 'past':
            query = query.filter(Game.date < today)
            query = query.order_by(Game.date.desc(), Game.time.desc())
        elif time_period == 'today':
            query = query.filter(Game.date == today)
            query = query.order_by(Game.time.asc())
        else:  # all
            query = query.order_by(Game.date.desc(), Game.time.desc())
        
        # Get counts safely for tabs
        try:
            base_query = Game.query
            # Check for is_active field safely
            try:
                base_query = base_query.filter(Game.is_active == True)
            except:
                # is_active field doesn't exist yet
                pass
            
            future_count = base_query.filter(Game.date >= today).count()
            today_count = base_query.filter(Game.date == today).count()
            past_count = base_query.filter(Game.date < today).count()
            released_count = base_query.filter(Game.status == 'released').count()
        except Exception as e:
            logger.error(f"Error getting counts: {e}")
            future_count = today_count = past_count = released_count = 0
        
        # Paginate results
        games = query.paginate(
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
                             date_filter=date_filter,
                             time_period=time_period,
                             future_count=future_count,
                             today_count=today_count,
                             past_count=past_count,
                             released_count=released_count)
        
    except Exception as e:
        logger.error(f"Error loading manage games: {e}")
        flash('Error loading games list.', 'error')
        return render_template('game/manage_games.html', games=None, leagues=[])

@game_bp.route('/add', methods=['GET', 'POST'])
@login_required
@game_manager_required
def add_game():
    """Add new game"""
    if request.method == 'POST':
        try:
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
            game_ranking = request.form.get('game_ranking', 3, type=int)
            ranking_notes = request.form.get('ranking_notes', '').strip()
            
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
            
            # Create game with safe field handling
            game_data = {
                'league_id': league_id,
                'location_id': location_id,
                'date': parsed_date,
                'time': parsed_time,
                'field_name': field_name if field_name else None,
                'home_team': home_team if home_team else None,
                'away_team': away_team if away_team else None,
                'level': level if level else None,
                'fee_per_official': fee_per_official if fee_per_official else None,
                'estimated_duration': estimated_duration,
                'notes': notes if notes else None,
                'special_instructions': special_instructions if special_instructions else None,
                'status': 'draft'
            }
            
            # Add optional fields if they exist in model
            try:
                game_data['game_ranking'] = game_ranking if game_ranking else 3
                game_data['ranking_notes'] = ranking_notes if ranking_notes else None
            except:
                pass  # Fields don't exist in current model
            
            game = Game(**game_data)
            
            # Check for conflicts if method exists
            try:
                conflicts = game.check_conflicts()
                if conflicts:
                    for conflict in conflicts:
                        flash(f"Warning: {conflict['message']}", 'warning')
            except:
                pass  # check_conflicts method doesn't exist
            
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
    """Edit game details - ALLOWS EDITING PAST GAMES per knowledge base"""
    try:
        game = Game.query.get_or_404(game_id)
        
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
        
    except Exception as e:
        logger.error(f"Error in edit_game {game_id}: {e}")
        flash('Error loading game for editing.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/change-status', methods=['POST'])
@login_required
@game_manager_required
def change_game_status(game_id):
    """Change game status"""
    try:
        game = Game.query.get_or_404(game_id)
        new_status = request.form.get('status')
        
        valid_statuses = ['draft', 'ready', 'released', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            flash('Invalid status', 'error')
            return redirect(url_for('game.manage_games'))
        
        # Business logic for status changes
        if game.status == 'draft' and new_status == 'released':
            flash('Games must be marked as "Ready" before being released.', 'error')
            return redirect(url_for('game.manage_games'))
        
        if new_status == 'released' and game.status != 'ready':
            flash('Only games in "Ready" status can be released.', 'error')
            return redirect(url_for('game.manage_games'))
        
        # Update status with reactivation logic from knowledge base
        old_status = game.status
        if old_status == 'cancelled' and new_status == 'draft':
            # REACTIVATION LOGIC from knowledge base
            game.status = 'draft'
            game.updated_at = datetime.utcnow()
            try:
                game.released_at = None  # Clear release date when reactivating
            except:
                pass  # Field might not exist
            
            try:
                db.session.commit()
                flash('Game has been reactivated and set to Draft status.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error reactivating game: {str(e)}', 'error')
            
            return redirect(url_for('game.manage_games'))

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
        
    except Exception as e:
        logger.error(f"Error changing status for game {game_id}: {e}")
        flash('Error changing game status.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/assign')
@login_required
@game_manager_required
def assign_officials(game_id):
    """Assign officials to game"""
    try:
        game = Game.query.get_or_404(game_id)
        
        # Get available officials
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
    except Exception as e:
        logger.error(f"Error loading assignment page for game {game_id}: {e}")
        flash('Error loading assignment page.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/assign-official', methods=['POST'])
@login_required
@game_manager_required
def assign_official_to_game(game_id):
    """Assign a specific official to a game - WITH FIXED CONSTRAINT HANDLING"""
    try:
        game = Game.query.get_or_404(game_id)
        user_id = request.form.get('user_id', type=int)
        position = request.form.get('position', '').strip()
        
        if not user_id:
            flash('Official selection is required', 'error')
            return redirect(url_for('game.assign_officials', game_id=game_id))
        
        # FIXED CONSTRAINT HANDLING from knowledge base
        # Check if user is already assigned (including inactive assignments)
        existing_assignment = GameAssignment.query.filter_by(
            game_id=game_id,
            user_id=user_id
        ).first()
        
        if existing_assignment:
            if existing_assignment.is_active:
                flash('This official is already assigned to this game.', 'error')
                return redirect(url_for('game.assign_officials', game_id=game_id))
            else:
                # Reactivate existing inactive assignment instead of creating new
                existing_assignment.is_active = True
                existing_assignment.status = 'assigned'
                existing_assignment.assigned_at = datetime.utcnow()
                existing_assignment.updated_at = datetime.utcnow()
                if position:
                    existing_assignment.position = position
        else:
            # Create new assignment
            assignment = GameAssignment(
                game_id=game_id,
                user_id=user_id,
                position=position if position else None,
                assignment_type='manual',
                status='assigned'
            )
            db.session.add(assignment)
        
        # Check for conflicts if method exists
        try:
            conflicts = game.check_conflicts(user_id=user_id)
            if conflicts:
                for conflict in conflicts:
                    if conflict['type'] == 'official_conflict':
                        flash(f"Conflict: {conflict['message']}", 'error')
                        return redirect(url_for('game.assign_officials', game_id=game_id))
        except:
            pass  # check_conflicts method doesn't exist
        
        try:
            db.session.commit()
            user = User.query.get(user_id)
            flash(f'{user.full_name} assigned to {game.game_title}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning official: {str(e)}', 'error')
        
        return redirect(url_for('game.assign_officials', game_id=game_id))
        
    except Exception as e:
        logger.error(f"Error assigning official to game {game_id}: {e}")
        flash('Error assigning official.', 'error')
        return redirect(url_for('game.assign_officials', game_id=game_id))

@game_bp.route('/assignment/<int:assignment_id>/remove', methods=['POST'])
@login_required
@game_manager_required
def remove_assignment(assignment_id):
    """Remove official assignment with LINKED GAME SUPPORT from knowledge base"""
    try:
        assignment = GameAssignment.query.get_or_404(assignment_id)
        game_id = assignment.game_id
        user_id = assignment.user_id
        
        # Get the game to check if it's part of a linked group
        game = Game.query.get_or_404(game_id)
        
        removed_count = 0
        
        # Check if this game is part of a linked group (from knowledge base)
        if game.notes and 'Linked Group:' in game.notes:
            try:
                group_id = game.notes.split('Linked Group:')[1].split('\n')[0].strip()
                
                # Find all games in this group
                linked_games = Game.query.filter(
                    Game.notes.contains(f'Linked Group: {group_id}')
                ).all()
                
                # Remove official from all linked games
                for linked_game in linked_games:
                    assignments_to_remove = GameAssignment.query.filter_by(
                        game_id=linked_game.id,
                        user_id=user_id,
                        is_active=True
                    ).all()
                    
                    for assignment_to_remove in assignments_to_remove:
                        assignment_to_remove.is_active = False
                        assignment_to_remove.updated_at = datetime.utcnow()
                        removed_count += 1
                
                flash(f'Official removed from {removed_count} linked games.', 'success')
            except Exception as e:
                logger.error(f"Error removing from linked games: {e}")
                # Fall back to single game removal
                assignment.is_active = False
                assignment.updated_at = datetime.utcnow()
                flash('Official assignment removed.', 'success')
        else:
            # Just remove from this single game
            assignment.is_active = False
            assignment.updated_at = datetime.utcnow()
            flash('Official assignment removed.', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing assignment {assignment_id}: {e}")
        flash('Error removing assignment.', 'error')
    
    return redirect(url_for('game.assign_officials', game_id=game_id))

# BULK OPERATIONS from knowledge base
@game_bp.route('/bulk/status-change', methods=['POST'])
@login_required
@game_manager_required
def bulk_status_change():
    """Bulk status change for multiple games"""
    try:
        game_ids = request.form.getlist('game_ids')
        action = request.form.get('action')
        
        if not game_ids or not action:
            flash('No games selected or invalid action.', 'error')
            return redirect(url_for('game.manage_games'))
        
        # Status mappings
        status_mappings = {
            'ready': 'ready',
            'release': 'released', 
            'cancel': 'cancelled',
            'reactivate': 'draft'
        }
        
        if action not in status_mappings:
            flash('Invalid action.', 'error')
            return redirect(url_for('game.manage_games'))
        
        new_status = status_mappings[action]
        updated_count = 0
        
        # Process each game
        for game_id_str in game_ids:
            try:
                game_id = int(game_id_str)
                game = Game.query.get(game_id)
                if not game:
                    continue
                
                # Skip invalid transitions
                if action == 'release' and game.status != 'ready':
                    continue
                elif action == 'reactivate' and game.status != 'cancelled':
                    continue
                
                game.status = new_status
                game.updated_at = datetime.utcnow()
                
                if new_status == 'released':
                    game.released_at = datetime.utcnow()
                elif action == 'reactivate':
                    try:
                        game.released_at = None
                    except:
                        pass
                
                updated_count += 1
                
            except (ValueError, TypeError):
                continue
            except Exception as e:
                logger.error(f"Error updating game {game_id_str}: {e}")
                continue
        
        try:
            db.session.commit()
            if updated_count > 0:
                flash(f'{updated_count} games successfully updated.', 'success')
            else:
                flash('No games were updated.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('game.manage_games'))
        
    except Exception as e:
        logger.error(f"Error in bulk status change: {e}")
        flash('Error processing status changes.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/bulk/link-games', methods=['POST'])
@login_required
@game_manager_required
def bulk_link_games():
    """Link multiple games together - from knowledge base"""
    try:
        game_ids = request.form.getlist('game_ids')
        
        if not game_ids or len(game_ids) < 2:
            flash('Please select at least 2 games to link together.', 'error')
            return redirect(url_for('game.manage_games'))
        
        try:
            game_ids = [int(gid) for gid in game_ids]
            games = Game.query.filter(Game.id.in_(game_ids)).all()
            
            # Create group ID
            group_id = f"GROUP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            for game in games:
                if not game.notes:
                    game.notes = f"Linked Group: {group_id}"
                else:
                    game.notes += f"\nLinked Group: {group_id}"
                game.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f'{len(games)} games linked in group: {group_id}', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error linking games: {str(e)}', 'error')
        
        return redirect(url_for('game.manage_games'))
        
    except Exception as e:
        logger.error(f"Error linking games: {e}")
        flash('Error linking games.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/bulk/clone-games', methods=['POST'])
@login_required
@game_manager_required
def bulk_clone_games():
    """Clone multiple games - MISSING FUNCTIONALITY ADDED"""
    try:
        game_ids = request.form.getlist('game_ids')
        clone_date = request.form.get('clone_date')  # Optional new date
        
        if not game_ids:
            flash('No games selected for cloning.', 'error')
            return redirect(url_for('game.manage_games'))
        
        cloned_count = 0
        errors = []
        
        for game_id_str in game_ids:
            try:
                game_id = int(game_id_str)
                original_game = Game.query.get(game_id)
                
                if not original_game:
                    continue
                
                # Create clone with safe field handling
                clone_data = {
                    'league_id': original_game.league_id,
                    'location_id': original_game.location_id,
                    'date': datetime.strptime(clone_date, '%Y-%m-%d').date() if clone_date else original_game.date,
                    'time': original_game.time,
                    'field_name': original_game.field_name,
                    'home_team': original_game.home_team,
                    'away_team': original_game.away_team,
                    'level': original_game.level,
                    'fee_per_official': original_game.fee_per_official,
                    'estimated_duration': original_game.estimated_duration,
                    'notes': f"Cloned from Game #{original_game.id}" + (f"\n{original_game.notes}" if original_game.notes else ""),
                    'special_instructions': original_game.special_instructions,
                    'status': 'draft'  # Always start clones as draft
                }
                
                # Add optional fields if they exist
                try:
                    clone_data['game_ranking'] = original_game.game_ranking
                    clone_data['ranking_notes'] = original_game.ranking_notes
                except:
                    pass
                
                cloned_game = Game(**clone_data)
                db.session.add(cloned_game)
                cloned_count += 1
                
            except (ValueError, TypeError):
                errors.append(f"Invalid game ID: {game_id_str}")
                continue
            except Exception as e:
                errors.append(f"Error cloning game {game_id_str}: {str(e)}")
                continue
        
        if cloned_count > 0:
            db.session.commit()
            flash(f'{cloned_count} games cloned successfully.', 'success')
        
        if errors:
            flash(f"Some games could not be cloned: {'; '.join(errors[:3])}", 'warning')
        
        if cloned_count == 0:
            flash('No games were cloned.', 'info')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk clone: {e}")
        flash('Error cloning games.', 'error')
    
    return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/clone', methods=['GET', 'POST'])
@login_required
@game_manager_required
def clone_game(game_id):
    """Clone a single game"""
    try:
        original_game = Game.query.get_or_404(game_id)
        
        if request.method == 'POST':
            clone_date = request.form.get('date')
            clone_time = request.form.get('time')
            
            # Create clone
            clone_data = {
                'league_id': original_game.league_id,
                'location_id': original_game.location_id,
                'date': datetime.strptime(clone_date, '%Y-%m-%d').date() if clone_date else original_game.date,
                'time': datetime.strptime(clone_time, '%H:%M').time() if clone_time else original_game.time,
                'field_name': original_game.field_name,
                'home_team': original_game.home_team,
                'away_team': original_game.away_team,
                'level': original_game.level,
                'fee_per_official': original_game.fee_per_official,
                'estimated_duration': original_game.estimated_duration,
                'notes': f"Cloned from Game #{original_game.id}" + (f"\n{original_game.notes}" if original_game.notes else ""),
                'special_instructions': original_game.special_instructions,
                'status': 'draft'
            }
            
            try:
                clone_data['game_ranking'] = original_game.game_ranking
                clone_data['ranking_notes'] = original_game.ranking_notes
            except:
                pass
            
            cloned_game = Game(**clone_data)
            db.session.add(cloned_game)
            db.session.commit()
            
            flash(f'Game "{original_game.game_title}" cloned successfully.', 'success')
            return redirect(url_for('game.manage_games'))
        
        # GET request - show clone form
        return render_template('game/clone_game.html', game=original_game)
        
    except Exception as e:
        logger.error(f"Error cloning game {game_id}: {e}")
        flash('Error cloning game.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/<int:game_id>/delete', methods=['POST'])
@login_required
@game_manager_required
def delete_game(game_id):
    """Delete a game - from knowledge base requirements"""
    try:
        game = Game.query.get_or_404(game_id)
        game_title = game.game_title
        
        # Check if game has assignments
        assignments_count = GameAssignment.query.filter_by(game_id=game_id, is_active=True).count()
        
        if assignments_count > 0:
            # Soft delete - keep game but mark as cancelled
            game.status = 'cancelled'
            try:
                game.is_active = False  # Only if field exists
            except:
                pass
            game.updated_at = datetime.utcnow()
            
            # Deactivate all assignments
            GameAssignment.query.filter_by(game_id=game_id).update({'is_active': False})
            
            flash(f'Game "{game_title}" has been cancelled and all assignments removed.', 'success')
        else:
            # Hard delete - no assignments, safe to completely remove
            db.session.delete(game)
            flash(f'Game "{game_title}" has been permanently deleted.', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting game {game_id}: {e}")
        flash('Error deleting game.', 'error')
    
    return redirect(url_for('game.manage_games'))

@game_bp.route('/bulk-delete', methods=['POST'])
@login_required
@game_manager_required
def bulk_delete_games():
    """Delete multiple games at once"""
    try:
        game_ids = request.form.getlist('game_ids')
        
        if not game_ids:
            flash('No games selected for deletion', 'warning')
            return redirect(url_for('game.manage_games'))
        
        deleted_count = 0
        cancelled_count = 0
        
        for game_id_str in game_ids:
            try:
                game_id = int(game_id_str)
                game = Game.query.get(game_id)
                if not game:
                    continue
                    
                assignments_count = GameAssignment.query.filter_by(game_id=game_id, is_active=True).count()
                
                if assignments_count > 0:
                    # Soft delete
                    game.status = 'cancelled'
                    try:
                        game.is_active = False
                    except:
                        pass
                    game.updated_at = datetime.utcnow()
                    GameAssignment.query.filter_by(game_id=game_id).update({'is_active': False})
                    cancelled_count += 1
                else:
                    # Hard delete
                    db.session.delete(game)
                    deleted_count += 1
                    
            except (ValueError, TypeError):
                continue
            except Exception as e:
                logger.error(f"Error processing game {game_id_str}: {e}")
                continue
        
        db.session.commit()
        
        message_parts = []
        if deleted_count > 0:
            message_parts.append(f"{deleted_count} game(s) permanently deleted")
        if cancelled_count > 0:
            message_parts.append(f"{cancelled_count} game(s) cancelled (had assignments)")
            
        if message_parts:
            flash(', '.join(message_parts), 'success')
        else:
            flash('No games were processed', 'info')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk delete: {e}")
        flash('Error deleting games.', 'error')
    
    return redirect(url_for('game.manage_games'))

# OFFICIAL ASSIGNMENT ROUTES from knowledge base
@game_bp.route('/official/assignments')
@login_required
def official_assignments():
    """Official's assignment dashboard"""
    try:
        return render_template('official/assignments.html', user=current_user)
    except Exception as e:
        logger.error(f"Error loading official assignments: {e}")
        flash('Error loading assignments.', 'error')
        return redirect(url_for('index'))

@game_bp.route('/official/assignments/data')
@login_required
def get_official_assignments_data():
    """Get assignments data for the current official - from knowledge base"""
    try:
        # Simple query - just get assignments for current user
        assignments = db.session.query(GameAssignment, Game, League, Location).join(
            Game, GameAssignment.game_id == Game.id
        ).join(
            League, Game.league_id == League.id
        ).join(
            Location, Game.location_id == Location.id
        ).filter(
            GameAssignment.user_id == current_user.id,
            GameAssignment.is_active == True
        ).all()
        
        # Format the data
        assignments_data = []
        for assignment, game, league, location in assignments:
            # Get partner officials for this game (excluding current user)
            partners = db.session.query(GameAssignment, User).join(
                User, GameAssignment.user_id == User.id
            ).filter(
                GameAssignment.game_id == game.id,
                GameAssignment.user_id != current_user.id,
                GameAssignment.is_active == True
            ).all()
            
            # Format partners data
            partners_data = []
            for partner_assignment, partner_user in partners:
                partners_data.append({
                    'name': partner_user.full_name,
                    'email': partner_user.email,
                    'phone': getattr(partner_user, 'phone', None),
                    'status': partner_assignment.status,
                    'position': partner_assignment.position
                })
            
            assignments_data.append({
                'id': assignment.id,
                'status': assignment.status,
                'partners': partners_data,
                'game': {
                    'id': game.id,
                    'date': game.date.strftime('%Y-%m-%d'),
                    'time': game.time.strftime('%H:%M'),
                    'home_team': game.home_team,
                    'away_team': game.away_team,
                    'notes': game.notes,
                    'fee_per_official': float(game.fee_per_official) if game.fee_per_official else None,
                    'league': {
                        'name': league.name,
                        'level': league.level,
                        'game_fee': float(getattr(league, 'game_fee', 0))
                    },
                    'location': {
                        'name': location.name,
                        'address': getattr(location, 'address', None),
                        'field': game.field_name
                    }
                }
            })
        
        return jsonify({
            'success': True,
            'assignments': assignments_data,
            'leagues': []
        })
        
    except Exception as e:
        logger.error(f"Error getting assignment data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading assignments'
        }), 500

@game_bp.route('/<int:game_id>/auto-assign', methods=['POST'])
@login_required
@game_manager_required
def auto_assign_officials(game_id):
    """Auto-assign officials based on ranking and availability"""
    game = Game.query.get_or_404(game_id)
    num_officials = request.form.get('num_officials', 2, type=int)
    
    # Get available officials not already assigned
    assigned_user_ids = [a.user_id for a in GameAssignment.query.filter_by(
        game_id=game_id, is_active=True
    ).all()]
    
    available_officials = User.query.filter(
        User.role.in_(['official', 'assigner', 'administrator', 'superadmin']),
        User.is_active == True,
        ~User.id.in_(assigned_user_ids)
    ).all()
    
    if len(available_officials) < num_officials:
        flash(f'Not enough available officials. Need {num_officials}, found {len(available_officials)}.', 'error')
        return redirect(url_for('game.assign_officials', game_id=game_id))
    
    # Simple auto-assignment logic (can be enhanced)
    # For now, just assign the first available officials
    assignments_created = 0
    
    for i in range(num_officials):
        if i < len(available_officials):
            official = available_officials[i]
            
            # Create assignment
            assignment = GameAssignment(
                game_id=game_id,
                user_id=official.id,
                position=f"Official {i+1}",
                assignment_type='auto',
                status='assigned'
            )
            
            try:
                db.session.add(assignment)
                assignments_created += 1
            except Exception as e:
                db.session.rollback()
                flash(f'Error assigning {official.full_name}: {str(e)}', 'error')
                continue
    
    if assignments_created > 0:
        try:
            db.session.commit()
            flash(f'Successfully auto-assigned {assignments_created} officials to the game.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving assignments: {str(e)}', 'error')
    
    return redirect(url_for('game.assign_officials', game_id=game_id))

@game_bp.route('/official/assignments/respond', methods=['POST'])
@login_required
def respond_to_assignment():
    """Handle official's response to assignment (accept/decline) - from knowledge base"""
    try:
        data = request.get_json()
        
        if not data or not all(key in data for key in ['assignment_id', 'status']):
            return jsonify({
                'success': False,
                'message': 'Missing required data'
            }), 400
        
        assignment_id = data['assignment_id']
        new_status = data['status']
        response_notes = data.get('notes', '')
        
        # Validate status
        if new_status not in ['accepted', 'declined']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Must be "accepted" or "declined"'
            }), 400
        
        # Get assignment and verify ownership
        assignment = GameAssignment.query.filter_by(
            id=assignment_id,
            user_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({
                'success': False,
                'message': 'Assignment not found or access denied'
            }), 404
        
        # Check if assignment can be changed
        if assignment.status in ['accepted', 'declined']:
            return jsonify({
                'success': False,
                'message': f'Assignment already {assignment.status}. Cannot change response.'
            }), 400
        
        # Update assignment
        if new_status == 'accepted':
            try:
                assignment.accept()  # Use model method if exists
            except:
                assignment.status = 'accepted'
                assignment.response_date = datetime.utcnow()
        else:
            try:
                assignment.decline(response_notes)  # Use model method if exists
            except:
                assignment.status = 'declined'
                assignment.response_date = datetime.utcnow()
                assignment.decline_reason = response_notes
        
        assignment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Assignment {new_status} successfully',
            'status': new_status,
            'response_date': assignment.response_date.isoformat() if assignment.response_date else None
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in respond_to_assignment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error updating assignment'
        }), 500

# API ROUTES
@game_bp.route('/api/games')
@login_required
def api_games():
    """API endpoint for game data"""
    try:
        games = Game.query.join(League).join(Location).all()
        return jsonify([{
            'id': game.id,
            'title': game.game_title,
            'date': game.date.isoformat() if game.date else None,
            'time': game.time.strftime('%H:%M') if game.time else None,
            'status': game.status,
            'league': game.league.name if game.league else None,
            'location': game.location.name if game.location else None
        } for game in games])
    except Exception as e:
        logger.error(f"Error in api_games: {e}")
        return jsonify({'error': 'Error loading games'}), 500

@game_bp.route('/api/league/<int:league_id>/fee')
@login_required
def api_league_fee(league_id):
    """Get default fee for a league"""
    try:
        league = League.query.get_or_404(league_id)
        fee = getattr(league, 'game_fee', 0)
        return jsonify({'fee': float(fee) if fee else 0})
    except Exception as e:
        logger.error(f"Error getting league fee: {e}")
        return jsonify({'fee': 0})

@game_bp.route('/api/location/<int:location_id>/fields')
@login_required
def api_location_fields(location_id):
    """Get field information for a location"""
    try:
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
            # Generate default field names based on our diagnostic results
            for i in range(1, location.field_count + 1):
                fields.append(f"Field {i}")
        
        return jsonify({'fields': fields})
        
    except Exception as e:
        logger.error(f"Error getting fields for location {location_id}: {e}")
        return jsonify({'error': str(e), 'fields': []}), 500

@game_bp.route('/<int:game_id>/view')
@login_required
def view_game(game_id):
    """View game details (read-only)"""
    from models.game import Game, GameAssignment
    from models.database import User
    
    game = Game.query.get_or_404(game_id)
    
    # Get game assignments
    assignments = GameAssignment.query.filter_by(
        game_id=game.id, 
        is_active=True
    ).join(User).all()
    
    # Calculate additional info
    assigned_officials = [assignment.user for assignment in assignments]
    
    return render_template('game/view_game.html',
                         game=game,
                         assignments=assignments,
                         assigned_officials=assigned_officials)

# EXPORT ROUTE
@game_bp.route('/export/games')
@login_required
@game_manager_required
def export_games():
    """Export games to CSV"""
    try:
        # Get same filters as manage_games
        search = request.args.get('search', '')
        league_filter = request.args.get('league', '')
        status_filter = request.args.get('status', '')
        time_period = request.args.get('time_period', 'all')
        
        # Build query
        query = Game.query.join(League).join(Location)
        
        # Apply filters (same as manage_games)
        if search:
            query = query.filter(
                or_(
                    Game.home_team.contains(search),
                    Game.away_team.contains(search),
                    League.name.contains(search),
                    Location.name.contains(search)
                )
            )
        
        if league_filter:
            try:
                query = query.filter(Game.league_id == int(league_filter))
            except:
                pass
        
        if status_filter:
            query = query.filter(Game.status == status_filter)
        
        # Apply time period filter
        today = date.today()
        if time_period == 'future':
            query = query.filter(Game.date >= today)
        elif time_period == 'past':
            query = query.filter(Game.date < today)
        elif time_period == 'today':
            query = query.filter(Game.date == today)
        
        games = query.order_by(Game.date.desc(), Game.time.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Time', 'Home Team', 'Away Team', 'League', 'Level',
            'Location', 'Field', 'Status', 'Fee', 'Officials', 'Duration', 'Notes'
        ])
        
        # Write game data
        for game in games:
            try:
                officials_count = game.assigned_officials_count
            except:
                officials_count = GameAssignment.query.filter_by(game_id=game.id, is_active=True).count()
            
            writer.writerow([
                game.date.strftime('%Y-%m-%d') if game.date else '',
                game.time.strftime('%H:%M') if game.time else '',
                game.home_team or '',
                game.away_team or '',
                game.league.name if game.league else '',
                game.level or '',
                game.location.name if game.location else '',
                game.field_name or '',
                game.status.title(),
                f"${game.fee_per_official:.2f}" if game.fee_per_official else '',
                officials_count,
                f"{game.estimated_duration} min" if game.estimated_duration else '',
                game.notes or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=games_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting games: {e}")
        flash('Error exporting games.', 'error')
        return redirect(url_for('game.manage_games'))

@game_bp.route('/')
@login_required
@game_manager_required
def index():
    """Redirect to manage games"""
    return redirect(url_for('game.manage_games'))

