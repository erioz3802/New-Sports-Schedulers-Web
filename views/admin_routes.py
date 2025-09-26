# views/admin_routes.py - Admin functionality (CORRECTED)
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from models.database import db, User
from utils.data_helpers import get_local_users, get_master_user_list

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin or assigner role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Allow superadmin, administrator, and assigner roles
        if current_user.role not in ['superadmin', 'administrator', 'assigner']:
            flash('Access denied. Administrator or Assigner role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with ROLE-BASED statistics"""
    try:
        # Get data specific to current user's permissions
        if current_user.role == 'superadmin':
            # Superadmin sees ALL data
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            
            # Get all leagues if available
            try:
                from models.league import League
                total_leagues = League.query.filter_by(is_active=True).count()
            except ImportError:
                total_leagues = 0
            
            # Get all games if available  
            try:
                from models.game import Game
                total_games = Game.query.filter_by(is_active=True).count()
            except ImportError:
                total_games = 0
                
            # Recent users (last 10)
            recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
            
        else:
            # Administrator and Assigner see LIMITED data
            accessible_users = get_local_users(current_user.id)
            total_users = len(accessible_users)
            active_users = len([u for u in accessible_users if u.get('is_active', True)])
            
            # Get leagues from user's scope
            try:
                from models.league import League, LeagueMembership
                user_leagues = LeagueMembership.query.filter_by(
                    user_id=current_user.id,
                    is_active=True
                ).all()
                total_leagues = len(user_leagues)
            except ImportError:
                total_leagues = 0
            
            # Get games from user's leagues
            total_games = 0  # Placeholder for now
            
            # Recent users from accessible users only
            recent_users = sorted(
                [User.query.get(u['id']) for u in accessible_users if User.query.get(u['id'])],
                key=lambda x: x.created_at or datetime.min,
                reverse=True
            )[:10]
        
        inactive_users = total_users - active_users
        
        # Role statistics
        role_stats = {}
        roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
        
        if current_user.role == 'superadmin':
            # System-wide role stats
            for role in roles:
                role_stats[role] = User.query.filter_by(role=role, is_active=True).count()
        else:
            # Limited role stats from accessible users
            accessible_users_data = get_local_users(current_user.id)
            for role in roles:
                role_stats[role] = len([u for u in accessible_users_data if u.get('role') == role and u.get('is_active', True)])
        
        # Dashboard context based on role
        if current_user.role == 'superadmin':
            dashboard_title = "Superadmin Dashboard"
            scope_description = "System-wide statistics"
        elif current_user.role == 'administrator':
            dashboard_title = "Administrator Dashboard"
            scope_description = "Your leagues and assigned users"
        elif current_user.role == 'assigner':
            dashboard_title = "Assigner Dashboard"
            scope_description = "Your assigned leagues and games"
        else:
            dashboard_title = "Dashboard"
            scope_description = "Loading..."
        
        return render_template('admin/dashboard.html',
                             dashboard_title=dashboard_title,
                             scope_description=scope_description,
                             total_users=total_users,
                             active_users=active_users,
                             inactive_users=inactive_users,
                             role_stats=role_stats,
                             recent_users=recent_users,
                             total_leagues=total_leagues,
                             total_games=total_games)
        
    except Exception as e:
        # Fallback dashboard if anything goes wrong
        print(f"Dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             dashboard_title="Dashboard Error",
                             scope_description="Please refresh the page",
                             total_users=0,
                             active_users=0,
                             inactive_users=0,
                             role_stats={},
                             recent_users=[],
                             total_leagues=0,
                             total_games=0)

@admin_bp.route('/users')
@login_required
@admin_required  
def manage_users():
    """User management page with search and filtering - UPDATED for local lists"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    # Get local users instead of all users
    local_users_data = get_local_users(current_user.id)
    
    # Apply filters
    filtered_users = []
    for user_data in local_users_data:
        # Apply search filter
        if search:
            search_match = (search.lower() in user_data['first_name'].lower() or
                          search.lower() in user_data['last_name'].lower() or
                          search.lower() in user_data['email'].lower())
            if not search_match:
                continue
        
        # Apply role filter
        if role_filter and user_data['role'] != role_filter:
            continue
            
        # Apply status filter
        if status_filter == 'active' and not user_data['is_active']:
            continue
        elif status_filter == 'inactive' and user_data['is_active']:
            continue
            
        filtered_users.append(user_data)
    
    # For superadmin, also get master list stats
    master_stats = None
    if current_user.role == 'superadmin':
        master_users = get_master_user_list()
        master_stats = {
            'total_users': len(master_users),
            'active_users': len([u for u in master_users if u.get('is_active', True)]),
            'by_role': {}
        }
        for user in master_users:
            role = user['role']
            if role not in master_stats['by_role']:
                master_stats['by_role'][role] = 0
            master_stats['by_role'][role] += 1
    
    return render_template('admin/manage_users.html',
                         users=filtered_users,
                         master_stats=master_stats,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user form"""
    if request.method == 'POST':
        # Validate form data
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'official')
        password = request.form.get('password', '')

        default_ranking = request.form.get('default_ranking')
        ranking_notes = request.form.get('ranking_notes', '').strip()
        
        # Validation
        errors = []
        if not email:
            errors.append('Email is required')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already exists')
        
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if role not in ['superadmin', 'administrator', 'assigner', 'official', 'viewer']:
            errors.append('Invalid role selected')
        
        # Check permission to create superadmin
        if role == 'superadmin' and not current_user.is_superadmin:
            errors.append('Only superadmins can create other superadmin accounts')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/add_user.html')
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone if phone else None,
            role=role,
            is_active=True,
            default_ranking=int(default_ranking) if default_ranking else 3,
            ranking_notes=ranking_notes if ranking_notes else None
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.full_name} created successfully!', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('admin/add_user.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""

    from models.database import db, User

    user = User.query.get_or_404(user_id)
    
    # Prevent editing other superadmins (unless current user is also superadmin)
    if user.is_superadmin and not current_user.is_superadmin:
        flash('You cannot edit superadmin accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if request.method == 'POST':
        # Update user details
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.phone = request.form.get('phone', '').strip()
        new_role = request.form.get('role')
        
        # Validate role change
        if new_role != user.role:
            if new_role == 'superadmin' and not current_user.is_superadmin:
                flash('Only superadmins can assign superadmin role.', 'error')
                return render_template('admin/edit_user.html', user=user)
            user.role = new_role
        
        # Handle password change
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return render_template('admin/edit_user.html', user=user)
            user.set_password(new_password)
        
        user.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'User {user.full_name} updated successfully!', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""

    from models.database import db, User

    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating self
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Prevent deactivating other superadmins
    if user.is_superadmin and not current_user.is_superadmin:
        flash('You cannot modify superadmin accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user.is_active = not user.is_active
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.full_name} has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user from local list (or master if superadmin)"""
    from models.database import User, db
    from models.local_user_list import LocalUserList
    
    if current_user.role == 'superadmin':
        # Superadmin can delete from master list
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        flash(f'{user.first_name} {user.last_name} deactivated from master list.', 'success')
    else:
        # Admin can only remove from local list
        local_user = LocalUserList.query.filter_by(
            admin_id=current_user.id, 
            user_id=user_id
        ).first()
        
        if local_user:
            local_user.is_active = False
            db.session.commit()
            flash('User removed from your local list.', 'success')
        else:
            flash('User not found in your local list.', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/api/user-stats')
@login_required
@admin_required
def user_stats_api():
    """API endpoint for user statistics - ROLE-BASED"""
    try:
        if current_user.role == 'superadmin':
            # System-wide statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            
            role_stats = {}
            roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
            for role in roles:
                role_stats[role] = User.query.filter_by(role=role, is_active=True).count()
            
            scope = 'system-wide'
        else:
            # Limited statistics for admin/assigner
            accessible_users = get_local_users(current_user.id)
            total_users = len(accessible_users)
            active_users = len([u for u in accessible_users if u.get('is_active', True)])
            
            role_stats = {}
            roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
            for role in roles:
                role_stats[role] = len([u for u in accessible_users if u.get('role') == role and u.get('is_active', True)])
            
            scope = 'your-leagues'
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'role_stats': role_stats,
            'scope': scope
        })
        
    except Exception as e:
        # Safe fallback
        return jsonify({
            'total_users': 0,
            'active_users': 0,
            'inactive_users': 0,
            'role_stats': {},
            'scope': 'error',
            'error': str(e)
        })

@admin_bp.route('/rankings/league/<int:league_id>')
@login_required
@admin_required
def league_rankings(league_id):
    """View/edit rankings for a specific league"""
    from models.availability import OfficialRanking
    from models.league import League
    from models.database import User
    
    league = League.query.get_or_404(league_id)
    
    # Get all active officials
    officials = User.query.filter(
        User.role.in_(['official', 'assigner', 'administrator']),
        User.is_active == True
    ).order_by(User.last_name, User.first_name).all()
    
    # Get existing rankings for this league
    rankings = {}
    league_rankings = OfficialRanking.query.filter_by(
        league_id=league_id,
        is_active=True
    ).all()
    for ranking in league_rankings:
        rankings[ranking.user_id] = ranking
    
    return render_template('admin/league_rankings.html',
                         league=league,
                         officials=officials,
                         rankings=rankings)

@admin_bp.route('/rankings/delete/<int:ranking_id>', methods=['POST'])
@login_required
@admin_required
def delete_ranking(ranking_id):
    """Delete an official ranking"""
    from models.availability import OfficialRanking
    
    ranking = OfficialRanking.query.get_or_404(ranking_id)
    
    try:
        user_name = ranking.user.full_name
        league_name = ranking.league.name
        
        # Soft delete by setting is_active to False
        ranking.is_active = False
        ranking.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Removed {user_name}\'s ranking from {league_name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ranking: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_rankings'))

@admin_bp.route('/rankings/statistics')
@login_required
@admin_required
def ranking_statistics():
    """View ranking statistics and analytics"""
    from models.availability import OfficialRanking
    from models.league import League
    from models.database import User
    
    # Get ranking distribution
    ranking_stats = db.session.query(
        OfficialRanking.ranking,
        db.func.count(OfficialRanking.id).label('count')
    ).filter(OfficialRanking.is_active == True)\
     .group_by(OfficialRanking.ranking).all()
    
    # Get rankings by league
    league_stats = db.session.query(
        League.name,
        db.func.count(OfficialRanking.id).label('ranked_officials'),
        db.func.avg(OfficialRanking.ranking).label('avg_ranking')
    ).join(OfficialRanking, League.id == OfficialRanking.league_id)\
     .filter(OfficialRanking.is_active == True)\
     .group_by(League.id, League.name).all()
    
    # Get top officials by league
    top_officials = db.session.query(
        User.full_name,
        League.name.label('league_name'),
        OfficialRanking.ranking
    ).join(OfficialRanking, User.id == OfficialRanking.user_id)\
     .join(League, OfficialRanking.league_id == League.id)\
     .filter(
         OfficialRanking.ranking == 5,
         OfficialRanking.is_active == True
     ).order_by(League.name, User.last_name).all()
    
    # Get officials without rankings
    unranked_officials = db.session.query(User).filter(
        User.role.in_(['official', 'assigner', 'administrator']),
        User.is_active == True,
        ~User.id.in_(
            db.session.query(OfficialRanking.user_id)
            .filter(OfficialRanking.is_active == True)
            .distinct()
        )
    ).count()
    
    return render_template('admin/ranking_statistics.html',
                         ranking_stats=ranking_stats,
                         league_stats=league_stats,
                         top_officials=top_officials,
                         unranked_officials=unranked_officials)

@admin_bp.route('/add-from-master', methods=['POST'])
@login_required
def add_user_from_master():
    """Add user(s) from master list to admin's local list"""
    if current_user.role == 'superadmin':
        flash('Superadmin has access to all users by default.', 'info')
        return redirect(url_for('admin.manage_users'))
    
    # Handle both single user_id and multiple user_id values
    user_ids = request.form.getlist('user_id')  # getlist gets all values
    
    if not user_ids:
        flash('User selection required.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Convert to integers and remove duplicates
    try:
        user_ids = list(set([int(uid) for uid in user_ids if uid.isdigit()]))
    except ValueError:
        flash('Invalid user selection.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if not user_ids:
        flash('No valid users selected.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    from models.database import User
    from models.local_user_list import LocalUserList
    from datetime import datetime
    
    added_users = []
    reactivated_users = []
    already_exists = []
    errors = []
    
    for user_id in user_ids:
        try:
            # Check if user exists in master list
            user = User.query.get(user_id)
            if not user or not user.is_active:
                errors.append(f'User ID {user_id} not found or inactive')
                continue
            
            # Check if already in local list
            existing = LocalUserList.query.filter_by(
                admin_id=current_user.id, 
                user_id=user_id
            ).first()
            
            if existing:
                if existing.is_active:
                    already_exists.append(user.full_name)
                else:
                    # Reactivate existing entry
                    existing.is_active = True
                    existing.added_at = datetime.utcnow()
                    existing.added_by = current_user.id
                    reactivated_users.append(user.full_name)
            else:
                # Create new local list entry
                local_entry = LocalUserList(
                    admin_id=current_user.id,
                    user_id=user_id,
                    added_by=current_user.id,
                    added_at=datetime.utcnow()
                )
                db.session.add(local_entry)
                added_users.append(user.full_name)
                
        except Exception as e:
            errors.append(f'Error adding user ID {user_id}: {str(e)}')
            continue
    
    # Commit all changes at once
    try:
        db.session.commit()
        
        # Create success messages
        messages = []
        if added_users:
            if len(added_users) == 1:
                messages.append(f'{added_users[0]} added to your local list.')
            else:
                messages.append(f'{len(added_users)} users added: {", ".join(added_users)}')
        
        if reactivated_users:
            if len(reactivated_users) == 1:
                messages.append(f'{reactivated_users[0]} reactivated in your local list.')
            else:
                messages.append(f'{len(reactivated_users)} users reactivated: {", ".join(reactivated_users)}')
        
        if already_exists:
            if len(already_exists) == 1:
                messages.append(f'{already_exists[0]} was already in your local list.')
            else:
                messages.append(f'{len(already_exists)} users already in list: {", ".join(already_exists)}')
        
        # Flash success messages
        for message in messages:
            flash(message, 'success' if 'added' in message or 'reactivated' in message else 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Database error: {str(e)}', 'error')
    
    # Flash any errors
    for error in errors:
        flash(error, 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/league-assignments')
@login_required
def league_assignments():
    """League assignment interface (superadmin only) - DEBUG VERSION"""
    if current_user.role != 'superadmin':
        flash('Access denied. Superadmin role required.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Get all administrators (exclude superadmin and current user)
    administrators = User.query.filter(
        User.role == 'administrator',
        User.is_active == True,
        User.id != current_user.id
    ).all()
    
    print(f"DEBUG: Found {len(administrators)} administrators")
    for admin in administrators:
        print(f"DEBUG: Administrator - {admin.full_name} (ID: {admin.id})")
    
    # Get all active leagues
    from models.league import League, LeagueMembership
    leagues = League.query.filter_by(is_active=True).all()
    print(f"DEBUG: Found {len(leagues)} active leagues")
    
    # Process administrators with ALL their league memberships
    for admin in administrators:
        print(f"DEBUG: Processing admin {admin.full_name} (ID: {admin.id})")
        
        # Get ALL active memberships for this admin
        memberships = LeagueMembership.query.filter_by(
            user_id=admin.id, 
            is_active=True
        ).all()
        
        print(f"DEBUG: Found {len(memberships)} memberships for {admin.full_name}")
        
        assigned_leagues = []
        for membership in memberships:
            print(f"DEBUG: Processing membership ID {membership.id}")
            print(f"DEBUG: Membership league: {membership.league}")
            print(f"DEBUG: Membership assigned_by: {membership.assigned_by}")
            
            if membership.league:
                # Determine the source and permission level
                if membership.assigned_by:
                    source = 'assigned'
                    permission_level = membership.permission_level or 'admin'
                else:
                    source = 'member'
                    permission_level = membership.role_in_league or 'admin'
                
                league_data = {
                    'id': membership.league.id,
                    'name': membership.league.name,
                    'level': membership.league.level,
                    'permission_level': permission_level,
                    'membership_id': membership.id,
                    'source': source
                }
                assigned_leagues.append(league_data)
                print(f"DEBUG: Added league {membership.league.name} as {source}")
            else:
                print(f"DEBUG: Membership {membership.id} has no league!")
        
        admin.assigned_leagues = assigned_leagues
        print(f"DEBUG: Final assigned_leagues for {admin.full_name}: {len(assigned_leagues)} leagues")
        for league in assigned_leagues:
            print(f"  - {league['name']} ({league['source']})")
    
    # Calculate assignment statistics
    total_assignments = LeagueMembership.query.filter(
        LeagueMembership.is_active == True,
        LeagueMembership.assigned_by.isnot(None)
    ).count()
    
    active_admins = len([admin for admin in administrators if hasattr(admin, 'assigned_leagues') and admin.assigned_leagues])
    unassigned_leagues = len([league for league in leagues if not any(
        membership.league_id == league.id and membership.is_active
        for membership in LeagueMembership.query.all()
    )])
    
    assignment_stats = {
        'total_assignments': total_assignments,
        'active_admins': active_admins,
        'unassigned_leagues': unassigned_leagues,
        'avg_assignments': round(total_assignments / max(len(administrators), 1), 1)
    }
    
    print(f"DEBUG: Final stats - {assignment_stats}")
    print(f"DEBUG: Rendering template with {len(administrators)} administrators")
    
    return render_template('admin/league_assignments.html', 
                         administrators=administrators,
                         leagues=leagues,
                         assignment_stats=assignment_stats)


@admin_bp.route('/assign-league', methods=['POST'])
@login_required
def assign_league_to_admin():
    """Assign league to administrator (superadmin only)"""
    if current_user.role != 'superadmin':
        flash('Access denied. Superadmin role required.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    admin_id = request.form.get('admin_id', type=int)
    league_id = request.form.get('league_id', type=int)
    permission_level = request.form.get('permission_level', 'admin')
    
    # Validation
    if not admin_id or not league_id:
        flash('Administrator and league selection required.', 'error')
        return redirect(url_for('admin.league_assignments'))
    
    # Validate admin exists and is administrator
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'administrator':
        flash('Invalid administrator selected.', 'error')
        return redirect(url_for('admin.league_assignments'))
    
    # Validate league exists
    from models.league import League, LeagueMembership
    league = League.query.get(league_id)
    if not league:
        flash('Invalid league selected.', 'error')
        return redirect(url_for('admin.league_assignments'))
    
    # Check for existing assignment
    existing = LeagueMembership.query.filter_by(
        user_id=admin_id, 
        league_id=league_id
    ).first()
    
    try:
        if existing:
            if existing.is_active and existing.assigned_by:
                flash(f'{admin.full_name} is already assigned to {league.name}.', 'warning')
            else:
                # Update existing assignment
                existing.is_active = True
                existing.permission_level = permission_level
                existing.assigned_by = current_user.id
                existing.assigned_at = datetime.utcnow()
                existing.removed_by = None
                existing.removed_at = None
                db.session.commit()
                flash(f'{admin.full_name} assigned to {league.name} with {permission_level} permissions.', 'success')
        else:
            # Create new assignment
            membership = LeagueMembership(
                user_id=admin_id,
                league_id=league_id,
                role_in_league='admin',  # For assigned admins
                permission_level=permission_level,
                assigned_by=current_user.id,
                assigned_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(membership)
            db.session.commit()
            flash(f'{admin.full_name} assigned to {league.name} with {permission_level} permissions.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash('Error creating league assignment. Please try again.', 'error')
        print(f"League assignment error: {str(e)}")
    
    return redirect(url_for('admin.league_assignments'))


@admin_bp.route('/remove-league-assignment', methods=['POST'])
@login_required 
def remove_league_assignment():
    """Remove league assignment (superadmin only)"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json()
    membership_id = data.get('membership_id')
    
    if not membership_id:
        return jsonify({'success': False, 'message': 'Missing membership ID'})
    
    try:
        from models.league import LeagueMembership
        membership = LeagueMembership.query.get(membership_id)
        
        if not membership:
            return jsonify({'success': False, 'message': 'Assignment not found'})
        
        # Soft delete assignment
        membership.is_active = False
        membership.removed_by = current_user.id
        membership.removed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'League assignment removed successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error removing assignment: {str(e)}'})


@admin_bp.route('/api/admin-assignments/<int:admin_id>')
@login_required
def api_admin_assignments(admin_id):
    """API endpoint to get admin's league assignments (superadmin only)"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Access denied'}), 403
    
    from models.league import LeagueMembership
    memberships = LeagueMembership.query.filter_by(
        user_id=admin_id, 
        is_active=True
    ).filter(LeagueMembership.assigned_by.isnot(None)).all()
    
    assignments = []
    for membership in memberships:
        if membership.league:
            assignments.append({
                'membership_id': membership.id,
                'league_name': membership.league.name,
                'league_level': membership.league.level,
                'permission_level': membership.permission_level or 'admin',
                'assigned_date': membership.assigned_at.strftime('%Y-%m-%d') if membership.assigned_at else 'N/A'
            })
    
    return jsonify({'assignments': assignments})

@admin_bp.route('/api/master-users')
@login_required
def api_master_users():
    """API endpoint to get master users for local list modal"""
    if current_user.role == 'superadmin':
        # Superadmin doesn't need this functionality
        return jsonify([])
    
    # Get all active users not already in admin's local list
    from models.database import User, db
    from models.local_user_list import LocalUserList
    
    # Get IDs of users already in admin's local list
    existing_local_users = LocalUserList.query.filter_by(
        admin_id=current_user.id,
        is_active=True
    ).all()
    existing_user_ids = [lu.user_id for lu in existing_local_users]
    
    # Get all active users not in local list
    available_users = User.query.filter(
        ~User.id.in_(existing_user_ids),
        User.is_active == True,
        User.id != current_user.id  # Don't include self
    ).all()
    
    users_data = []
    for user in available_users:
        users_data.append({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role
        })
    
    return jsonify(users_data)

# Let's check the database directly to see what's happening
# Add this temporary debug route to your views/admin_routes.py:

@admin_bp.route('/debug-memberships')
@login_required
def debug_memberships():
    """Debug route to see what's in the database"""
    if current_user.role != 'superadmin':
        return "Access denied"
    
    from models.league import League, LeagueMembership
    
    # Get all memberships
    memberships = LeagueMembership.query.all()
    
    debug_info = []
    debug_info.append("<h3>All League Memberships in Database:</h3>")
    
    for membership in memberships:
        user_name = membership.user.full_name if membership.user else "Unknown User"
        league_name = membership.league.name if membership.league else "Unknown League"
        
        debug_info.append(f"<p><strong>Membership ID:</strong> {membership.id}<br>")
        debug_info.append(f"<strong>User:</strong> {user_name} (ID: {membership.user_id})<br>")
        debug_info.append(f"<strong>League:</strong> {league_name} (ID: {membership.league_id})<br>")
        debug_info.append(f"<strong>Role:</strong> {membership.role_in_league}<br>")
        debug_info.append(f"<strong>Is Active:</strong> {membership.is_active}<br>")
        debug_info.append(f"<strong>Assigned By:</strong> {membership.assigned_by}<br>")
        debug_info.append(f"<strong>Permission Level:</strong> {membership.permission_level}<br>")
        debug_info.append(f"<strong>Assigned At:</strong> {membership.assigned_at}</p><hr>")
    
    if not memberships:
        debug_info.append("<p>No league memberships found in database!</p>")
    
    # Get all administrators
    administrators = User.query.filter_by(role='administrator', is_active=True).all()
    debug_info.append(f"<h3>Administrators Found: {len(administrators)}</h3>")
    
    for admin in administrators:
        debug_info.append(f"<p><strong>{admin.full_name}</strong> (ID: {admin.id}, Email: {admin.email})</p>")
    
    # Get all leagues
    leagues = League.query.filter_by(is_active=True).all()
    debug_info.append(f"<h3>Active Leagues Found: {len(leagues)}</h3>")
    
    for league in leagues:
        debug_info.append(f"<p><strong>{league.name}</strong> - {league.level} (ID: {league.id})</p>")
    
    return "<br>".join(debug_info)
