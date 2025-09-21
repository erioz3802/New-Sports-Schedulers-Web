# app.py - Sports Schedulers - Production Ready
# JES Baseball LLC - 2025

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user
from datetime import datetime
import os

# Load environment variables
if os.environ.get('RENDER'):
    # Production - Render sets environment variables automatically
    pass
else:
    # Development - load from .env file
    from dotenv import load_dotenv
    load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Production-ready configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sports-scheduler-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration for both development and production
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production database (PostgreSQL on Render)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_scheduler.db'

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = 'AIzaSyBG6YHNSe5JjnDW7mnPa32v1OFU4liwddE'

# Initialize database and Flask-Login
from models.database import db, User, create_demo_users

# Initialize the database with the app
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user_role():
    """Make user role available in all templates"""
    if current_user.is_authenticated:
        return {'user_role': current_user.role, 'current_user': current_user}
    return {'user_role': None, 'current_user': None}

# Main routes
@app.route('/')
def index():
    """Main dashboard - role-based landing page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get dashboard stats based on user role
    dashboard_data = {}
    
    if current_user.can_manage_users:
        try:
            from models.league import Location
            location_count = Location.query.count()
        except:
            location_count = 0
        
        dashboard_data.update({
            'total_users': 4,  # Demo count
            'total_leagues': 3,  # Demo count
            'total_locations': location_count,
            'total_games': 8,  # Demo count
            'recent_games': []
        })
    
    if current_user.role in ['assigner', 'administrator', 'superadmin']:
        dashboard_data.update({
            'draft_games': 2,
            'ready_games': 1,
            'released_games': 3,
            'unassigned_games': 1
        })
    
    if current_user.role == 'official':
        dashboard_data.update({
            'upcoming_assignments': 2,
            'total_earnings_ytd': 450.00,
            'games_worked_ytd': 15
        })
    
    return render_template('dashboard.html', 
                         title=f'{current_user.role.title()} Dashboard',
                         user=current_user,
                         **dashboard_data)

@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect to main dashboard"""
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile management"""
    return render_template('profile.html', user=current_user)

@app.route('/help')
def help_page():
    """Help and FAQ page"""
    return render_template('help.html')

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for chatbot Susan"""
    try:
        message = request.json.get('message', '') if request.json else ''
        
        # Enhanced chatbot responses
        responses = {
            'hello': 'Hi! I\'m Susan, your Sports Schedulers assistant. How can I help you today?',
            'help': 'I can help you with:\n- Adding and managing games\n- Assigning officials\n- Managing leagues and locations\n- Understanding user roles\n- Navigation tips\n- Viewing reports and earnings',
            'games': 'To add a game, go to Game Management and click "Add Game". Select a league, location, date, and time. You can then assign officials manually or use auto-assignment.',
            'assign': 'Officials can be assigned manually from the game assignment page, or automatically based on their ranking and availability. The system checks for conflicts automatically.',
            'users': 'Administrators can manage users from the Admin Dashboard. You can add, edit, and manage user roles and league memberships.',
            'leagues': 'Leagues organize games by sport and level. Each league can have different fee structures and official rankings.',
            'locations': 'Locations are venues where games are played. Each location can have multiple fields or courts.',
            'default': 'I\'m here to help! Try asking about games, assignments, users, leagues, reports, or navigation.'
        }
        
        response = responses.get('default')
        message_lower = message.lower()
        
        for keyword, reply in responses.items():
            if keyword in message_lower:
                response = reply
                break
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': 'Sorry, I encountered an error. Please try again.'})

# Temporary debug routes
@app.route('/debug-users')
def debug_users():
    """Temporary route to check if users exist"""
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'email': user.email,
                'role': user.role,
                'active': user.is_active
            })
        return f"Users in database: {user_list}"
    except Exception as e:
        return f"Database error: {str(e)}"

