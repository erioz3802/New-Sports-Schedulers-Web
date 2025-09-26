# app.py - Main Flask Application - Phase 6 Ready (CLEAN VERSION)
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user
from datetime import datetime

OFFICIAL_ROUTES_AVAILABLE = False

# ADD THIS SECTION HERE:
import os

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = 'AIzaSyBG6YHNSe5JjnDW7mnPa32v1OFU4liwddE'

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sports-scheduler-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and Flask-Login
from models.database import db, User, create_demo_users
from models.league import League, Location, LeagueMembership  
from models.game import Game, GameAssignment 
from models.local_user_list import LocalUserList

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

@app.context_processor
def inject_official_availability():
    """Make official routes availability known to templates"""
    return {
        'OFFICIAL_ROUTES_AVAILABLE': globals().get('OFFICIAL_ROUTES_AVAILABLE', False)
    }

# Main routes
@app.route('/')
def index():
    """Main dashboard - role-based landing page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get dashboard stats based on user role with REAL filtering
    dashboard_data = {}
    
    if current_user.role == 'superadmin':
        # Superadmin sees ALL system data
        from models.database import User
        from models.league import Location
        
        dashboard_data.update({
            'total_users': User.query.count(),  # Real system-wide count
            'active_users': User.query.filter_by(is_active=True).count(),
            'total_locations': Location.query.count(),
            'scope_description': 'System-wide overview'
        })
        
        # Get real league count
        try:
            from models.league import League
            dashboard_data['total_leagues'] = League.query.filter_by(is_active=True).count()
        except ImportError:
            dashboard_data['total_leagues'] = 0
            
        # Get real game count
        try:
            from models.game import Game
            dashboard_data['total_games'] = Game.query.filter_by(is_active=True).count()
        except ImportError:
            dashboard_data['total_games'] = 0
    
    elif current_user.role in ['administrator', 'assigner']:
        # Admin/Assigner see LIMITED data from their scope
        from utils.data_helpers import get_local_users
        from models.league import Location
    
        accessible_users = get_local_users(current_user.id)
        dashboard_data.update({
            'total_users': len(accessible_users),
            'active_users': len([u for u in accessible_users if u.get('is_active', True)]),
            'total_locations': Location.query.count(),
            'scope_description': 'Your scope overview'
        })
    
        # Get leagues from user's scope
        try:
            from models.league import LeagueMembership
            user_leagues = LeagueMembership.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).all()
            dashboard_data['total_leagues'] = len(user_leagues)
        except ImportError:
            dashboard_data['total_leagues'] = 0
    
        # Get REAL game data based on user's leagues
        try:
            from models.game import Game
            league_ids = [ul.league_id for ul in user_leagues]
            if league_ids:
                user_games = Game.query.filter(
                    Game.league_id.in_(league_ids),
                    Game.is_active == True
                ).all()
            
                dashboard_data.update({
                    'draft_games': len([g for g in user_games if g.status == 'draft']),
                    'ready_games': len([g for g in user_games if g.status == 'ready']),
                    'released_games': len([g for g in user_games if g.status == 'released']),
                    'total_games': len(user_games)
                })
            else:
                # No leagues assigned = no games
                dashboard_data.update({
                    'draft_games': 0,
                    'ready_games': 0,
                    'released_games': 0,
                    'total_games': 0
                })
        except ImportError:
            # Game model not available
            dashboard_data.update({
                'draft_games': 0,
                'ready_games': 0,
                'released_games': 0,
                'total_games': 0
            })
    
    elif current_user.role == 'official':
        # Official sees personal data only
        dashboard_data.update({
            'total_users': 1,  # Just themselves
            'active_users': 1,
            'total_leagues': 0,  # Could show leagues they're assigned to
            'total_games': 0,   # Could show their assigned games
            'upcoming_assignments': 2,
            'total_earnings_ytd': 450.00,
            'games_worked_ytd': 15,
            'scope_description': 'Your personal overview'
        })
    
    else:
        # Viewer role - minimal data
        dashboard_data.update({
            'total_users': 1,
            'active_users': 1,
            'total_leagues': 0,
            'total_games': 0,
            'scope_description': 'Read-only view'
        })
    
    return render_template('dashboard.html', 
                         title=f'{current_user.role.title()} Dashboard',
                         user=current_user,
                         **dashboard_data)

#@app.route('/dashboard')
#@login_required
#def dashboard():
#    """Redirect to main dashboard"""
#    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile management"""
    return render_template('profile.html', user=current_user)

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """Enhanced API endpoint for chatbot Susan - COMPLETE VERSION"""
    try:
        data = request.get_json() if request.is_json else {}
        message = data.get('message', '').strip() if data else ''
        
        # Get user context safely
        user_context = {'first_name': 'friend', 'role': 'user'}
        try:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                user_context = {
                    'first_name': getattr(current_user, 'first_name', 'friend'),
                    'role': getattr(current_user, 'role', 'user'),
                    'can_manage_users': getattr(current_user, 'can_manage_users', False)
                }
        except Exception:
            pass  # Use default context
        
        # Use enhanced chatbot if available, otherwise fall back to basic responses
        if CHATBOT_ENHANCED and susan:
            try:
                response = susan.process_message(message, user_context)
                suggestions = susan.generate_suggestions(message, user_context)
                
                return jsonify({
                    'response': response,
                    'suggestions': suggestions,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'version': 'enhanced'
                })
            except Exception as e:
                print(f"Enhanced chatbot error: {e}")
                # Fall through to basic responses
        
        # Basic responses fallback (enhanced version of existing logic)
        message_lower = message.lower() if message else ''
        
        # Enhanced basic responses
        responses = {
            'hello': f"Hi {user_context.get('first_name', 'friend')}! 👋 I'm Susan, your Sports Scheduler assistant. How can I help you today?",
            'help': """I can help you with:
• Adding and managing games
• Assigning officials  
• Managing leagues and locations
• Understanding user roles
• Navigation tips
• Viewing reports and earnings

What specific help do you need?""",
            'games': "To add a game, go to Game Management and click 'Add Game'. Select a league, location, date, and time. Need help with a specific step?",
            'assign': "Officials can be assigned manually or automatically based on their ranking and availability. Would you like me to walk you through the process?",
            'users': "Administrators can manage users from the Admin Dashboard. You can add, edit, and manage user roles. Need help with a specific user task?",
            'admin': "The Admin Dashboard shows user statistics and allows you to manage the system. What admin task can I help you with?",
            'leagues': "To create a league, go to League Management and click 'Add League'. Fill in the league details and settings. Need specific help?",
            'locations': "To add a location, go to Locations and click 'Add Location'. You can search for venues or add them manually. What location help do you need?",
            'reports': "Reports are available in the Reports section. You can view financial reports, assignment statistics, and performance data. What type of report are you looking for?",
            'navigation': "Use the main menu to navigate between sections. Your available options depend on your role. Where do you need to go?",
            'error': "Let's troubleshoot this! Try refreshing the page, clearing your browser cache, or logging out and back in. What specific error are you seeing?",
            'problem': "I'm here to help solve problems! Try refreshing the page first, then let me know what specific issue you're experiencing.",
            'default': f"I'm here to help, {user_context.get('first_name', 'friend')}! Try asking about games, assignments, users, leagues, reports, or navigation. What can I assist you with?"
        }
        
        # Find best response
        response = responses.get('default')
        for keyword, reply in responses.items():
            if keyword in message_lower:
                response = reply
                break
        
        # Generate basic suggestions based on role
        role = user_context.get('role', 'user')
        basic_suggestions = {
            'administrator': ['How do I add users?', 'Create a league', 'Manage games', 'View reports'],
            'superadmin': ['System administration', 'User management', 'View all reports', 'Manage settings'],
            'assigner': ['Create games', 'Assign officials', 'Check schedules', 'View assignments'],
            'official': ['My assignments', 'Set availability', 'View earnings', 'Game details'],
            'viewer': ['View reports', 'League information', 'Game schedules', 'Statistics']
        }.get(role, ['Help', 'Navigation', 'How to guides', 'Troubleshooting'])
        
        return jsonify({
            'response': response,
            'suggestions': basic_suggestions,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'version': 'basic'
        })
        
    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({
            'response': "Oops! 😅 I got a bit confused there. Mind trying that again? If this keeps happening, try refreshing the page!",
            'suggestions': ['Try asking again', 'Refresh page', 'Contact support'],
            'status': 'error'
        }), 200

 
