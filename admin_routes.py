# views/admin_routes.py - Admin functionality (CORRECTED)
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from models.database import db, User

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_users:
            flash('Access denied. Administrator role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with user statistics"""
    # Import here to avoid circular imports
    from models.database import db, User
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = total_users - active_users
    
    # Role statistics
    role_stats = {}
    roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
    for role in roles:
        role_stats[role] = User.query.filter_by(role=role, is_active=True).count()
    
    # Recent users (last 10)
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         inactive_users=inactive_users,
                         role_stats=role_stats,
                         recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@admin_required  
def manage_users():
    """User management page with search and filtering"""

    from models.database import db, User

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search)
            )
        )
    
    # Apply role filter
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Paginate results
    users = query.order_by(User.last_name, User.first_name).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/manage_users.html',
                         users=users,
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
    """Delete user (superadmin only)"""
    if not current_user.is_superadmin:
        flash('Only superadmins can delete users.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user_name = user.full_name
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user_name} has been deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/api/user-stats')
@login_required
@admin_required
def user_stats_api():
    """API endpoint for user statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    role_stats = {}
    roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
    for role in roles:
        role_stats[role] = User.query.filter_by(role=role, is_active=True).count()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'role_stats': role_stats
    })

# ADD THESE ROUTES TO THE END OF views/admin_routes.py

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

