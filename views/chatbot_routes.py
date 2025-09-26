# views/chatbot_routes.py - FIXED VERSION - Complete Susan Chatbot Implementation
from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
import re
import random
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

class ChatbotSusan:
    """Enhanced conversational chatbot - WORKING VERSION"""
    
    def __init__(self):
        self.name = "Susan"
        self.version = "2.0 - Fixed"
        
        # Fixed greeting patterns
        self.greeting_patterns = [
            r'\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b',
            r'\b(susan)\b'
        ]
        
        # Fixed help patterns  
        self.help_patterns = [
            r'\b(help|assistance|support|guide|how to|tutorial)\b'
        ]
        
        # Complete context keywords
        self.context_keywords = {
            'games': ['game', 'games', 'schedule', 'scheduling', 'match', 'matches'],
            'officials': ['official', 'officials', 'referee', 'referees', 'umpire', 'umpires'],
            'assignments': ['assign', 'assignment', 'assignments', 'assigned'],
            'leagues': ['league', 'leagues', 'competition', 'tournament'],
            'locations': ['location', 'locations', 'venue', 'venues', 'field', 'fields'],
            'users': ['user', 'users', 'people', 'person', 'account', 'accounts'],
            'availability': ['available', 'availability', 'free', 'busy', 'schedule'],
            'reports': ['report', 'reports', 'earnings', 'financial', 'statistics', 'stats'],
            'navigation': ['navigate', 'navigation', 'find', 'where', 'how to get to'],
            'errors': ['error', 'problem', 'issue', 'bug', 'not working', 'broken'],
            'login': ['login', 'log in', 'sign in', 'password', 'authentication'],
            'profile': ['profile', 'account settings', 'personal info', 'edit profile']
        }
    
    def process_message(self, message, user_context=None):
        """FIXED: Process user message and return appropriate response"""
        if not message or not message.strip():
            return self._get_default_greeting(user_context)
            
        message_lower = message.lower().strip()
        user_role = user_context.get('role', 'user') if user_context else 'user'
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        
        # Check for greetings - FIXED
        if self._matches_patterns(message_lower, self.greeting_patterns):
            return self._get_greeting_response(user_context)
        
        # Check for help requests - FIXED
        if self._matches_patterns(message_lower, self.help_patterns):
            return self._get_help_response(user_context)
        
        # Context-based responses - FIXED
        context = self._detect_context(message_lower)
        if context:
            return self._get_context_response(context, user_role)
            
        # Default helpful response
        return self._get_default_response(user_name, user_role)
    
    def _matches_patterns(self, message, patterns):
        """FIXED: Check if message matches any of the provided patterns"""
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _detect_context(self, message):
        """FIXED: Detect the context of the user's message"""
        for context, keywords in self.context_keywords.items():
            if any(keyword in message for keyword in keywords):
                return context
        return None
    
    def _get_greeting_response(self, user_context):
        """FIXED: Generate personalized greeting"""
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        user_role = user_context.get('role', 'user') if user_context else 'user'
        
        greetings = [
            f"Hi {user_name}! 👋 I'm Susan, your Sports Scheduler assistant.",
            f"Hello {user_name}! 😊 Susan here, ready to help you today.",
            f"Hey there {user_name}! I'm Susan, and I'm here to help."
        ]
        
        base_greeting = random.choice(greetings)
        
        role_additions = {
            'superadmin': " As the superadmin, you have access to everything! What would you like to manage?",
            'administrator': " As an admin, you can manage users, leagues, and games. How can I help?",
            'assigner': " Ready to manage games and assign officials? What do you need help with?",
            'official': " Want to check your assignments or set availability? I'm here to help!",
            'viewer': " I can help you find reports and league information. What are you looking for?"
        }
        
        role_text = role_additions.get(user_role, " How can I help you navigate the system today?")
        return base_greeting + role_text
    
    def _get_help_response(self, user_context):
        """FIXED: Generate helpful response based on user role"""
        user_role = user_context.get('role', 'user') if user_context else 'user'
        
        help_responses = {
            'superadmin': """**Superadmin Help** 🎯

I can help you with:
• **User Management** - Add/edit users, manage roles
• **System Administration** - Global settings and monitoring
• **League Management** - Create and manage all leagues
• **Game Management** - Full game scheduling control
• **Reports** - System-wide analytics and reports

What specific area do you need help with?""",
            
            'administrator': """**Administrator Help** 🎯

Here's what I can help you with:
• **User Management** - Add officials and assigners to your leagues
• **League Management** - Create and manage your leagues
• **Game Scheduling** - Create and manage games
• **Reports** - View league and financial reports

What would you like to work on today?""",
            
            'assigner': """**Game Management Help** 🎯

I can guide you through:
• **Creating Games** - Step-by-step game creation
• **Assigning Officials** - Manual and auto-assignment
• **Managing Schedules** - Organizing game schedules
• **Conflict Detection** - Avoiding scheduling conflicts

What assignment task can I help you with?""",
            
            'official': """**Official Help** 🎯

I'm here to help you with:
• **Viewing Assignments** - Check your upcoming games
• **Setting Availability** - Manage your schedule
• **Accepting/Declining** - Respond to assignments
• **Earnings** - View your payment history

What do you need help with today?""",
            
            'viewer': """**Viewer Help** 🎯

I can help you find:
• **Reports** - League and game statistics
• **Schedules** - Game schedules and information
• **League Information** - League details and settings
• **Analytics** - Performance and trend data

What information are you looking for?"""
        }
        
        return help_responses.get(user_role, """**General Help** 🎯

I can help you with:
• Navigation and finding features
• Understanding system workflows
• Troubleshooting common issues
• Step-by-step guidance

What specific help do you need?""")
    
    def _get_context_response(self, context, user_role):
        """FIXED: Generate response based on detected context"""
        context_responses = {
            'games': {
                'administrator': """**Game Management** 🎮

Here's how to work with games:
• **Create Games:** Go to Games → Add New Game
• **Edit Games:** Click on any game to modify details
• **Game Status:** Change from Draft → Ready → Released
• **Clone Games:** Copy similar games for quick creation

Need help with a specific game task?""",
                
                'assigner': """**Game Assignment** 🎯

For managing games and assignments:
• **Assign Officials:** Select game → Assign Officials
• **Auto-Assignment:** Use ranking-based auto-assignment
• **Check Conflicts:** System prevents double-booking
• **Release Games:** Make games visible to officials

What specific assignment help do you need?""",
                
                'official': """**Your Game Schedule** 📅

For your assignments:
• **View Schedule:** Check your dashboard for upcoming games
• **Game Details:** Click on games for location and partner info
• **Accept/Decline:** Respond to new assignments promptly
• **Set Availability:** Prevent conflicts by setting unavailable times

Questions about a specific game?"""
            },
            
            'assignments': """**Assignment Help** 📋

I can help you with:
• **Creating Assignments** - Assign officials to games
• **Managing Responses** - Track accept/decline status
• **Conflict Detection** - Avoid scheduling conflicts
• **Assignment Reports** - View assignment statistics

What assignment task do you need help with?""",
            
            'navigation': """**Navigation Help** 🧭

Having trouble finding something? Here's how to navigate:

📍 **Main Menu Areas:**
• **Dashboard** - Your home base with quick stats
• **Games** - Schedule and manage games  
• **Users** - Manage officials and accounts
• **Reports** - Financial and performance data

🔍 **Tips:**
• Use the search function in each section
• Check your role - menu options depend on permissions
• Look for breadcrumbs to track your location

Where do you need to go?""",
            
            'errors': """**Troubleshooting** 🔧

Let's fix the issue! Try these steps:

🔄 **Quick Fixes:**
• Refresh the page (fixes most issues!)
• Clear your browser cache
• Log out and back in
• Check your internet connection

🆘 **Still Having Problems?**
• Take a screenshot of the error
• Note what you were trying to do
• Contact your administrator
• Try a different browser

What specific error are you seeing?""",
            
            'login': """**Login Help** 🔐

Having trouble signing in?

📧 **Login Steps:**
• Use your email address (not username)
• Enter your password carefully
• Check caps lock is off

🔒 **Forgot Password?**
• Contact your administrator for a reset
• They can create a new temporary password

⚠️ **Still Can't Login?**
• Clear browser cache and cookies
• Try a different browser
• Check internet connection

Need me to walk you through it?""",
            
            'users': """**User Management** 👥

I can help you with user management:
• **Adding Users:** Go to Admin → Add User
• **Editing Profiles:** Select user → Edit Profile
• **Role Management:** Assign appropriate roles
• **Account Settings:** Manage permissions and access

What user management task do you need help with?""",
            
            'leagues': """**League Management** 🏆

For league management tasks:
• **Create League:** Go to Leagues → Add New League
• **League Settings:** Configure fees, levels, and rules
• **Member Management:** Add officials to leagues
• **League Reports:** View league-specific analytics

What league task can I help you with?""",
            
            'locations': """**Location Management** 📍

For managing venues and locations:
• **Add Location:** Go to Locations → Add New Location
• **Edit Venues:** Update location details and fields
• **Google Integration:** Search and add locations easily
• **Field Management:** Manage multiple fields per location

What location task do you need help with?""",
            
            'reports': """**Reports & Analytics** 📊

I can help you access reports:
• **Financial Reports:** Earnings and payment tracking
• **Assignment Reports:** Official assignment statistics
• **League Analytics:** League performance data
• **Export Data:** Download reports for external use

What type of report are you looking for?""",
            
            'availability': """**Availability Management** 📅

For managing official availability:
• **Set Availability:** Mark when you're free/busy
• **Block Dates:** Prevent assignments on specific dates
• **Calendar View:** Visual availability management
• **Recurring Blocks:** Set regular unavailable times

What availability help do you need?"""
        }
        
        # Get role-specific response or generic response
        if context in context_responses:
            if isinstance(context_responses[context], dict):
                return context_responses[context].get(user_role, context_responses[context].get('default', 
                    f"I can help you with {context}! What specific question do you have?"))
            else:
                return context_responses[context]
        
        return f"I'd be happy to help you with {context}! What specific question do you have?"
    
    def _get_default_response(self, user_name, user_role):
        """FIXED: Friendly fallback response"""
        return f"""I'd love to help you, {user_name}! 😊

I can assist with:
• **Navigation** - Finding features and getting around
• **Games & Scheduling** - Creating and managing games  
• **Official Assignments** - Assigning and managing officials
• **Troubleshooting** - Fixing issues and answering questions
• **How-to Guides** - Step-by-step instructions

What specific topic can I help you with? Just ask me anything related to sports scheduling!"""
    
    def _get_default_greeting(self, user_context):
        """FIXED: Default greeting when no message provided"""
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        return f"Hi {user_name}! 👋 I'm Susan, your Sports Scheduler assistant. What can I help you with today?"