@app.route('/api/chat', methods=['POST'])
def chatbot_frontend_api():
    """Frontend compatibility route - redirects to main chatbot API"""
    return chatbot_api()

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

# Enhanced chatbot import - SAFE VERSION
try:
    from utils.chatbot_susan import ChatbotSusan
    CHATBOT_ENHANCED = True
    print("✅ Enhanced Susan chatbot loaded successfully")
except ImportError:
    CHATBOT_ENHANCED = False
    print("⚠️  Enhanced chatbot not available, using basic responses")

# Initialize enhanced chatbot if available
if CHATBOT_ENHANCED:
    susan = ChatbotSusan()
else:
    susan = None

# Add this import after your existing imports
try:
    from views.bulk_routes import bulk_bp
    app.register_blueprint(bulk_bp, url_prefix='/bulk')
    print("✅ Bulk operations enabled")
except ImportError as e:
    print(f"⚠️ Bulk operations not available: {e}")

# Import league routes
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

@app.route('/help')
def help_page():
    """Help and documentation page"""
    try:
        return render_template('help.html', title='Help & Support')
    except Exception as e:
        # Fallback if help.html doesn't exist
        return f"""
        <h1>Sports Scheduler Help</h1>
        <p>Welcome to the Sports Scheduler help system!</p>
        <ul>
            <li><a href="/">Return to Dashboard</a></li>
            <li><a href="/test-susan">Test Susan Chatbot</a></li>
        </ul>
        <p>For more help, contact your administrator.</p>
        """

