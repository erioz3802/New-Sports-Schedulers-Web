# views/league_routes.py - League Management Routes (Simple Version)
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from models.database import db, User
from models.league import League, Location

league_bp = Blueprint('league', __name__)

def league_admin_required(f):
    """Decorator to require league admin permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not hasattr(current_user, 'can_manage_users') or not current_user.can_manage_users:
            flash('Access denied. League administrator role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@league_bp.route('/dashboard')
@login_required
@league_admin_required
def dashboard():
    """League management dashboard"""
    leagues = League.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).limit(10).all()
    
    # Statistics
    total_leagues = League.query.count()
    active_leagues = League.query.filter_by(is_active=True).count()
    total_locations = Location.query.count()
    
    return render_template('placeholder.html', title='League Management - Coming Soon')

@league_bp.route('/add_league')
@login_required
@league_admin_required
def add_league():
    """Add league placeholder"""
    return render_template('placeholder.html', title='Add League - Coming Soon')

@league_bp.route('/manage_locations')
@login_required
@league_admin_required
def manage_locations():
    """Location management placeholder"""
    return render_template('placeholder.html', title='Location Management - Coming Soon')
