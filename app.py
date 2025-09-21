# app.py - Main Flask Application - Phase 6 Ready (CLEAN VERSION)
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


# ADD THIS SECTION HERE:
import os

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = 'AIzaSyBG6YHNSe5JjnDW7mnPa32v1OFU4liwddE'

# Production-ready configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sports-scheduler-secret-key-change-in-production')

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
        # Import Location model
        from models.league import Location
        
        # Admin dashboard data
        dashboard_data.update({
            'total_users': 4,  # Demo count
            'total_leagues': 3,  # Demo count
            'total_locations': Location.query.count(),  # Real location count
            'total_games': 8,  # Demo count
            'recent_games': []  # Placeholder for recent games
        })
    
    if current_user.role in ['assigner', 'administrator', 'superadmin']:
        # Game management data
        dashboard_data.update({
            'draft_games': 2,
            'ready_games': 1,
            'released_games': 3,
            'unassigned_games': 1
        })
    
    if current_user.role == 'official':
        # Official-specific dashboard data
        dashboard_data.update({
            'upcoming_assignments': 2,
            'total_earnings_ytd': 450.00,
            'games_worked_ytd': 15
        })
    
    return render_template('dashboard.html', 
                         title=f'{current_user.role.title()} Dashboard',
                         user=current_user,
                         **dashboard_data)  # This spreads all the dashboard_data into the template

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
        
        # Enhanced chatbot responses for Phase 6
        responses = {
            'hello': 'Hi! I\'m Susan, your Sports Scheduler assistant. How can I help you today?',
            'help': 'I can help you with:\n- Adding and managing games\n- Assigning officials\n- Managing leagues and locations\n- Understanding user roles\n- Navigation tips\n- Viewing reports and earnings',
            'games': 'To add a game, go to Game Management and click "Add Game". Select a league, location, date, and time. You can then assign officials manually or use auto-assignment.',
            'assign': 'Officials can be assigned manually from the game assignment page, or automatically based on their ranking and availability. The system checks for conflicts automatically.',
            'users': 'Administrators can manage users from the Admin Dashboard. You can add, edit, and manage user roles and league memberships.',
            'admin': 'The Admin Dashboard shows user statistics and allows you to manage the system. Game Management shows game statistics and scheduling tools.',
            'leagues': 'Leagues organize games by sport and level. Each league can have different fee structures and official rankings.',
            'locations': 'Locations are venues where games are played. Each location can have multiple fields or courts.',
            'status': 'Games progress through statuses: Draft → Ready → Released → Completed. Only released games are visible to officials.',
            'ranking': 'Officials are ranked 1-5 within each league, with 5 being the highest. Rankings affect auto-assignment priority.',
            'availability': 'Officials can set their availability to block out times when they cannot work games.',
            'conflicts': 'The system automatically checks for scheduling conflicts, including 2-hour buffers and field double-bookings.',
            'reports': 'Access financial and game reports from the Reports section. Officials can view earnings, admins can see league financials.',
            'earnings': 'Officials can view and export their earnings reports showing games worked and fees earned.',
            'export': 'You can export reports to CSV format for analysis in Excel or other programs.',
            'notifications': 'The system sends email notifications for game assignments and reminders 72 and 24 hours before games.',
            'communication': 'Officials receive email notifications about assignments, changes, and reminders automatically.',
            'phase6': 'Phase 6 brings advanced features like bulk operations, enhanced mobile support, and performance improvements.',
            'import': 'Bulk import features allow you to upload games, users, and assignments via Excel/CSV files.',
            'mobile': 'The mobile interface is optimized for smartphones and tablets with touch-friendly controls.',
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

# Register blueprints (all completed phases)
from views.auth_routes import auth_bp
from views.admin_routes import admin_bp

# Add this import after your existing imports
try:
    from views.bulk_routes import bulk_bp
    app.register_blueprint(bulk_bp, url_prefix='/bulk')
    print("✅ Bulk operations enabled")
except ImportError as e:
    print(f"⚠️ Bulk operations not available: {e}")

# Add this import with your other blueprint imports (SAFE)
try:
    from views.chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot', name='enhanced_chatbot')
    print("✅ Enhanced chatbot enabled")
except ImportError as e:
    print(f"⚠️ Chatbot not available: {e}")
except ValueError as e:
    print(f"⚠️ Chatbot blueprint conflict: {e}")

# Import league routes (Phase 3)
try:
    from views.league_routes import league_bp
    app.register_blueprint(league_bp, url_prefix='/league')
    print("✅ League routes loaded successfully")
except ImportError as e:
    print(f"⚠️  League routes not available: {e}")

# Import game routes (Phase 4 - COMPLETED)
try:
    from views.game_routes import game_bp
    app.register_blueprint(game_bp, url_prefix='/game')
    print("✅ Game routes loaded successfully")
except ImportError as e:
    print(f"⚠️  Game routes not available: {e}")

# Import report routes (Phase 5 - COMPLETED)
try:
    from views.report_routes import report_bp
    app.register_blueprint(report_bp, url_prefix='/report')
    print("✅ Report routes loaded successfully")
except ImportError as e:
    print(f"⚠️  Report routes not available: {e}")

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
        # For development, we'll use the default settings (prints to console)
        # In production, configure with real SMTP settings:
        # configure_email_service('smtp.gmail.com', 587, 'your-email@gmail.com', 'your-password')
        print("📧 Email notification service initialized (development mode)")
    except ImportError as e:
        print(f"⚠️  Email service not available: {e}")

def create_demo_rankings():
    """Create demo official rankings for testing - SAFE VERSION"""
    try:
        # Safe: Conditional imports with fallback behavior
        try:
            from models.database import User
            from models.league import League
            from models.availability import OfficialRanking
        except ImportError as e:
            print(f"⚠️  Availability models not available: {e}")
            return  # Safe: Graceful degradation
        
        # Safe: Check if tables exist before querying
        try:
            if OfficialRanking.query.count() > 0:
                print("Rankings already exist in database")
                return
        except Exception as e:
            print(f"⚠️  OfficialRanking table not ready: {e}")
            return  # Safe: Graceful degradation
        
        # Safe: Get demo users with error handling
        try:
            admin_user = User.query.filter_by(email='admin@sportsscheduler.com').first()
            official_user = User.query.filter_by(email='official@sportsscheduler.com').first()
            assigner_user = User.query.filter_by(email='assigner@sportsscheduler.com').first()
            administrator_user = User.query.filter_by(email='administrator@sportsscheduler.com').first()
        except Exception as e:
            print(f"⚠️  User table not ready: {e}")
            return  # Safe: Graceful degradation
        
        # Safe: Get leagues with error handling
        try:
            leagues = League.query.all()
        except Exception as e:
            print(f"⚠️  League table not ready: {e}")
            return  # Safe: Graceful degradation
        
        if admin_user and leagues:
            for league in leagues:
                rankings_to_add = []
                
                if admin_user:
                    rankings_to_add.append(OfficialRanking(
                        user_id=admin_user.id,
                        league_id=league.id,
                        ranking=5,
                        years_experience=15,
                        games_worked=200
                    ))
                
                if official_user:
                    rankings_to_add.append(OfficialRanking(
                        user_id=official_user.id,
                        league_id=league.id,
                        ranking=4,
                        years_experience=5,
                        games_worked=75
                    ))
                
                if assigner_user:
                    rankings_to_add.append(OfficialRanking(
                        user_id=assigner_user.id,
                        league_id=league.id,
                        ranking=4,
                        years_experience=8,
                        games_worked=120
                    ))
                
                if administrator_user:
                    rankings_to_add.append(OfficialRanking(
                        user_id=administrator_user.id,
                        league_id=league.id,
                        ranking=5,
                        years_experience=12,
                        games_worked=180
                    ))
                
                # Safe: Add with error handling and rollback
                for ranking in rankings_to_add:
                    try:
                        db.session.add(ranking)
                    except Exception as e:
                        print(f"⚠️  Error adding ranking: {e}")
                        db.session.rollback()
                        return  # Safe: Stop on error
        
        try:
            db.session.commit()
            print("✅ Demo rankings created successfully!")
        except Exception as e:
            print(f"❌ Error committing rankings: {e}")
            db.session.rollback()
        
    except Exception as e:
        print(f"❌ Unexpected error in create_demo_rankings: {e}")
        try:
            db.session.rollback()
        except:
            pass  # Safe: Don't fail on rollback error

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

# Add this import with your other blueprint imports (SAFE)
try:
    from views.chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    print("✅ Enhanced chatbot enabled")
except ImportError as e:
    print(f"⚠️ Chatbot not available: {e}")

# SAFE: Update existing chatbot API to use new system
@app.route('/api/chatbot', methods=['POST'])
def chatbot_api_legacy():
    """Legacy chatbot API - safely redirects to new system"""
    try:
        from flask import request, jsonify
        # Forward request to new system
        message = request.json.get('message', '') if request.json else ''
        
        # Simple fallback if new system not available
        if message.lower() in ['hello', 'hi', 'help']:
            return jsonify({
                'response': "Hi! I'm Susan, your assistant. The enhanced chat system is loading..."
            })
        
        return jsonify({
            'response': "I'm here to help! Please use the chat widget for better assistance."
        })
    except Exception:
        return jsonify({
            'response': "Chat system temporarily unavailable. Please try again."
        })

if __name__ == '__main__':
    with app.app_context():
        try:
            # Safe: Create basic tables first (existing functionality)
            db.create_all()
            print("✅ Database tables created successfully!")

            # Import new models to create tables
            try:
                from models.availability import OfficialAvailability, OfficialRanking
                db.create_all()
            except ImportError:
                pass

            try:
                from sqlalchemy import text
                
                with db.engine.connect() as conn:
                    # Check and add game ranking columns
                    try:
                        conn.execute(text('ALTER TABLE games ADD COLUMN game_ranking INTEGER DEFAULT 3'))
                        print("✅ Added game_ranking column")
                    except Exception:
                        pass  # Column already exists
                        
                    try:
                        conn.execute(text('ALTER TABLE games ADD COLUMN ranking_notes TEXT'))
                        print("✅ Added games ranking_notes column")
                    except Exception:
                        pass  # Column already exists
                        
                    # Check and add user ranking columns
                    try:
                        conn.execute(text('ALTER TABLE users ADD COLUMN default_ranking INTEGER DEFAULT 3'))
                        print("✅ Added default_ranking column")
                    except Exception:
                        pass  # Column already exists
                        
                    try:
                        conn.execute(text('ALTER TABLE users ADD COLUMN ranking_notes TEXT'))
                        print("✅ Added users ranking_notes column")
                    except Exception:
                        pass  # Column already exists
                        
                    conn.commit()
                    
            except Exception as e:
                print(f"ℹ️  Ranking columns setup: {e}")
            
            # Safe: Create demo users (existing functionality)
            create_demo_users()
            
            # Safe: Only try advanced features if basic ones work
            try:
                # Test if we can import availability models
                from models.availability import OfficialAvailability, OfficialRanking
                print("✅ Availability models available - creating demo rankings")
                create_demo_rankings()
            except ImportError as e:
                print(f"⚠️  Availability system not available: {e}")
                print("ℹ️  This is normal - availability features will be added later")
            except Exception as e:
                print(f"⚠️  Error with availability system: {e}")
                print("ℹ️  Continuing without availability features")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            print("🔧 Some features may not be available")
    
    setup_email_notifications()
    
    print("=" * 60)
    print("SPORTS SCHEDULERS - JES BASEBALL LLC")
    print("=" * 60)
    print("Server: Starting production server...")
    print("Copyright: 2025 JES Baseball LLC")
    print("Contact: admin@sportsschedulers.com")
    print("=" * 60)
    
    app.run(host='localhost', port=5000, debug=True)
