# views/bulk_routes.py - Bulk Operations for Games and Users
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import csv
import io
from functools import wraps

# Import pandas with error handling for missing dependency
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

bulk_bp = Blueprint('bulk', __name__)

def admin_required(f):
    """Decorator to require admin role for bulk operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_users:
            flash('Access denied. Administrator role required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@bulk_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Bulk operations dashboard"""
    # Use conditional imports to avoid circular dependency issues
    try:
        from models.database import db, User
        from models.league import League, Location
        from models.game import Game
        
        # Statistics for dashboard
        stats = {
            'total_users': User.query.count(),
            'total_leagues': League.query.count(),
            'total_locations': Location.query.count(),
            'total_games': Game.query.count(),
            'recent_uploads': []  # Will implement upload history later
        }
    except ImportError as e:
        # Graceful fallback if models don't exist yet
        flash(f'Some features not available: {str(e)}', 'warning')
        stats = {
            'total_users': 0,
            'total_leagues': 0,
            'total_locations': 0,
            'total_games': 0,
            'recent_uploads': []
        }
    
    return render_template('bulk/dashboard.html', stats=stats)

@bulk_bp.route('/games/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_games():
    """Upload games from CSV file"""
    # Check if pandas is available
    if not PANDAS_AVAILABLE:
        flash('Bulk operations require pandas library. Please install: pip install pandas openpyxl', 'error')
        return redirect(url_for('bulk.dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            flash('Invalid file type. Please upload CSV or Excel files only.', 'error')
            return redirect(request.url)
        
        try:
            # Process the uploaded file
            results = process_games_file(file)
            
            if results['success']:
                flash(f'Successfully processed {results["created"]} games. {results["errors"]} errors.', 'success')
                return redirect(url_for('bulk.upload_results', upload_id=results['upload_id']))
            else:
                flash(f'Upload failed: {results["message"]}', 'error')
                return render_template('bulk/upload_games.html', 
                                     errors=results.get('validation_errors', []),
                                     leagues=[], locations=[])
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form with conditional model loading
    try:
        from models.league import League, Location
        leagues = League.query.filter_by(is_active=True).all()
        locations = Location.query.filter_by(is_active=True).all()
    except ImportError:
        # Graceful fallback if models don't exist
        leagues = []
        locations = []
        flash('League and Location models not available. Please ensure all database models are properly set up.', 'warning')
    
    return render_template('bulk/upload_games.html', leagues=leagues, locations=locations)

@bulk_bp.route('/games/template')
@login_required
@admin_required
def download_games_template():
    """Download CSV template for games upload"""
    from flask import Response
    
    # Create CSV template with headers and example data
    template_data = [
        ['league_id', 'location_id', 'date', 'time', 'home_team', 'away_team', 'level', 'field_name', 'fee_per_official', 'notes'],
        ['1', '1', '2025-10-15', '19:00', 'Home Team', 'Away Team', 'Varsity', 'Field 1', '75.00', 'Championship game'],
        ['1', '2', '2025-10-16', '18:30', 'Team A', 'Team B', 'JV', 'Main Field', '60.00', 'Regular season'],
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    for row in template_data:
        writer.writerow(row)
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=games_upload_template.csv'}
    )
    return response

@bulk_bp.route('/users/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_users():
    """Upload users from CSV file"""
    if not PANDAS_AVAILABLE:
        flash('Bulk operations require pandas library. Please install: pip install pandas openpyxl', 'error')
        return redirect(url_for('bulk.dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        try:
            results = process_users_file(file)
            
            if results['success']:
                flash(f'Successfully processed {results["created"]} users. {results["errors"]} errors.', 'success')
                return redirect(url_for('bulk.upload_results', upload_id=results['upload_id']))
            else:
                flash(f'Upload failed: {results["message"]}', 'error')
                return render_template('bulk/upload_users.html', 
                                     errors=results.get('validation_errors', []))
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('bulk/upload_users.html')

@bulk_bp.route('/users/template')
@login_required
@admin_required
def download_users_template():
    """Download CSV template for users upload"""
    from flask import Response
    
    template_data = [
        ['first_name', 'last_name', 'email', 'phone', 'role'],
        ['John', 'Smith', 'john.smith@email.com', '555-123-4567', 'official'],
        ['Jane', 'Doe', 'jane.doe@email.com', '555-987-6543', 'assigner'],
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    for row in template_data:
        writer.writerow(row)
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users_upload_template.csv'}
    )
    return response

@bulk_bp.route('/results/<upload_id>')
@login_required
@admin_required
def upload_results(upload_id):
    """Show results of bulk upload operation"""
    return render_template('bulk/upload_results.html', upload_id=upload_id)

def process_games_file(file):
    """Process uploaded games file and create games"""
    # Check pandas availability
    if not PANDAS_AVAILABLE:
        return {
            'success': False,
            'message': 'pandas library not available. Please install: pip install pandas openpyxl'
        }
    
    try:
        # Conditional imports to avoid circular dependencies
        from models.database import db
        from models.league import League, Location
        from models.game import Game
        
        # Read file based on extension
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['league_id', 'location_id', 'date', 'time', 'home_team', 'away_team']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            }
        
        created_count = 0
        error_count = 0
        validation_errors = []
        upload_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for index, row in df.iterrows():
            try:
                # Validate league exists
                league = League.query.get(row['league_id'])
                if not league:
                    validation_errors.append(f'Row {index + 2}: League ID {row["league_id"]} not found')
                    error_count += 1
                    continue
                
                # Validate location exists
                location = Location.query.get(row['location_id'])
                if not location:
                    validation_errors.append(f'Row {index + 2}: Location ID {row["location_id"]} not found')
                    error_count += 1
                    continue
                
                # Parse date and time
                game_date = pd.to_datetime(row['date']).date()
                game_time = pd.to_datetime(row['time']).time()
                
                # Check for conflicts (basic check)
                existing_game = Game.query.filter_by(
                    location_id=row['location_id'],
                    date=game_date,
                    time=game_time
                ).first()
                
                if existing_game:
                    validation_errors.append(f'Row {index + 2}: Time conflict - game already exists at this location/time')
                    error_count += 1
                    continue
                
                # Create game
                game = Game(
                    league_id=row['league_id'],
                    location_id=row['location_id'],
                    date=game_date,
                    time=game_time,
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    level=row.get('level', ''),
                    field_name=row.get('field_name', ''),
                    fee_per_official=row.get('fee_per_official', league.game_fee),
                    notes=row.get('notes', ''),
                    status='draft'
                )
                
                db.session.add(game)
                created_count += 1
                
            except Exception as e:
                validation_errors.append(f'Row {index + 2}: {str(e)}')
                error_count += 1
        
        if created_count > 0:
            db.session.commit()
        
        return {
            'success': True,
            'created': created_count,
            'errors': error_count,
            'validation_errors': validation_errors,
            'upload_id': upload_id
        }
    
    except ImportError as e:
        return {
            'success': False,
            'message': f'Required models not available: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def process_users_file(file):
    """Process uploaded users file and create users"""
    # Check pandas availability
    if not PANDAS_AVAILABLE:
        return {
            'success': False,
            'message': 'pandas library not available. Please install: pip install pandas openpyxl'
        }
    
    try:
        # Conditional imports to avoid circular dependencies
        from models.database import db, User
        
        # Read file
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['first_name', 'last_name', 'email', 'role']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            }
        
        created_count = 0
        error_count = 0
        validation_errors = []
        upload_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        valid_roles = ['superadmin', 'administrator', 'assigner', 'official', 'viewer']
        
        for index, row in df.iterrows():
            try:
                # Validate role
                if row['role'] not in valid_roles:
                    validation_errors.append(f'Row {index + 2}: Invalid role "{row["role"]}"')
                    error_count += 1
                    continue
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=row['email'].lower()).first()
                if existing_user:
                    validation_errors.append(f'Row {index + 2}: User with email {row["email"]} already exists')
                    error_count += 1
                    continue
                
                # Create user
                user = User(
                    first_name=row['first_name'].strip(),
                    last_name=row['last_name'].strip(),
                    email=row['email'].lower().strip(),
                    phone=row.get('phone', '').strip(),
                    role=row['role'],
                    is_active=True
                )
                
                # Set default password (they'll need to change it)
                user.set_password('password123')
                
                db.session.add(user)
                created_count += 1
                
            except Exception as e:
                validation_errors.append(f'Row {index + 2}: {str(e)}')
                error_count += 1
        
        if created_count > 0:
            db.session.commit()
        
        return {
            'success': True,
            'created': created_count,
            'errors': error_count,
            'validation_errors': validation_errors,
            'upload_id': upload_id
        }
    
    except ImportError as e:
        return {
            'success': False,
            'message': f'User model not available: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
