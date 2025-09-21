# views/chatbot_routes.py - Enhanced Chatbot "Susan" System (SAFE VERSION)
from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
import re
import json
from datetime import datetime, timedelta

chatbot_bp = Blueprint('chatbot', __name__)

class ChatbotSusan:
    """Enhanced intelligent chatbot with context awareness and real data integration"""
    
    def __init__(self):
        self.name = "Susan"
        self.greeting_patterns = [
            r'\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b',
            r'\b(susan)\b'
        ]
        self.help_patterns = [
            r'\b(help|assistance|support|guide|how to|tutorial)\b'
        ]
        self.context_keywords = {
            'games': ['game', 'games', 'schedule', 'scheduling', 'match', 'matches'],
            'officials': ['official', 'officials', 'referee', 'referees', 'umpire', 'umpires'],
            'assignments': ['assign', 'assignment', 'assignments', 'assigned'],
            'leagues': ['league', 'leagues', 'competition', 'tournament'],
            'locations': ['location', 'locations', 'venue', 'venues', 'field', 'fields'],
            'users': ['user', 'users', 'people', 'person', 'account', 'accounts'],
            'availability': ['available', 'availability', 'free', 'busy', 'schedule'],
            'reports': ['report', 'reports', 'earnings', 'financial', 'statistics', 'stats'],
            'bulk': ['bulk', 'import', 'export', 'upload', 'csv', 'excel'],
            'navigation': ['navigate', 'navigation', 'find', 'where', 'how to get to'],
            'errors': ['error', 'problem', 'issue', 'bug', 'not working', 'broken'],
            'login': ['login', 'log in', 'sign in', 'password', 'authentication'],
            'profile': ['profile', 'account settings', 'personal info', 'edit profile']
        }
    
    def process_message(self, message, user_context=None):
        """Process user message and return appropriate response"""
        message_lower = message.lower().strip()
        
        # Check for greetings
        if self._matches_patterns(message_lower, self.greeting_patterns):
            return self._get_greeting_response(user_context)
        
        # Check for help requests
        if self._matches_patterns(message_lower, self.help_patterns):
            return self._get_help_response(user_context)
        
        # Context-based responses
        context = self._detect_context(message_lower)
        
        if context:
            return self._get_context_response(context, message_lower, user_context)
        
        # Fallback response
        return self._get_fallback_response(user_context)
    
    def _matches_patterns(self, message, patterns):
        """Check if message matches any of the given patterns"""
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _detect_context(self, message):
        """Detect the primary context/topic of the user's message"""
        context_scores = {}
        
        for context, keywords in self.context_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > 0:
                context_scores[context] = score
        
        # Return the context with the highest score
        return max(context_scores, key=context_scores.get) if context_scores else None
    
    def _get_greeting_response(self, user_context):
        """Generate personalized friendly greeting response"""
        user_name = user_context.get('first_name', 'there') if user_context else 'there'
        role = user_context.get('role', 'user') if user_context else 'user'
        
        friendly_greetings = [
            f"Hey {user_name}! 👋 I'm Susan, and I'm excited to help you with your Sports Scheduler today!",
            f"Hi there {user_name}! 😊 Susan here - I'm your friendly assistant ready to make sports scheduling a breeze!",
            f"Hello {user_name}! 🌟 I'm Susan, your personal Sports Scheduler guide. What can we tackle together?"
        ]
        
        import random
        base_greeting = random.choice(friendly_greetings)
        
        # Add role-specific friendly context
        role_tips = {
            'administrator': "As an admin, you have superpowers! 🦸‍♀️ I can help you manage users, bulk operations, reports, and so much more!",
            'superadmin': "Wow, a superadmin! 🌟 You've got the keys to everything! I'm here to help you master the entire system.",
            'assigner': "You're the assignment wizard! ✨ I can help you schedule games, assign officials, and avoid those pesky conflicts.",
            'official': "Great to see you! 🎯 I'm here to help you stay on top of your assignments, availability, and earnings.",
            'viewer': "Welcome! 👀 I can help you find all the reports and information you need to stay informed."
        }
        
        tip = role_tips.get(role, "I'm here to help you navigate and get the most out of Sports Scheduler! 🚀")
        return f"{base_greeting}\n\n{tip}"
    
    def _get_help_response(self, user_context):
        """Generate friendly role-specific help response"""
        role = user_context.get('role', 'user') if user_context else 'user'
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        
        help_responses = {
            'administrator': f"""Hey {user_name}! 🎉 I'm so excited to help you manage everything! Here's what we can do together:

🚀 **Your Admin Superpowers:**
• **User Magic** ✨ - Add, edit, or remove users with ease
• **League Wizardry** 🏆 - Create leagues, set fees, manage everything  
• **Game Mastery** 🎮 - Schedule games and assign officials like a pro
• **Bulk Operations** 📊 - Import hundreds of games/users in seconds (seriously!)
• **Reports & Insights** 📈 - See all the data that matters
• **Navigation Help** 🧭 - I'll guide you anywhere you want to go

💡 **Try asking me things like:**
"Show me how to bulk upload games" or "I need help with user management" 

What sounds interesting to you? 😊""",
            
            'superadmin': f"""Wow {user_name}, a superadmin! 🌟 You're basically the captain of this ship! Let me help you navigate your kingdom:

👑 **Your Royal Powers:**
• **Complete System Control** 🎛️ - Every feature, every setting, everything!
• **User Kingdom Management** 👥 - Rule over all users and their destinies
• **Advanced Analytics** 📊 - See the big picture with powerful reports
• **System Configuration** ⚙️ - Shape how everything works
• **Bulk Operations** 🚀 - Move mountains of data effortlessly
• **Troubleshooting** 🔧 - I'll help you solve any mystery

🎯 **Popular requests from superadmins:**
"Help me manage multiple leagues" or "Show me the system reports"

What would you like to conquer today? 💪""",
            
            'assigner': f"""Hi {user_name}! 🎯 You're the assignment hero! I love helping assigners because you make the magic happen:

⭐ **Your Assignment Superpowers:**
• **Game Creation** 🎮 - Build awesome game schedules
• **Official Assignment** 👨‍⚓ - Match the perfect officials to games
• **Conflict Resolution** 🛡️ - I'll help you avoid scheduling disasters
• **Availability Detective** 🔍 - Check who's free before assigning
• **Game Status Wizard** ⚡ - Manage the whole game lifecycle
• **Reports & Stats** 📈 - See how your assignments are performing

💭 **Things I love helping with:**
"How do I assign officials without conflicts?" or "Show me game management"

What assignment challenge can we tackle? 🚀""",
            
            'official': f"""Hey {user_name}! 😊 Officials like you are the heart of sports - let me help you stay organized and successful:

🏆 **Your Official Toolkit:**
• **Assignment Central** 📋 - See all your games at a glance
• **Availability Manager** 📅 - Control when you're free or busy
• **Earnings Tracker** 💰 - Watch your income grow game by game
• **Game Details** 🎮 - Get all the info you need for each game
• **Profile Power** 👤 - Keep your info current and professional
• **Accept/Decline** ✅ - Respond to assignments easily

🎯 **Officials love asking:**
"When are my next games?" or "How do I update my availability?"

What can I help you with today? 🌟""",
            
            'viewer': f"""Welcome {user_name}! 👋 I'm here to help you find exactly what you're looking for:

📊 **Your Information Hub:**
• **Reports Galore** 📈 - All the stats and data you need
• **League Intel** 🏆 - Everything about leagues and competitions
• **Game Schedules** 📅 - See what's happening when
• **System Insights** 💡 - Understand how everything works
• **Navigation Guide** 🧭 - I'll get you where you need to go

🔍 **Viewers often ask:**
"Where are the league reports?" or "Show me game statistics"

What information can I dig up for you? 😊"""
        }
        
        return help_responses.get(role, self._get_general_help())
    
    def _get_general_help(self):
        """Friendly general help for unknown or unauthenticated users"""
        return """Hi there! 😊 I'm Susan, and even though I don't know your role yet, I'm excited to help! 

🌟 **I can definitely help you with:**
• **Finding Your Way** 🧭 - Navigation and discovering features
• **Understanding Roles** 👥 - What different users can do
• **Getting Started** 🚀 - Basic information about sports scheduling
• **Login Help** 🔑 - Trouble accessing your account

💡 **Try asking me things like:**
"What can administrators do?" or "Help me log in" or "How does this work?"

Don't worry - once you're logged in, I'll be even more helpful! What can I help you with right now? 😊"""
    
    def _get_context_response(self, context, message, user_context):
        """Generate context-specific responses"""
        role = user_context.get('role', 'user') if user_context else 'user'
        
        context_responses = {
            'games': self._get_games_response(message, role),
            'officials': self._get_officials_response(message, role),
            'assignments': self._get_assignments_response(message, role),
            'leagues': self._get_leagues_response(message, role),
            'locations': self._get_locations_response(message, role),
            'users': self._get_users_response(message, role),
            'availability': self._get_availability_response(message, role),
            'reports': self._get_reports_response(message, role),
            'bulk': self._get_bulk_response(message, role),
            'navigation': self._get_navigation_response(message, role),
            'errors': self._get_error_response(message, role),
            'login': self._get_login_response(message, role),
            'profile': self._get_profile_response(message, role)
        }
        
        return context_responses.get(context, self._get_fallback_response(user_context))
    
    def _get_games_response(self, message, role):
        """Friendly games-related responses"""
        if 'add' in message or 'create' in message:
            if role in ['administrator', 'superadmin', 'assigner']:
                return """🎮 **Oh, you want to add a game? I love this!** Let me walk you through it:

✨ **Here's the magic formula:**
1. **Navigate** → Go to **Games** → **Manage Games** 
2. **Create** → Click that shiny **"Add New Game"** button
3. **Fill the Details** → Pick your league, location, date, and time
4. **Add Teams** → Enter those team names and game details
5. **Save as Draft** → Keep it safe, then assign officials later

🚀 **Pro Tip Alert!** 
Want to add LOTS of games at once? Check out **Bulk Operations** - you can upload entire seasons from a CSV file! It's like magic! ✨

Need help with any of these steps? Just ask! 😊"""
            else:
                return """Aww, I wish I could help you create games! 😔 But only administrators and assigners have those special powers. 

🎯 **But hey!** You can definitely check out your assigned games in **My Assignments** - that's where all your game action happens! 

Want me to show you around your assignments? 😊"""
        
        elif 'assign' in message:
            if role in ['administrator', 'superadmin', 'assigner']:
                return """🎯 **Official assignment time!** This is one of my favorite features! Let me show you how to be an assignment wizard:

⭐ **The Assignment Magic:**
1. **Find Your Game** → Go to **Games** → **Manage Games**
2. **Click the Magic Button** → Hit **"Assign Officials"** on your game
3. **Choose Your Method:**
   - 🎯 **Manual Assignment** → You pick exactly who you want
   - 🤖 **Auto-Assignment** → Let the system work its magic based on rankings and availability

🛡️ **Don't worry about conflicts!** I've got your back - the system automatically checks for:
• Time conflicts (with a 2-hour buffer)
• Double-bookings 
• Official availability blocks

Want me to explain any of these steps in more detail? I'm here for you! 😊"""
            else:
                return """I see you're curious about assignments! 😊 

🎯 **Your assignment world** lives in **My Assignments** where you can:
• See all your games
• Accept or decline assignments
• Check game details and partner info

Want me to show you around your assignment area? 🌟"""
        
        elif 'conflict' in message:
            return """🛡️ **Conflict detection - one of my superpowers!** I'm like a scheduling guardian angel:

✅ **I automatically watch out for:**
• ⏰ **Time Conflicts** - No official works two games at once (with 2-hour buffer!)
• 📍 **Location Double-booking** - Same field can't host two games simultaneously
• 🚫 **Availability Blocks** - Respect when officials say they're not free
• 👥 **Official Overload** - Nobody gets overwhelmed with too many assignments

🔧 **When conflicts happen, here's what we do:**
• 🕐 **Adjust the Time** - Shift the game to avoid conflicts
• 📍 **Change Location** - Find another field or venue
• 👤 **Assign Different Officials** - Find someone who's available
• 📅 **Update Availability** - Help officials adjust their schedules

I'm pretty good at preventing drama before it starts! 😄 Any specific conflicts you're dealing with?"""
        
        return """🎮 **Game Management - my specialty!** Here's your complete toolkit:

🚀 **Your Game Powers:**
• **Creating Games** → Games → Manage Games → Add New Game
• **Assigning Officials** → Use manual or auto-assignment magic
• **Status Management** → Draft → Ready → Released → Completed
• **Bulk Import** → Upload entire seasons with Bulk Operations

💡 **What specifically would you like to know about games?** I've got tons of tricks to share! 😊"""
    
    def _get_assignments_response(self, message, role):
        """Friendly assignment-related responses"""
        if role == 'official':
            return """🎯 **Your assignment world!** This is where all your game magic happens:

📋 **Your Assignment Command Center:**
• **📅 My Assignments** → See all your games in one beautiful place
• **🔜 Upcoming Games** → What's coming up with dates, times, and locations
• **✅ Accept/Decline** → Respond to new assignments with ease
• **💰 Earnings Tracker** → Watch your income grow game by game
• **📞 Partner Info** → Get contact details for your fellow officials

🔔 **And here's the cool part** - you'll get friendly email notifications:
• When you're assigned to new games (exciting!)
• 72 hours before game time (get ready!)
• 24 hours before game time (almost showtime!)

Want me to show you around any of these features? I'm like your personal assignment tour guide! 😊"""
        
        elif role in ['administrator', 'superadmin', 'assigner']:
            return """🎯 **Official Assignment - where the magic happens!** Let me show you the assignment superpowers:

⭐ **Your Assignment Toolkit:**
• **🎯 Manual Assignment** → You're the conductor, pick exactly who you want
• **🤖 Auto-Assignment** → Let the smart system work its magic based on:
  - 🏆 Official rankings (1-5 scale)
  - 📅 Availability calendars 
  - 🎮 Game level compatibility
  - 🛡️ Conflict prevention

⚠️ **Your Built-in Safety Net:**
• ⏰ 2-hour buffer between games
• 📍 Location/field availability checks
• 🚫 Official's blocked times protection

📊 **Bonus Features:**
• Assignment history tracking
• Performance statistics
• Assignment load balancing

This system is seriously smart! What part would you like me to explain more? 😄"""
        
        return "🎯 Assignment features are role-specific! What specific assignment question do you have? I'd love to help! 😊"
    
    def _get_bulk_response(self, message, role):
        """Bulk operations responses"""
        if role in ['administrator', 'superadmin']:
            return """**Bulk Operations - Save Hours of Work!**
📤 **Access:** Navigation → **Bulk Operations**

🎮 **Game Import:**
• Upload CSV/Excel with game schedules
• Automatic conflict detection
• Supports multiple leagues and locations
• Download template for proper format

👥 **User Import:**
• Mass import officials and staff
• Automatic role assignment
• Duplicate detection
• Default password setup

📋 **Requirements:**
• CSV or Excel files
• Required columns (download templates)
• Valid league/location IDs

💡 **Pro Tip:** Download templates first to see exact format needed! """
        else:
            return "Bulk operations are available to administrators only. Contact your admin for bulk data imports."
    
    def _get_navigation_response(self, message, role):
        """Navigation help responses"""
        if 'find' in message or 'where' in message:
            navigation_guide = f"""**Navigation Guide for {role.title()}s:**

🏠 **Dashboard:** Main overview and quick stats
"""
            
            if role in ['administrator', 'superadmin']:
                navigation_guide += """👥 **Users:** Manage accounts and roles
🏆 **Leagues:** Create and manage leagues
📍 **Locations:** Venue management
🎮 **Games:** Schedule and assign games  
📤 **Bulk Operations:** Import/export data
📊 **Admin:** Administrative dashboard
📈 **Reports:** Financial and system reports"""
            
            elif role == 'assigner':
                navigation_guide += """🎮 **Games:** Create and manage games
📋 **Assignments:** Assign officials to games
📊 **Reports:** View assignment statistics"""
            
            elif role == 'official':
                navigation_guide += """📅 **My Availability:** Set when you're free/busy
📋 **My Assignments:** View assigned games
💰 **Reports:** Check earnings and history"""
            
            navigation_guide += "\n\n🔍 **Can't find something?** Ask me: 'Where is [feature name]?'"
            return navigation_guide
        
        return "What are you trying to find? I can help you navigate to any feature!"
    
    def _get_fallback_response(self, user_context):
        """Friendly fallback response for unrecognized queries"""
        role = user_context.get('role', 'user') if user_context else 'user'
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        
        friendly_fallbacks = [
            f"""Hey {user_name}! 😊 I want to help, but I didn't quite catch what you're looking for. 

🌟 **Let's try this - ask me about:**
• "How do I add a game?" 🎮
• "Show me my assignments" 📋  
• "Where is bulk operations?" 📊
• "Help with user management" 👥
• "How do reports work?" 📈

💬 **Or just say "help"** and I'll show you everything I can do for {role}s!

What would you like to explore? I'm excited to help! 🚀""",
            
            f"""Hmm, I'm not quite sure what you're looking for, {user_name}! 🤔 But don't worry - I'm here to help!

✨ **Try being a bit more specific, like:**
• Instead of "games" → "how do I add a game?"
• Instead of "help" → "help with assignments"
• Instead of "users" → "how do I manage users?"

🎯 **Popular questions for {role}s:**
• Navigation and finding features 🧭
• Step-by-step how-to guides 📚
• Understanding system workflows ⚡
• Troubleshooting issues 🔧

What can I help you discover today? 😊""",
        ]
        
        import random
        return random.choice(friendly_fallbacks)
    
    # Helper methods for other contexts - now with friendly personality!
    def _get_officials_response(self, message, role):
        return """👨‍⚓ **Officials are the heart of sports!** They're the amazing people who referee games and make everything happen! 

🌟 **Fun fact:** All users in our system are officials by default - how cool is that? 

Administrators can manage official accounts, set rankings (1-5 stars!), and handle assignments. Want to know more about official management? Just ask! 😊"""
    
    def _get_leagues_response(self, message, role):
        return """🏆 **Leagues are where the magic is organized!** Think of them as your sports containers that keep everything neat and tidy!

✨ **League superpowers:**
• Organize games by sport and level
• Set custom fees and billing
• Manage memberships and rankings

📍 **Find them:** **Leagues** section to create or manage your league empire!

Want me to walk you through league management? I love showing off this feature! 🌟"""
    
    def _get_locations_response(self, message, role):
        return """📍 **Locations - where the action happens!** These are your game venues, and they're pretty smart!

🏟️ **Location awesomeness:**
• Multiple fields per venue
• Google Maps integration (so cool!)
• Contact information storage
• Conflict prevention by field

🎯 **Find them:** **Locations** section to add venues and set up that Google Maps magic!

Need help setting up a location? I'm your venue expert! 😊"""
    
    def _get_users_response(self, message, role):
        if role in ['administrator', 'superadmin']:
            return """👥 **User management - your people power!** This is where you build your sports scheduling dream team!

🚀 **Your user superpowers:**
• Add new team members
• Assign roles and permissions  
• Manage account settings
• Track user activity

📍 **Command Center:** **Users** section for all your people management needs!

Want me to show you how to add users or manage roles? I'm great at this stuff! 😄"""
        return "👥 **Users questions?** Your administrator is the best person to help with account changes! They've got all the user management superpowers! 😊"
    
    def _get_availability_response(self, message, role):
        if role in ['official', 'assigner', 'administrator', 'superadmin']:
            return """📅 **Availability - your scheduling shield!** This is how you tell the system when you're free or busy!

⭐ **Availability magic:**
• Block out busy times
• Set recurring unavailability  
• Prevent assignment conflicts
• Take control of your schedule

📍 **Find it:** **My Availability** to set your perfect schedule!

This feature is seriously a lifesaver! Want me to explain how to use it? 🌟"""
        return "📅 **Availability settings** are for officials who work games! It's how they control their schedules! 😊"
    
    def _get_reports_response(self, message, role):
        return """📊 **Reports - your data detective headquarters!** I love reports because they tell such great stories with numbers!

✨ **Report magic includes:**
• Earnings and financial tracking 💰
• Game statistics and trends 📈  
• Assignment history 📋
• Performance insights ⭐

📍 **Treasure location:** **Reports** section for all your data adventures!

What kind of report story would you like to explore? I'm excited to help! 🎯"""
    
    def _get_error_response(self, message, role):
        return """🛠️ **Oops! Having a technical hiccup?** Don't worry - I'm here to help you troubleshoot! 

🔧 **Let's try these magic fixes:**
• ✨ Refresh the page (works surprisingly often!)
• 🌐 Check your internet connection  
• 🔄 Log out and back in (the classic move!)
• 👨‍💻 Contact your administrator if it persists
• 💬 Tell me more details - I might have specific help!

🤔 **What specific error are you seeing?** The more details you give me, the better I can help! I'm like a tech support detective! 😊"""
    
    def _get_login_response(self, message, role):
        return """🔑 **Login troubles? I've got your back!** Let's get you back into your account!

💡 **Try these steps:**
• Double-check your email address and password
• Make sure Caps Lock isn't playing tricks on you
• Clear your browser cache (sometimes it helps!)
• Contact your administrator for password resets

🆕 **Need a new account?** Ask your administrator to create one - they're the account wizards!

Still stuck? Tell me more about what's happening and I'll try to help! 😊"""
    
    def _get_profile_response(self, message, role):
        return """👤 **Profile management - make it yours!** I love helping people keep their info current and professional!

✨ **Profile power moves:**
• **📝 Edit Profile:** Click your name → Profile → Edit Profile
• **🔒 Change Password:** Keep your account secure and updated
• **📞 Update Contact:** Make sure we can reach you for games
• **👁️ View Info:** See your role and account status

🎯 **Pro tip:** Keep your profile info current - it's used for game assignments and important communications!

Need help updating anything specific? I'm your profile personal assistant! 😊"""

