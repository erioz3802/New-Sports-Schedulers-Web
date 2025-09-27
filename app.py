# ============================================================================
# app.py - CORRECTED VERSION - Fixed all known issues from knowledge base
# ============================================================================

import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sports-scheduler-secret-key-change-in-production'

# ✅ FIX #1: Proper database configuration (was missing in previous artifact)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "sports_scheduler.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ FIX #2: Initialize database properly
from models.database import db, User
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

from sqlalchemy import select

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID - SQLAlchemy 2.0 compatible"""
    try:
        from models.database import db
        return db.session.get(User, int(user_id))
    except Exception as e:
        print(f"Warning: Falling back to legacy User.query.get() due to: {e}")
        return User.query.get(int(user_id))

@app.context_processor
def inject_user_role():
    """Make user role available in all templates"""
    if current_user.is_authenticated:
        return {'user_role': current_user.role, 'current_user': current_user}
    return {'user_role': None, 'current_user': None}

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard - role-based landing page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get dashboard stats based on user role
    dashboard_data = {}
    
    if current_user.can_manage_users:
        # Admin dashboard data - safe version with try/catch
        try:
            from models.league import League, Location
            dashboard_data.update({
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'total_leagues': League.query.count(),
                'total_locations': Location.query.count()
            })
        except Exception as e:
            print(f"⚠️  Dashboard stats error: {e}")
            dashboard_data = {'total_users': 0, 'active_users': 0, 'total_leagues': 0, 'total_locations': 0}
    
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

# ============================================================================
# CHATBOT API
# ============================================================================

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """Enhanced API endpoint for chatbot Susan"""
    try:
        data = request.get_json() if request.is_json else {}
        message = data.get('message', '').strip() if data else ''
        
        # Get user context safely
        user_context = {'first_name': 'friend', 'role': 'user'}
        if current_user.is_authenticated:
            user_context = {
                'first_name': getattr(current_user, 'first_name', 'friend'),
                'role': getattr(current_user, 'role', 'user')
            }
        
        # Try to use enhanced Susan if available
        try:
            from utils.chatbot_susan import ChatbotSusan
            susan = ChatbotSusan()
            response = susan.process_message(message, user_context)
            suggestions = susan.generate_suggestions(message, user_context)
            
            return jsonify({
                'response': response,
                'suggestions': suggestions,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'version': 'enhanced'
            })
        except ImportError:
            # Fallback to basic responses
            pass
        
        # Basic chatbot responses (your existing code)
        responses = {
            'hello': f"Hi {user_context.get('first_name', 'friend')}! I'm Susan, your Sports Scheduler assistant. How can I help you today?",
            'help': 'I can help you with:\n- User management\n- League and location setup\n- Game scheduling\n- Reports and navigation',
            'users': 'Go to Admin → Manage Users to add, edit, or manage user accounts and roles.',
            'leagues': 'Access League Management to create leagues, set fees, and manage locations.',
            'locations': 'Use League → Locations to add venues and manage field information.',
            'admin': 'The Admin Dashboard shows system statistics and provides user management tools.',
            'games': 'Game management allows you to schedule games and assign officials.',
            'bulk': 'Use Bulk Operations to import multiple games or users from CSV files.',
            'default': 'I\'m here to help! Try asking about users, leagues, games, or navigation.'
        }
        
        response = responses.get('default')
        message_lower = message.lower()
        
        for keyword, reply in responses.items():
            if keyword in message_lower:
                response = reply
                break
        
        # Generate basic suggestions based on user role
        role_suggestions = {
            'administrator': ['How do I add users?', 'Show me bulk operations', 'Game management help'],
            'superadmin': ['System administration', 'User management', 'Advanced reports'],
            'assigner': ['How to assign officials?', 'Create new games', 'Check for conflicts'],
            'official': ['Show my assignments', 'Set availability', 'Check earnings'],
            'viewer': ['View reports', 'League information', 'Game schedules']
        }
        
        suggestions = role_suggestions.get(user_context.get('role', 'user'), 
                                         ['Help with navigation', 'User guide', 'Ask a question'])
        
        return jsonify({
            'response': response,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'version': 'basic'
        })
        
    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({
            'response': 'Sorry, I encountered an error. Please try again.',
            'suggestions': ['Try again', 'Refresh page'],
            'status': 'error'
        }), 200
@app.route('/test-susan')
def test_susan():
    """Test Susan functionality"""
    try:
        from utils.chatbot_susan import ChatbotSusan
        susan = ChatbotSusan()
        test_response = susan.process_message("hello", {'first_name': 'Test User', 'role': 'administrator'})
        return jsonify({
            'status': 'working',
            'enhanced_mode': True,
            'test_response': test_response,
            'chatbot_version': susan.version
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# REDIRECT ROUTES
# ============================================================================

@app.route('/admin')
@login_required
def admin_redirect():
    """Redirect to admin dashboard"""
    if not current_user.can_manage_users:
        flash('Access denied. Administrator role required.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('admin.dashboard'))

@app.route('/leagues')
@login_required
def leagues_redirect():
    """Redirect to league management"""
    if not current_user.can_manage_users:
        flash('Access denied. League management role required.', 'error')
        return redirect(url_for('index'))
    return redirect(url_for('league.dashboard'))

@app.route('/games')
@login_required
def games_redirect():
    """Redirect to game management"""
    if current_user.role not in ['assigner', 'administrator', 'superadmin']:
        flash('Access denied. Game management role required.', 'error')
        return redirect(url_for('index'))
    try:
        return redirect(url_for('game.dashboard'))
    except:
        return render_template('placeholder.html', title='Game Management - Coming Soon')

@app.route('/reports')
@login_required
def reports_redirect():
    """Redirect to reports"""
    try:
        return redirect(url_for('report.dashboard'))
    except:
        return render_template('placeholder.html', title='Reports - Coming Soon')

# ============================================================================
# ✅ FIX #4: CORRECTED BLUEPRINT REGISTRATION
# ============================================================================

def register_blueprints():
    """Register all blueprints safely with proper error handling"""
    
    # Auth routes (critical - must exist)
    try:
        from views.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Auth routes registered")
    except ImportError as e:
        print(f"❌ CRITICAL: Auth routes failed: {e}")
        raise  # Stop execution - auth is required
    
    # Admin routes (critical - must exist)
    try:
        from views.admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("✅ Admin routes registered")
    except ImportError as e:
        print(f"❌ CRITICAL: Admin routes failed: {e}")
        raise  # Stop execution - admin is required
    
    # League routes (important but not critical)
    try:
        from views.league_routes import league_bp
        app.register_blueprint(league_bp, url_prefix='/league')
        print("✅ League routes registered")
    except ImportError as e:
        print(f"⚠️  League routes not available: {e}")
    
    # Game routes (optional)
    try:
        from views.game_routes import game_bp
        app.register_blueprint(game_bp, url_prefix='/game')
        print("✅ Game routes registered")
    except ImportError as e:
        print(f"⚠️  Game routes not available: {e}")
    
    # Report routes (optional)
    try:
        from views.report_routes import report_bp
        app.register_blueprint(report_bp, url_prefix='/report')
        print("✅ Report routes registered")
    except ImportError as e:
        print(f"⚠️  Report routes not available: {e}")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

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
    db.session.rollback()
    return render_template('error.html',
                         error_code=500,
                         error_message='Internal server error'), 500

# ============================================================================
# ✅ FIX #5: CORRECTED DEMO DATA CREATION
# ============================================================================

def create_demo_users():
    """Create demo users if they don't exist - FIXED VERSION"""
    try:
        # Check if users already exist
        if User.query.count() > 0:
            print("✅ Demo users already exist")
            return
        
        # Create demo users
        demo_users = [
            {
                'first_name': 'Super',
                'last_name': 'Admin',
                'email': 'admin@sportsscheduler.com',
                'password': 'admin123',
                'role': 'superadmin',
                'phone': '555-000-0001'
            },
            {
                'first_name': 'League',
                'last_name': 'Administrator',
                'email': 'administrator@sportsscheduler.com',
                'password': 'admin123',
                'role': 'administrator',
                'phone': '555-000-0002'
            },
            {
                'first_name': 'Game',
                'last_name': 'Assigner',
                'email': 'assigner@sportsscheduler.com',
                'password': 'assigner123',
                'role': 'assigner',
                'phone': '555-000-0003'
            },
            {
                'first_name': 'Sports',
                'last_name': 'Official',
                'email': 'official@sportsscheduler.com',
                'password': 'official123',
                'role': 'official',
                'phone': '555-000-0004'
            },
            {
                'first_name': 'Report',
                'last_name': 'Viewer',
                'email': 'viewer@sportsscheduler.com',
                'password': 'viewer123',
                'role': 'viewer',
                'phone': '555-000-0005'
            }
        ]
        
        for user_data in demo_users:
            user = User(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                phone=user_data['phone'],
                role=user_data['role'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        db.session.commit()
        print("✅ Demo users created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        db.session.rollback()

def create_demo_leagues():
    """Create demo leagues and locations - FIXED VERSION"""
    try:
        from models.league import League, Location
        
        # Check if leagues already exist
        if League.query.count() > 0:
            print("✅ Demo leagues already exist")
            return
        
        # Create demo leagues
        demo_leagues = [
            {
                'name': 'Youth Basketball',
                'level': 'Middle School',
                'game_fee': 45.00,
                'billing_amount': 50.00,
                'billing_recipient': 'City Recreation Department'
            },
            {
                'name': 'High School Soccer',
                'level': 'Varsity',
                'game_fee': 65.00,
                'billing_amount': 70.00,
                'billing_recipient': 'Athletic Association'
            },
            {
                'name': 'Adult Volleyball',
                'level': 'Recreational',
                'game_fee': 35.00,
                'billing_amount': 40.00,
                'billing_recipient': 'Community Center'
            },
            {
                'name': 'Youth Baseball',
                'level': 'Little League',
                'game_fee': 40.00,
                'billing_amount': 45.00,
                'billing_recipient': 'Baseball Association'
            }
        ]
        
        for league_data in demo_leagues:
            league = League(
                name=league_data['name'],
                level=league_data['level'],
                game_fee=league_data['game_fee'],
                billing_amount=league_data['billing_amount'],
                billing_recipient=league_data['billing_recipient']
            )
            db.session.add(league)
        
        # Create demo locations
        demo_locations = [
            {
                'name': 'Central High School',
                'address': '123 Education Drive',
                'city': 'Cypress',
                'state': 'TX',
                'zip_code': '77433',
                'field_count': 2,
                'contact_name': 'Athletic Director',
                'contact_phone': '281-555-0100'
            },
            {
                'name': 'Community Sports Complex',
                'address': '456 Sports Way',
                'city': 'Cypress',
                'state': 'TX',
                'zip_code': '77433',
                'field_count': 4,
                'contact_name': 'Facility Manager',
                'contact_phone': '281-555-0200'
            },
            {
                'name': 'Memorial Park',
                'address': '789 Park Avenue',
                'city': 'Houston',
                'state': 'TX',
                'zip_code': '77024',
                'field_count': 3,
                'contact_name': 'Parks Department',
                'contact_phone': '713-555-0300'
            },
            {
                'name': 'Northwest Recreation Center',
                'address': '321 Recreation Blvd',
                'city': 'Cypress',
                'state': 'TX',
                'zip_code': '77429',
                'field_count': 1,
                'contact_name': 'Recreation Coordinator',
                'contact_phone': '281-555-0400'
            }
        ]
        
        for location_data in demo_locations:
            location = Location(
                name=location_data['name'],
                address=location_data['address'],
                city=location_data['city'],
                state=location_data['state'],
                zip_code=location_data['zip_code'],
                field_count=location_data['field_count'],
                contact_name=location_data['contact_name'],
                contact_phone=location_data['contact_phone']
            )
            db.session.add(location)
        
        db.session.commit()
        print("✅ Demo leagues and locations created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating demo leagues: {e}")
        db.session.rollback()

# ============================================================================
# ✅ FIX #6: CORRECTED APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    # ✅ FIXED: Proper initialization order
    with app.app_context():
        # Create database tables first
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Then create demo data (FIXED: now inside app context)
        create_demo_users()
        create_demo_leagues()
    
    # Register blueprints (FIXED: with proper error handling)
    register_blueprints()
    
    print("\n🚀 Starting Sports Scheduler on http://localhost:5000")
    print("=" * 60)
    print("Demo accounts available:")
    print("- Superadmin: admin@sportsscheduler.com / admin123")
    print("- Administrator: administrator@sportsscheduler.com / admin123") 
    print("- Assigner: assigner@sportsscheduler.com / assigner123")
    print("- Official: official@sportsscheduler.com / official123")
    print("- Viewer: viewer@sportsscheduler.com / viewer123")
    print("=" * 60)
    
    app.run(host='localhost', port=5000, debug=True)
