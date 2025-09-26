# views/league_routes.py - League Management Routes
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
        if not current_user.can_manage_users:
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
    
    return render_template('league/dashboard.html',
                         leagues=leagues,
                         locations=locations,
                         total_leagues=total_leagues,
                         active_leagues=active_leagues,
                         total_locations=total_locations)

@league_bp.route('/manage')
@login_required
@league_admin_required
def manage_leagues():
    """League management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = League.query
    
    if search:
        query = query.filter(
            db.or_(
                League.name.contains(search),
                League.level.contains(search)
            )
        )
    
    leagues = query.order_by(League.name, League.level).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('league/manage_leagues.html',
                         leagues=leagues,
                         search=search)

@league_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_league():
    """Add a new league with enhanced features."""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            level = request.form.get('level', '').strip()
            description = request.form.get('description', '').strip()
            
            # Get the enhanced fields
            officials_count_raw = request.form.get('default_officials_count', '').strip()
            default_officials_count = int(officials_count_raw) if officials_count_raw else 2
            game_fee_raw = request.form.get('game_fee', '').strip()
            game_fee = float(game_fee_raw) if game_fee_raw else 0.00
            scheduling_fee_raw = request.form.get('default_scheduling_fee', '').strip()
            default_scheduling_fee = float(scheduling_fee_raw) if scheduling_fee_raw else 0.00
            billing_recipient = request.form.get('billing_recipient', '').strip()
            billing_amount_raw = request.form.get('billing_amount', '').strip()
            billing_amount = float(billing_amount_raw) if billing_amount_raw else 0.00
            
            # Validate input
            if not name or not level:
                flash('League name and level are required.', 'error')
                return render_template('league/add_league.html')
            
            if default_officials_count < 1 or default_officials_count > 6:
                flash('Number of officials must be between 1 and 6.', 'error')
                return render_template('league/add_league.html')
            
            # Check if league already exists
            existing_league = League.query.filter_by(name=name, level=level).first()
            if existing_league:
                flash('A league with this name and level already exists.', 'error')
                return render_template('league/add_league.html')
            
            # Create the new league with ALL fields INCLUDING created_by
            league = League(
                name=name,
                level=level,
                description=description,
                default_officials_count=default_officials_count,
                game_fee=game_fee,
                default_scheduling_fee=default_scheduling_fee,
                billing_recipient=billing_recipient,
                billing_amount=billing_amount,
                created_by=current_user.id,  
                is_active=True
            )
            
            db.session.add(league)
            db.session.flush()  # Get the league ID before committing
            
            # ← ADD THIS SECTION: Automatically create membership for the creator
            from models.league import LeagueMembership
            membership = LeagueMembership(
                user_id=current_user.id,
                league_id=league.id,
                role_in_league='admin',
                permission_level='owner',  # Creator has owner permissions
                is_active=True
            )
            db.session.add(membership)
            
            db.session.commit()
            
            flash(f'League "{league.full_name}" created successfully! You have automatic access as the creator with {default_officials_count} officials per game.', 'success')
            return redirect(url_for('league.manage_leagues'))
            
        except ValueError:
            flash('Please enter valid numeric values.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating league: {str(e)}', 'error')
    
    return render_template('league/add_league.html')
@league_bp.route('/<int:league_id>/edit', methods=['GET', 'POST'])
@login_required
@league_admin_required
def edit_league(league_id):
    """Edit league details"""
    league = League.query.get_or_404(league_id)
    
    if request.method == 'POST':
        try:  # Added try block for better error handling
            league.name = request.form.get('name', '').strip()
            league.level = request.form.get('level', '').strip()
            game_fee_raw = request.form.get('game_fee', '').strip()
            league.game_fee = float(game_fee_raw) if game_fee_raw else 0.00
            billing_amount_raw = request.form.get('billing_amount', '').strip()
            league.billing_amount = float(billing_amount_raw) if billing_amount_raw else 0.00
            league.billing_recipient = request.form.get('billing_recipient', '').strip()
            league.description = request.form.get('description', '').strip()
            officials_count_raw = request.form.get('default_officials_count', '').strip()
            league.default_officials_count = int(officials_count_raw) if officials_count_raw else 2
            league.default_officials_count = int(officials_count_raw) if officials_count_raw else 2
            scheduling_fee_raw = request.form.get('default_scheduling_fee', '').strip()
            league.default_scheduling_fee = float(scheduling_fee_raw) if scheduling_fee_raw else 0.00
            league.updated_at = datetime.utcnow()
            
            # Validate the new fields
            if league.default_officials_count < 1 or league.default_officials_count > 6:
                flash('Number of officials must be between 1 and 6.', 'error')
                return render_template('league/edit_league.html', league=league)
            
            # Validate required fields
            if not league.name or not league.level:
                flash('League name and level are required.', 'error')
                return render_template('league/edit_league.html', league=league)
            
            db.session.commit()
            flash(f'League "{league.full_name}" updated successfully!', 'success')
            return redirect(url_for('league.manage_leagues'))
            
        except ValueError:
            flash('Please enter valid numeric values.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating league: {str(e)}', 'error')
    
    return render_template('league/edit_league.html', league=league)
@league_bp.route('/<int:league_id>/toggle-status', methods=['POST'])
@login_required
@league_admin_required
def toggle_league_status(league_id):
    """Toggle league active/inactive status"""
    league = League.query.get_or_404(league_id)
    
    league.is_active = not league.is_active
    league.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        status = 'activated' if league.is_active else 'deactivated'
        flash(f'League "{league.full_name}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating league status: {str(e)}', 'error')
    
    return redirect(url_for('league.manage_leagues'))

# Location Management Routes

@league_bp.route('/locations')
@login_required
@league_admin_required
def manage_locations():
    """Location management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Location.query
    
    if search:
        query = query.filter(
            db.or_(
                Location.name.contains(search),
                Location.city.contains(search),
                Location.address.contains(search)
            )
        )
    
    locations = query.order_by(Location.name).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('league/manage_locations.html',
                         locations=locations,
                         search=search)