# Initialize the chatbot instance
susan = ChatbotSusan()

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Enhanced chatbot API endpoint with context awareness"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'response': "Hey there! 👋 I'm Susan, and I'm so excited to chat with you! What can we explore together today? 😊",
                'suggestions': ['How do I add a game?', 'Show me my assignments', 'Help me navigate', 'What can I do?']
            })
        
        # Get user context for personalized responses (SAFE)
        user_context = None
        try:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                user_context = {
                    'id': getattr(current_user, 'id', None),
                    'first_name': getattr(current_user, 'first_name', 'User'),
                    'role': getattr(current_user, 'role', 'user'),
                    'can_manage_users': getattr(current_user, 'can_manage_users', False)
                }
        except Exception:
            # Fallback if current_user not available
            user_context = {'first_name': 'User', 'role': 'user'}
        
        # Process message with enhanced chatbot
        response = susan.process_message(message, user_context)
        
        # Generate contextual suggestions
        suggestions = _generate_suggestions(message, user_context)
        
        return jsonify({
            'response': response,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        # Safe error response
        return jsonify({
            'response': "I'm sorry, I encountered an error. Please try again or contact support.",
            'suggestions': ['Help', 'Navigation', 'Try again'],
            'error': str(e) if (hasattr(current_user, 'role') and current_user.role == 'superadmin') else None
        }), 500

def _generate_suggestions(message, user_context):
    """Generate contextual quick-reply suggestions"""
    role = user_context.get('role', 'user') if user_context else 'user'
    
    base_suggestions = {
        'administrator': [
            'How do I add users?',
            'Show me bulk operations',
            'Game management help',
            'View reports'
        ],
        'superadmin': [
            'System administration',
            'User management',
            'Bulk operations',
            'Advanced reports'
        ],
        'assigner': [
            'How to assign officials?',
            'Create new games',
            'Check for conflicts',
            'Assignment reports'
        ],
        'official': [
            'Show my assignments',
            'Set availability',
            'Check earnings',
            'Game details'
        ],
        'viewer': [
            'View reports',
            'League information',
            'Game schedules',
            'Statistics'
        ]
    }
    
    return base_suggestions.get(role, ['Help', 'Navigation', 'How to guides'])

@chatbot_bp.route('/help/chat')
def chat_help():
    """Help page for chatbot features - no login required"""
    return render_template('chatbot/help.html')

@chatbot_bp.route('/help/quick-start')
def quick_start():
    """Quick start guide based on user role - no login required"""
    user_role = 'guest'
    try:
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_role = getattr(current_user, 'role', 'user')
    except Exception:
        pass
    
    return render_template('chatbot/quick_start.html', user_role=user_role)