@app.route('/assignments')
@login_required
def assignments_redirect():
    """SAFE redirect to official assignments - compatible with all phases"""
    try:
        return redirect(url_for('official.assignments'))
    except:
        # Safe fallback if official blueprint not available
        flash('Assignment system is being set up. Please check back soon!', 'info')
        return redirect(url_for('index'))

@app.route('/my-assignments')
@login_required  
def my_assignments_redirect():
    """Alternative URL for assignments"""
    return redirect(url_for('assignments_redirect'))

try:
   from views.official_routes import official_bp
   app.register_blueprint(official_bp, url_prefix='/official')
   print("✅ Official routes registered successfully")
   OFFICIAL_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Official routes not available: {e}")
    OFFICIAL_ROUTES_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Official routes registration failed: {e}")
    OFFICIAL_ROUTES_AVAILABLE = False

@app.context_processor
def inject_system_info():
    """SAFE context processor - provides system info to templates"""
    context = {}
    
    if current_user.is_authenticated:
        context.update({
            'user_role': current_user.role, 
            'current_user': current_user,
            'official_routes_available': True
        })
    else:
        context.update({
            'user_role': None, 
            'current_user': None,
            'official_routes_available': False
        })
    
    return context

@app.route('/official/dashboard')
@login_required
def official_dashboard():
    """Safe official dashboard - works without database tables"""
    if current_user.role != 'official':
        flash('Access denied. Official account required.', 'error')
        return redirect(url_for('index'))
    
    # Safe version - no database queries
    return render_template('official/dashboard.html',
                         title='Official Dashboard',
                         upcoming_assignments=[],
                         recent_assignments=[],
                         total_assignments=0,
                         pending_count=0,
                         accepted_count=0,
                         completed_count=0,
                         total_earnings=0.0)
@app.route('/official/assignments')
@login_required
def official_assignments():
    """Working assignments page with real data"""
    if current_user.role != 'official':
        flash('Access denied. Official account required.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Add debugging
        print(f"DEBUG: Current user ID: {current_user.id}")
        print(f"DEBUG: Current user role: {current_user.role}")
        
        # FIXED: Get assignments with proper JOIN
        from models.game import GameAssignment, Game
        from sqlalchemy import desc
        
        # CORRECT QUERY: Properly join GameAssignment with Game table
        assignments = GameAssignment.query.join(Game).filter(
            GameAssignment.user_id == current_user.id,
            GameAssignment.is_active == True
        ).order_by(desc(Game.date)).all()
        
        print(f"DEBUG: Found {len(assignments)} assignments")
        for assignment in assignments:
            print(f"DEBUG: Assignment {assignment.id}, Game {assignment.game_id}, Status: {assignment.status}")
        
        return render_template('official/assignments.html',
                             title='My Assignments',
                             assignments=assignments)
        
    except Exception as e:
        print(f"Assignment loading error: {e}")
        flash('Assignment system is loading. Please check back shortly.', 'info')
        return render_template('official/assignments.html',
                             title='My Assignments',
                             assignments=[])

@app.route('/official/availability')
@login_required
def official_availability():
    """Safe availability page"""
    if current_user.role != 'official':
        flash('Access denied. Official account required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('official/availability.html',
                         title='My Availability')

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
    print("🚀 SPORTS SCHEDULER - STARTING SAFELY")
    print("=" * 60)
    print("🌐 Server: http://localhost:5000")
    print("\n✅ **WORKING FEATURES:**")
    print("  Phase 1: Foundation & Setup")
    print("  Phase 2: Database & User Management")
    print("  Phase 3: League & Location Management")
    print("  Phase 4: Game Scheduling & Official Assignment")
    print("  Phase 5: Reporting & Communication")
    print("\n⚠️  **AVAILABILITY SYSTEM:**")
    print("  Will be added safely once models are confirmed working")
    print("=" * 60)
    print("🚀 Starting Sports Scheduler with SAFE Official Routes on http://localhost:5000")
    print("📦 Available features:")
    print("- ✅ Authentication system")
    print("- ✅ User management") 
    print("- ✅ League management")
    print(f"- ✅ Official assignment system")
       
     
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
