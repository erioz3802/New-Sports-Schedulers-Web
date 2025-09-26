# utils/chatbot_susan.py - Enhanced with Detailed Step-by-Step Instructions

import re
import random
from datetime import datetime

class ChatbotSusan:
    """Enhanced conversational chatbot with detailed step-by-step instructions"""
    
    def __init__(self):
        self.name = "Susan"
        self.version = "2.1 - Detailed Instructions"
        
        # Enhanced context keywords for more specific detection
        self.context_keywords = {
            'greeting': ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'susan'],
            'thanks': ['thank', 'thanks', 'appreciate', 'grateful', 'thx'],
            'help': ['help', 'assistance', 'support', 'guide', 'how to', 'tutorial'],
            
            # Specific action keywords for detailed instructions
            'add_user': ['add user', 'create user', 'new user', 'add official', 'create official', 'new official'],
            'add_game': ['add game', 'create game', 'new game', 'schedule game'],
            'assign_officials': ['assign official', 'assign officials', 'assign ref', 'assign referee'],
            'add_league': ['add league', 'create league', 'new league'],
            'add_location': ['add location', 'create location', 'new location', 'add venue'],
            'view_reports': ['view reports', 'see reports', 'show reports', 'reports'],
            'set_availability': ['set availability', 'availability', 'set schedule', 'block time'],
            'view_assignments': ['my assignments', 'view assignments', 'see assignments', 'show assignments'],
            
            # General categories
            'users': ['user', 'users', 'people', 'person', 'account', 'accounts'],
            'games': ['game', 'games', 'schedule', 'scheduling', 'match', 'matches'],
            'assignments': ['assign', 'assignment', 'assignments', 'assigned'],
            'leagues': ['league', 'leagues', 'competition', 'tournament'],
            'locations': ['location', 'locations', 'venue', 'venues', 'field', 'fields'],
            'reports': ['report', 'reports', 'earnings', 'financial', 'statistics', 'stats'],
            'navigation': ['navigate', 'navigation', 'find', 'where', 'how to get to', 'menu'],
            'errors': ['error', 'problem', 'issue', 'bug', 'not working', 'broken', 'trouble'],
            'login': ['login', 'log in', 'sign in', 'password', 'authentication']
        }
        
        # Detailed step-by-step instructions
        self.detailed_instructions = {
            'add_user': {
                'superadmin': """**📋 Step-by-Step: Add a New User**

**Step 1:** Click **"Users"** in the main navigation menu
**Step 2:** Click the **"Add User"** button (usually blue, top-right)
**Step 3:** Fill out the user form:
   • **First Name:** Enter their first name
   • **Last Name:** Enter their last name  
   • **Email:** Must be unique (this is their login)
   • **Password:** Create a temporary password
   • **Role:** Choose from dropdown (Official, Assigner, Administrator, etc.)
   • **Phone:** Optional but recommended
**Step 4:** Click **"Save"** or **"Add User"**
**Step 5:** The new user will appear in your user list

💡 **Pro Tip:** The user can change their password after first login.

Need help with any specific step? 🤔""",
                
                'administrator': """**📋 Step-by-Step: Add a New User**

**Step 1:** Go to **Admin** → **"Manage Users"**
**Step 2:** Click **"Add New User"** button
**Step 3:** Complete the registration form:
   • **Email Address:** This becomes their username
   • **First & Last Name:** Full name for identification
   • **Role:** Select appropriate role (Official is most common)
   • **Phone Number:** For communications
   • **Initial Password:** They can change this later
**Step 4:** Select which **leagues** they should have access to
**Step 5:** Click **"Create User"**

✅ **Result:** User receives account and can log in immediately.

Having trouble with any step? Let me know! 📞"""
            },
            
            'add_game': {
                'administrator': """**📋 Step-by-Step: Create a New Game**

**Step 1:** Navigate to **"Games"** in the main menu
**Step 2:** Click **"Add Game"** (green button)
**Step 3:** Select game details:
   • **League:** Choose from dropdown
   • **Date:** Click calendar picker
   • **Time:** Use time selector
   • **Location:** Select venue from list
   • **Field:** Choose specific field if multiple available
**Step 4:** Enter game information:
   • **Home Team:** Team name
   • **Away Team:** Team name  
   • **Game Level:** Select appropriate level
   • **Notes:** Any special instructions (optional)
**Step 5:** Set **Game Status:**
   • **Draft:** For editing later
   • **Ready:** For review
   • **Released:** Officials can see and accept
**Step 6:** Click **"Save Game"**

🎯 **Next Step:** Assign officials to the game!

Need help with officials assignment? 🤝""",
                
                'assigner': """**📋 Step-by-Step: Schedule a Game**

**Step 1:** Click **"Games"** → **"Add New Game"**
**Step 2:** Choose your **League** (you can only see your assigned leagues)
**Step 3:** Set the **Date & Time:**
   • Use the date picker for accurate dates
   • Set start time (system calculates end time)
**Step 4:** Pick **Location & Field:**
   • Select from available venues
   • Choose specific field if location has multiple
   • System checks for conflicts automatically
**Step 5:** Enter **Team Details:**
   • Home team name
   • Visiting team name
   • Competition level
**Step 6:** **Save as Draft** first to review
**Step 7:** When ready, **change status to "Released"**

⚡ **Quick Tip:** You can clone similar games to save time!

Ready to assign officials to this game? 👥"""
            },
            
            'assign_officials': {
                'administrator': """**📋 Step-by-Step: Assign Officials to a Game**

**Step 1:** Go to **Games** → **"Manage Games"**
**Step 2:** Find your game and click **"Assign Officials"**
**Step 3:** Choose assignment method:

**🎯 Manual Assignment:**
   • Click **"Manual Assignment"**
   • Select officials from the dropdown
   • System shows their availability status
   • Add multiple officials as needed
   
**🤖 Auto-Assignment:**
   • Click **"Auto-Assignment"** 
   • System picks best officials based on:
     - Availability (no conflicts)
     - Rankings (1-5 scale)
     - Workload balance
   • Review suggestions before confirming

**Step 4:** **Release the game** so officials can see it
**Step 5:** Officials will get notified and can accept/decline

🔍 **Check Status:** View assignment responses in the game details.

Want help with the ranking system? ⭐"""
            },
            
            'add_league': {
                'administrator': """**📋 Step-by-Step: Create a New League**

**Step 1:** Navigate to **"Leagues"** in main menu
**Step 2:** Click **"Add League"** button
**Step 3:** Enter **Basic Information:**
   • **League Name:** Clear, descriptive name
   • **Sport:** Basketball, Soccer, etc.
   • **Season:** Fall 2024, Spring 2025, etc.
   • **Level:** High School, Youth, Adult, etc.
**Step 4:** Set **Financial Details:**
   • **Game Fee:** How much officials earn per game
   • **Payment Schedule:** When officials get paid
   • **Billing Contact:** Who handles payments
**Step 5:** Configure **Settings:**
   • **Game Duration:** Standard game length
   • **Officials Needed:** How many per game
   • **Assignment Rules:** Auto vs manual
**Step 6:** Click **"Create League"**
**Step 7:** **Add Officials** to the league roster

✨ **Next Steps:** Add locations and start scheduling games!

Need help adding officials to your new league? 👥"""
            },
            
            'view_assignments': {
                'official': """**📋 Step-by-Step: View Your Assignments**

**Step 1:** Login to your account
**Step 2:** Your **Dashboard** shows upcoming assignments immediately
**Step 3:** For detailed view, click **"My Assignments"** or **"Assignments"**
**Step 4:** You'll see:
   • **Upcoming Games:** Next 7 days highlighted
   • **Game Details:** Date, time, location, teams
   • **Partner Officials:** Who you're working with
   • **Game Status:** Confirmed, pending, etc.
   • **Payment Info:** Your earnings per game

**📱 Game Details Include:**
   • Full address with map link
   • Partner contact information
   • Special game notes
   • Weather alerts (if applicable)

**Step 5:** Click any game for **full details** and **directions**

📅 **Pro Tip:** Use the calendar view to see your whole schedule at once!

Need help with accepting/declining assignments? ✅❌"""
            },
            
            'view_reports': {
                'administrator': """**📋 Step-by-Step: Access Reports**

**Step 1:** Click **"Reports"** in the main navigation
**Step 2:** Choose your report type:

**💰 Financial Reports:**
   • **Official Payments:** Who earned what
   • **League Expenses:** Total costs per league
   • **Payment Status:** Pending vs. paid

**📊 Assignment Reports:**
   • **Official Workload:** Games per official
   • **Assignment Response Rates:** Accept/decline stats
   • **Conflict Reports:** Scheduling issues

**📈 Performance Analytics:**
   • **League Statistics:** Games scheduled vs. completed
   • **Official Rankings:** Performance metrics
   • **Utilization Reports:** How efficiently officials are used

**Step 3:** **Filter** by date range, league, or official
**Step 4:** **Export** to Excel/CSV for external analysis
**Step 5:** **Print** or **Email** reports as needed

🎯 **Quick Access:** Bookmark frequently used reports!

Which specific report do you need help with? 📋"""
            }
        }
    
    def process_message(self, message, user_context=None):
        """Process user message and return detailed, actionable response"""
        if not message or not message.strip():
            return self._get_greeting_response(user_context)
            
        message_lower = message.lower().strip()
        
        # Get user role for personalization
        user_role = user_context.get('role', 'user') if user_context else 'user'
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        
        # Check for specific action requests first (highest priority)
        for action, keywords in self.context_keywords.items():
            if action.startswith('add_') or action.startswith('view_') or action.startswith('set_'):
                if any(keyword in message_lower for keyword in keywords):
                    return self._get_detailed_instruction(action, user_role, user_name)
        
        # Then check for general categories
        primary_context = self._detect_primary_context(message_lower)
        
        # Generate appropriate response
        if primary_context == 'greeting':
            return self._get_greeting_response(user_context)
        elif primary_context == 'thanks':
            return self._get_thanks_response()
        elif primary_context == 'help':
            return self._get_help_response(user_role)
        elif primary_context in ['users', 'games', 'assignments', 'leagues', 'locations', 'reports']:
            return self._get_category_help(primary_context, user_role, user_name)
        else:
            return self._get_default_response(user_name, user_role)
    
    def _detect_primary_context(self, message):
        """Detect the primary context/intent of the message"""
        # Check each context category
        for context, keywords in self.context_keywords.items():
            if any(keyword in message for keyword in keywords):
                return context
        return None
    
    def _get_detailed_instruction(self, action, user_role, user_name):
        """Get detailed step-by-step instructions for specific actions"""
        if action in self.detailed_instructions:
            instructions = self.detailed_instructions[action]
            if isinstance(instructions, dict):
                # Role-specific instructions
                return instructions.get(user_role, instructions.get('default', 
                    f"I can help you with {action.replace('_', ' ')}, but I need to provide role-specific instructions. What's your role in the system?"))
            else:
                return instructions
        
        # Fallback for actions not yet detailed
        action_name = action.replace('_', ' ').title()
        return f"""**{action_name} Instructions** 📋

I'd love to give you step-by-step instructions for {action_name}, {user_name}! 

To provide the most accurate steps, could you tell me:
• What specific part are you stuck on?
• Have you started the process already?
• Are you seeing any error messages?

This helps me give you exactly the right guidance! 🎯"""
    
    def _get_category_help(self, category, user_role, user_name):
        """Get help for general categories with specific action prompts"""
        category_help = {
            'users': f"""**User Management Help** 👥

Hi {user_name}! I can give you detailed instructions for:

🔧 **Specific Actions:**
• **"add user"** → Step-by-step user creation
• **"edit user profile"** → Modify user details  
• **"change user role"** → Update permissions
• **"reset password"** → Help users with login issues

💡 **Just say:** "add user" or "how to add user" for detailed steps!

What specific user task do you need help with? 🤔""",
            
            'games': f"""**Game Management Help** 🎮

Ready to help you with games, {user_name}!

🎯 **Specific Instructions Available:**
• **"add game"** → Complete game creation walkthrough
• **"assign officials"** → Step-by-step official assignment
• **"clone game"** → Copy existing games quickly
• **"change game status"** → Update Draft→Ready→Released

📋 **Just ask:** "how to add game" for detailed steps!

What game management task can I walk you through? ⚽"""
        }
        
        return category_help.get(category, f"I can help you with {category}, {user_name}! What specific task do you need step-by-step instructions for?")
    
    def _get_greeting_response(self, user_context):
        """Get personalized greeting based on user role"""
        user_role = user_context.get('role', 'default') if user_context else 'default'
        user_name = user_context.get('first_name', 'friend') if user_context else 'friend'
        
        role_greetings = {
            'superadmin': f"Hi {user_name}! 👋 I'm Susan, your Sports Scheduler assistant. As the superadmin, you have access to everything! I can give you detailed step-by-step instructions for any task. What would you like to do?",
            'administrator': f"Hello {user_name}! 😊 I'm Susan. As an admin, I can walk you through user management, league creation, game scheduling, and more. What task needs step-by-step instructions?",
            'assigner': f"Hey {user_name}! I'm Susan. Ready to help you with detailed game management and official assignment instructions. What do you need help with?",
            'official': f"Hi {user_name}! 👋 I'm Susan. I can guide you through viewing assignments, setting availability, and more. What do you need step-by-step help with?",
            'viewer': f"Hello {user_name}! I'm Susan. I can help you find and understand reports and league information. What do you need detailed help with?",
            'default': f"Hi {user_name}! 👋 I'm Susan, your Sports Scheduler assistant. I can provide detailed, step-by-step instructions for any task. What do you need help with?"
        }
        
        return role_greetings.get(user_role, role_greetings['default'])
    
    def _get_thanks_response(self):
        """Return a friendly thanks response"""
        responses = [
            "You're so welcome! Happy to help with detailed instructions anytime! 😊",
            "No problem at all! I love walking people through things step-by-step!",
            "Glad I could help! Feel free to ask for detailed help with anything else.",
            "You're very welcome! I'm here whenever you need step-by-step guidance! 🌟"
        ]
        return random.choice(responses)
    
    def _get_help_response(self, user_role):
        """Get role-specific help response"""
        help_responses = {
            'superadmin': """**Superadmin Detailed Help** 🎯

I can provide step-by-step instructions for:

👥 **User Management:**
• "add user" → Complete user creation walkthrough
• "manage roles" → Role assignment instructions
• "bulk user import" → Import multiple users

🏆 **League Management:**  
• "add league" → Detailed league creation
• "league settings" → Configuration instructions

🎮 **Game Management:**
• "add game" → Game creation walkthrough  
• "assign officials" → Assignment instructions

📊 **Reports & Analytics:**
• "view reports" → Report access instructions
• "export data" → Data export steps

**Just ask for what you need!** For example: "add user" or "how to create a league"

What specific task needs detailed instructions? 🤔""",
            
            'administrator': """**Administrator Step-by-Step Help** 🎯

I specialize in detailed instructions for:

👥 **User Management:**
• "add user" → Complete user creation process
• "edit user" → Profile modification steps
• "user permissions" → Role management

🏆 **League Operations:**
• "add league" → League creation walkthrough
• "manage leagues" → League administration

🎮 **Game Scheduling:**
• "add game" → Game creation instructions
• "assign officials" → Assignment process

📊 **Reporting:**
• "view reports" → Report access and interpretation

**💡 Pro Tip:** Be specific! Say "add user" instead of just "users" for step-by-step instructions.

What task do you need detailed help with? 📋"""
        }
        
        return help_responses.get(user_role, """**General Help** 🎯

I can provide detailed, step-by-step instructions for most tasks!

**💡 For best results, be specific:**
• Say "add user" instead of "users"  
• Say "create game" instead of "games"
• Say "view reports" instead of "reports"

**Popular requests:**
• "add user" → User creation walkthrough
• "add game" → Game scheduling instructions  
• "assign officials" → Assignment process
• "view assignments" → How to check your schedule

What specific task needs step-by-step instructions? 🤔""")
    
    def _get_default_response(self, user_name, user_role):
        """Friendly fallback response"""
        return f"""I'd love to help you with detailed instructions, {user_name}! 😊

**💡 For step-by-step help, try being specific:**
• **"add user"** → Complete user creation walkthrough
• **"add game"** → Game scheduling instructions
• **"assign officials"** → Official assignment process  
• **"view reports"** → Report access guide
• **"view assignments"** → Check your schedule

**Or tell me what you're trying to do:**
• "I need to schedule a game"
• "I want to add a new official"
• "How do I check my assignments"

What specific task can I walk you through step-by-step? 📋"""
    
    def generate_suggestions(self, message, user_context):
        """Generate smart suggestions based on context"""
        user_role = user_context.get('role', 'user') if user_context else 'user'
        
        # Role-specific suggestions with actionable phrases
        role_suggestions = {
            'superadmin': [
                'add user',
                'add league', 
                'view reports',
                'assign officials'
            ],
            'administrator': [
                'add user',
                'add game',
                'add league',
                'view reports'
            ],
            'assigner': [
                'add game',
                'assign officials',
                'view assignments',
                'check schedules'
            ],
            'official': [
                'view assignments',
                'set availability',
                'view earnings',
                'contact partners'
            ],
            'viewer': [
                'view reports',
                'check schedules',
                'league information',
                'game statistics'
            ]
        }
        
        suggestions = role_suggestions.get(user_role, ['add user', 'add game', 'view reports', 'help'])
        
        # Context-based suggestions
        if message:
            message_lower = message.lower()
            if 'user' in message_lower:
                suggestions = ['add user', 'edit user', 'user permissions', 'reset password']
            elif 'game' in message_lower:
                suggestions = ['add game', 'assign officials', 'clone game', 'change game status']
            elif 'report' in message_lower:
                suggestions = ['view reports', 'financial reports', 'export data', 'assignment stats']
        
        return suggestions[:4]  # Limit to 4 suggestions

# For backward compatibility with existing simple responses
ENHANCED_RESPONSES = {
    'hello': "Hi! 👋 I'm Susan, your Sports Scheduler assistant. I can provide detailed step-by-step instructions for any task. What do you need help with?",
    'help': """I can provide detailed step-by-step instructions for:
• **"add user"** → Complete user creation walkthrough
• **"add game"** → Game scheduling instructions
• **"assign officials"** → Official assignment process
• **"view reports"** → Report access guide

What specific task needs detailed instructions?""",
    'default': "I'm here to provide detailed step-by-step instructions! What specific task can I walk you through?"
}