@app.route('/create-admin-now')
def create_admin_now():
    """Force create admin user"""
    try:
        from werkzeug.security import generate_password_hash
        
        # Delete existing admin if any
        existing = User.query.filter_by(email='admin@sportsscheduler.com').first()
        if existing:
            db.session.delete(existing)
        
        # Create new admin
        admin = User(
            email='admin@sportsscheduler.com',
            first_name='Admin',
            last_name='User',
            role='superadmin',
            password_hash=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        return "Admin user created! Try logging in now."
    except Exception as e:
        return f"Error: {str(e)}"

# Redirect routes to proper blueprints
@app.route('/admin')
@login_required
def admin_redirect():
    """Redirect to admin dashboard"""
    if not current_user.can_manage_users:
        flash('Access denied. Administrator role required.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('admin.dashboard'))

@app.route('/games')
@login_required  
def games_redirect():
    """Redirect to game management"""
    if current_user.role not in ['assigner', 'administrator', 'superadmin']:
        flash('Access denied. Game management role required.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('game.dashboard'))

@app.route('/leagues')
@login_required
def leagues_redirect():
    """Redirect to league management"""
    if not current_user.can_manage_users:
        flash('Access denied. League management role required.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('league.dashboard'))

@app.route('/reports')
@login_required
def reports_redirect():
    """Redirect to reports dashboard"""
    return redirect(url_for('report.dashboard'))

# Register blueprints
from views.auth_routes import auth_bp
from views.admin_routes import admin_bp

# Bulk operations
try:
    from views.bulk_routes import bulk_bp
    app.register_blueprint(bulk_bp, url_prefix='/bulk')
    print("Bulk operations enabled")
except ImportError:
    pass

# Enhanced chatbot
try:
    from views.chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    print("Enhanced chatbot enabled")
except ImportError:
    pass

# League routes
try:
    from views.league_routes import league_bp
    app.register_blueprint(league_bp, url_prefix='/league')
    print("League routes loaded successfully")
except ImportError:
    pass

# Game routes
try:
    from views.game_routes import game_bp
    app.register_blueprint(game_bp, url_prefix='/game')
    print("Game routes loaded successfully")
except ImportError:
    pass

# Report routes
try:
    from views.report_routes import report_bp
    app.register_blueprint(report_bp, url_prefix='/report')
    print("Report routes loaded successfully")
except ImportError:
    pass

# Register core blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404,
                         error_message='Page not found'), 404

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('error.html',
                         error_code=403, 
                         error_message='Access forbidden'), 403

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html',
                         error_code=500,
                         error_message='Internal server error'), 500

# Initialize email service for notifications
def setup_email_notifications():
    """Setup email notification service"""
    try:
        from utils.email_service import configure_email_service
        print("Email notification service initialized")
    except ImportError:
        pass

def create_demo_rankings():
    """Create demo official rankings for testing"""
    try:
        from models.database import User
        from models.league import League
        from models.availability import OfficialRanking
        
        if OfficialRanking.query.count() > 0:
            return
        
        admin_user = User.query.filter_by(email='admin@sportsscheduler.com').first()
        leagues = League.query.all()
        
        if admin_user and leagues:
            for league in leagues:
                ranking = OfficialRanking(
                    user_id=admin_user.id,
                    league_id=league.id,
                    ranking=5,
                    years_experience=15,
                    games_worked=200
                )
                db.session.add(ranking)
            
            db.session.commit()
            print("Demo rankings created successfully!")
        
    except Exception:
        pass

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        
        # Validation
        errors = []
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not email:
            errors.append('Email is required')
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if existing_user:
            errors.append('Email is already in use by another account')
        
        # Password validation if changing password
        if new_password:
            if len(new_password) < 6:
                errors.append('New password must be at least 6 characters')
            if not current_password:
                errors.append('Current password is required to set a new password')
            elif not current_user.check_password(current_password):
                errors.append('Current password is incorrect')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile_edit.html', user=current_user)
        
        # Update user information
        try:
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.email = email
            current_user.phone = phone if phone else None
            
            # Update password if provided
            if new_password:
                current_user.set_password(new_password)
            
            current_user.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('profile_edit.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create basic tables first
            db.create_all()
            print("Database tables created successfully!")

            # Create admin user if it doesn't exist
            admin = User.query.filter_by(email='admin@sportsscheduler.com').first()
            if not admin:
                from werkzeug.security import generate_password_hash
                admin = User(
                    email='admin@sportsscheduler.com',
                    first_name='Admin',
                    last_name='User',
                    role='superadmin',
                    password_hash=generate_password_hash('admin123'),
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists")

            # Create other demo users
            create_demo_users()
            
            # Try to create rankings if available
            try:
                from models.availability import OfficialAvailability, OfficialRanking
                create_demo_rankings()
            except ImportError:
                print("Availability system not available")
                
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    setup_email_notifications()
    
    print("=" * 60)
    print("SPORTS SCHEDULERS - JES BASEBALL LLC")
    print("=" * 60)
    print("Server: Starting production server...")
    print("Copyright: 2025 JES Baseball LLC")
    print("Contact: admin@sportsschedulers.com")
    print("=" * 60)
    
    # Production-ready server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