@league_bp.route('/locations/add', methods=['GET', 'POST'])
@login_required
@league_admin_required
def add_location():
    """Add new location"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        
        contact_name = request.form.get('contact_name', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        
        field_count = request.form.get('field_count', 1, type=int)
        notes = request.form.get('notes', '').strip()
        
        # ✅ FIXED: Extract coordinate data properly
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        place_id = request.form.get('place_id', '').strip()
        
        # Validation
        if not name:
            flash('Location name is required', 'error')
            return render_template('league/add_location.html')
        
        # ✅ FIXED: Create location without google_maps_link to avoid setter error
        location = Location(
            name=name,
            address=address if address else None,
            city=city if city else None,
            state=state if state else None,
            zip_code=zip_code if zip_code else None,
            contact_name=contact_name if contact_name else None,
            contact_email=contact_email if contact_email else None,
            contact_phone=contact_phone if contact_phone else None,
            field_count=field_count,
            notes=notes if notes else None,
            latitude=latitude,
            longitude=longitude,
            place_id=place_id if place_id else None
        )
                  
        try:
            db.session.add(location)
            db.session.commit()
            flash(f'Location "{location.name}" created successfully!', 'success')
            return redirect(url_for('league.manage_locations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating location: {str(e)}', 'error')
    
    return render_template('league/add_location.html')

@league_bp.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@league_admin_required
def edit_location(location_id):
    """Edit location details"""
    location = Location.query.get_or_404(location_id)
    
    if request.method == 'POST':
        location.name = request.form.get('name', '').strip()
        location.address = request.form.get('address', '').strip()
        location.city = request.form.get('city', '').strip()
        location.state = request.form.get('state', '').strip()
        location.zip_code = request.form.get('zip_code', '').strip()
        location.contact_name = request.form.get('contact_name', '').strip()
        location.contact_email = request.form.get('contact_email', '').strip()
        location.contact_phone = request.form.get('contact_phone', '').strip()
        location.field_count = request.form.get('field_count', 1, type=int)
        location.notes = request.form.get('notes', '').strip()
        location.updated_at = datetime.utcnow()
        
        # Validation
        if not location.name:
            flash('Location name is required', 'error')
            return render_template('league/edit_location.html', location=location)
        
        try:
            db.session.commit()
            flash(f'Location "{location.name}" updated successfully!', 'success')
            return redirect(url_for('league.manage_locations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating location: {str(e)}', 'error')
    
    return render_template('league/edit_location.html', location=location)

@league_bp.route('/locations/<int:location_id>/toggle-status', methods=['POST'])
@login_required
@league_admin_required
def toggle_location_status(location_id):
    """Toggle location active/inactive status"""
    location = Location.query.get_or_404(location_id)
    
    location.is_active = not location.is_active
    location.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        status = 'activated' if location.is_active else 'deactivated'
        flash(f'Location "{location.name}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating location status: {str(e)}', 'error')
    
    return redirect(url_for('league.manage_locations'))

@league_bp.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
@league_admin_required
def delete_location(location_id):
    """Delete location (superadmin only, no games scheduled)"""
    if not current_user.is_superadmin:
        flash('Only superadmins can delete locations.', 'error')
        return redirect(url_for('league.manage_locations'))
    
    location = Location.query.get_or_404(location_id)
    
    # Check if location has any games
    if location.games_count > 0:
        flash(f'Cannot delete location "{location.name}" - it has {location.games_count} scheduled games.', 'error')
        return redirect(url_for('league.manage_locations'))
    
    location_name = location.name
    
    try:
        db.session.delete(location)
        db.session.commit()
        flash(f'Location "{location_name}" has been deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting location: {str(e)}', 'error')
    
    return redirect(url_for('league.manage_locations'))

@league_bp.route('/api/leagues')
@login_required
@league_admin_required
def api_leagues():
    """API endpoint for league data"""
    leagues = League.query.filter_by(is_active=True).all()
    return jsonify([league.to_dict() for league in leagues])

@league_bp.route('/api/locations')
@login_required
@league_admin_required
def api_locations():
    """API endpoint for location data"""
    locations = Location.query.filter_by(is_active=True).all()
    return jsonify([location.to_dict() for location in locations])