# Initialize the chatbot instance
susan = ChatbotSusan()

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """FIXED: Enhanced chatbot API endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'response': "Hi! I'm Susan. What can I help you with today?",
                'suggestions': ['How do I navigate?', 'Help with games', 'Show me features'],
                'status': 'success'
            })
        
        message = data.get('message', '').strip()
        
        # Get user context safely - FIXED
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
        
        # Process message - FIXED
        response = susan.process_message(message, user_context)
        
        # Generate suggestions - FIXED
        suggestions = _generate_smart_suggestions(message.lower() if message else '', user_context)
        
        return jsonify({
            'response': response,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        # Better error handling - FIXED
        print(f"Chatbot error: {str(e)}")
        return jsonify({
            'response': "Oops! 😅 I got a bit confused there. Mind trying that again? If this keeps happening, try refreshing the page!",
            'suggestions': ['Try asking again', 'Refresh page', 'Contact support'],
            'status': 'error'
        }), 200

def _generate_smart_suggestions(message, user_context):
    """FIXED: Generate contextually relevant suggestions"""
    role = user_context.get('role', 'user')
    
    # Role-specific suggestions - FIXED
    role_suggestions = {
        'superadmin': [
            'How do I manage users?',
            'Show me system reports',
            'Help with system administration',
            'Troubleshoot issues'
        ],
        'administrator': [
            'How do I create a league?',
            'Add new users',
            'Manage games',
            'View reports'
        ],
        'assigner': [
            'How do I create games?',
            'Assign officials',
            'Check for conflicts',
            'Manage schedules'
        ],
        'official': [
            'Show my assignments',
            'Set my availability',
            'View my earnings',
            'Contact partners'
        ],
        'viewer': [
            'Show me reports',
            'View schedules',
            'League information',
            'Statistics'
        ]
    }
    
    suggestions = role_suggestions.get(role, ['Help me navigate', 'How to guides', 'Troubleshooting'])
    
    # Context-based suggestions - FIXED
    if message:
        if any(word in message for word in ['game', 'schedule']):
            suggestions.insert(0, 'Help with games')
        elif any(word in message for word in ['assign', 'official']):
            suggestions.insert(0, 'Assignment help')
        elif any(word in message for word in ['error', 'problem', 'issue']):
            suggestions.insert(0, 'Troubleshooting guide')
    
    return suggestions[:4]  # Limit to 4 suggestions

@chatbot_bp.route('/chatbot/help')
def chatbot_help():
    """Chatbot help page"""
    return render_template('chatbot/help.html', title='Susan - Sports Scheduler Assistant')

@chatbot_bp.route('/api/chatbot/status')
def chatbot_status():
    """Return chatbot status"""
    return jsonify({
        'name': susan.name,
        'version': susan.version,
        'status': 'online',
        'capabilities': [
            'Role-based responses',
            'Context-aware help',
            'Problem troubleshooting',
            'Navigation assistance',
            'Personalized greetings'
        ]
    })

# Test route for debugging
@chatbot_bp.route('/test')
def test_chatbot():
    """Test route to verify chatbot is working"""
    try:
        test_response = susan.process_message("hello", {'first_name': 'Test User', 'role': 'administrator'})
        return jsonify({
            'status': 'working',
            'test_response': test_response,
            'chatbot_version': susan.version
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500