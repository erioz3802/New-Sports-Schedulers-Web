# utils/susan_knowledge_manager.py - Safe Knowledge Manager (Knowledge Base Compliant)
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import re

class SafeSusanKnowledgeManager:
    """Safe knowledge manager that follows proven patterns from knowledge base"""
    
    def __init__(self, knowledge_file='susan_knowledge.json'):
        self.knowledge_file = knowledge_file
        self.knowledge_base = self._load_knowledge_base()
        self.documentation_paths = [
            'docs/',
            'templates/',
            'README.md',
            'CHANGELOG.md',
            'requirements.txt',
            '*.md'  # Any markdown files
        ]
        
    def _load_knowledge_base(self):
        """Load existing knowledge base or create safe default"""
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Knowledge base load error: {e}")
        
        # Safe default knowledge structure
        return {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'application_features': {
                'detected_features': {},
                'file_structure': {}
            },
            'user_guides': {},
            'troubleshooting': self._get_default_troubleshooting(),
            'changelog': [],
            'faq': {},
            'workflow_guides': {},
            'system_requirements': {},
            'api_endpoints': {},
            'database_schema': {},
            'safe_mode': True
        }
    
    def save_knowledge_base(self):
        """Safely save knowledge base to file"""
        try:
            self.knowledge_base['last_updated'] = datetime.now().isoformat()
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=4, default=str, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Knowledge base save error: {e}")
            return False
    
    def update_from_documentation(self):
        """Safely scan documentation files and update knowledge base"""
        print("🧠 Susan is learning from documentation...")
        
        try:
            # Scan for markdown files safely
            self._scan_documentation_files()
            
            # Scan for code documentation safely
            self._scan_code_documentation()
            
            # Detect application features safely
            self._detect_application_features()
            
            # Save updates
            if self.save_knowledge_base():
                print("✅ Susan's knowledge updated successfully!")
            else:
                print("⚠️ Knowledge update completed but save failed")
                
        except Exception as e:
            print(f"❌ Knowledge update error: {e}")
    
    def _scan_documentation_files(self):
        """Safely scan documentation files"""
        for root, dirs, files in os.walk('.'):
            # Skip problematic directories (following knowledge base pattern)
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules', '.env']]
            
            for file in files:
                if file.endswith(('.md', '.txt', '.rst')):
                    file_path = os.path.join(root, file)
                    self._process_documentation_file(file_path)
    
    def _process_documentation_file(self, file_path):
        """Safely process a documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            
            # Process different file types safely
            if filename.lower() == 'readme.md':
                self._extract_readme_info(content)
            elif 'changelog' in filename.lower():
                self._extract_changelog_info(content)
            elif any(word in filename.lower() for word in ['progress', 'tracker', 'status']):
                self._extract_progress_info(content)
            elif 'faq' in filename.lower():
                self._extract_faq_info(content)
            elif filename.endswith('.md'):
                self._extract_general_markdown_info(content, filename)
                
        except Exception as e:
            print(f"Could not process {file_path}: {e}")
            # Continue processing other files
    
    def _extract_readme_info(self, content):
        """Extract information from README.md safely"""
        try:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    project_name = line[2:].strip()
                    # Look for description in next few lines
                    description = ""
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            description = lines[j].strip()
                            break
                    
                    self.knowledge_base['application_features']['project_info'] = {
                        'name': project_name,
                        'description': description,
                        'updated': datetime.now().isoformat()
                    }
                    break
        except Exception as e:
            print(f"README extraction error: {e}")
    
    def _extract_changelog_info(self, content):
        """Extract recent changes from changelog safely"""
        try:
            changelog_entries = []
            lines = content.split('\n')
            
            current_version = None
            current_changes = []
            
            for line in lines:
                # Version headers
                if re.match(r'^##?\s*(v?\d+\.\d+|\[.*\])', line):
                    if current_version and current_changes:
                        changelog_entries.append({
                            'version': current_version,
                            'changes': current_changes[:10],  # Limit changes
                            'extracted': datetime.now().isoformat()
                        })
                    
                    current_version = line.strip()
                    current_changes = []
                
                # Change items
                elif line.strip().startswith(('-', '*', '+')):
                    change = line.strip()[1:].strip()
                    if change and len(current_changes) < 10:  # Limit per version
                        current_changes.append(change)
            
            # Add the last version
            if current_version and current_changes:
                changelog_entries.append({
                    'version': current_version,
                    'changes': current_changes,
                    'extracted': datetime.now().isoformat()
                })
            
            # Keep only recent 5 versions
            self.knowledge_base['changelog'] = changelog_entries[:5]
            
        except Exception as e:
            print(f"Changelog extraction error: {e}")
    
    def _extract_progress_info(self, content):
        """Extract progress and status information safely"""
        try:
            progress_info = {
                'phases': [],
                'current_status': 'Unknown',
                'last_milestone': None,
                'updated': datetime.now().isoformat()
            }
            
            # Extract completed features safely
            completed_patterns = [
                r'- \[x\]\s*(.*)',
                r'✅.*?([A-Z][^✅❌]*)',
                r'COMPLETED.*?([A-Z][^✅❌]*)'
            ]
            
            pending_patterns = [
                r'- \[ \]\s*(.*)',
                r'❌.*?([A-Z][^✅❌]*)',
                r'PENDING.*?([A-Z][^✅❌]*)'
            ]
            
            completed_features = []
            pending_features = []
            
            for pattern in completed_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                completed_features.extend(matches[:5])  # Limit results
                
            for pattern in pending_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                pending_features.extend(matches[:5])  # Limit results
            
            progress_info['completed_features'] = completed_features[:10]
            progress_info['pending_features'] = pending_features[:10]
            
            self.knowledge_base['application_features']['development_progress'] = progress_info
            
        except Exception as e:
            print(f"Progress extraction error: {e}")
    
    def _extract_faq_info(self, content):
        """Extract FAQ information safely"""
        try:
            # Extract Q&A pairs safely
            qa_pattern = r'(?:^|\n)[*#-]?\s*(?:Q:|Question:)\s*(.*?)\n[*#-]?\s*(?:A:|Answer:)\s*(.*?)(?=\n[*#-]?\s*(?:Q:|Question:)|\n\n|\Z)'
            qa_matches = re.findall(qa_pattern, content, re.DOTALL | re.IGNORECASE)
            
            faq_count = 0
            for question, answer in qa_matches:
                if faq_count >= 20:  # Limit FAQ items
                    break
                    
                clean_question = question.strip()
                clean_answer = answer.strip()
                
                if clean_question and clean_answer:
                    self.knowledge_base['faq'][clean_question] = {
                        'answer': clean_answer,
                        'source': 'documentation',
                        'updated': datetime.now().isoformat()
                    }
                    faq_count += 1
                    
        except Exception as e:
            print(f"FAQ extraction error: {e}")
    
    def _extract_general_markdown_info(self, content, filename):
        """Extract information from general markdown files safely"""
        try:
            # Look for step-by-step guides
            if 'step' in content.lower() and ('guide' in filename.lower() or 'how' in filename.lower()):
                steps = re.findall(r'(?:^|\n)\d+\.\s*(.*)', content)
                if steps:
                    guide_name = filename.replace('.md', '').replace('_', ' ').title()
                    self.knowledge_base['workflow_guides'][guide_name] = {
                        'steps': steps[:15],  # Limit steps
                        'source': filename,
                        'updated': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"General markdown extraction error: {e}")
    
    def _scan_code_documentation(self):
        """Safely scan code files for documentation"""
        try:
            api_endpoints = {}
            
            # Scan Python files for Flask routes safely
            for root, dirs, files in os.walk('.'):
                # Skip problematic directories
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        self._extract_flask_routes(file_path, api_endpoints)
                        
                        # Limit endpoints to prevent memory issues
                        if len(api_endpoints) > 50:
                            break
            
            self.knowledge_base['api_endpoints'] = api_endpoints
            
        except Exception as e:
            print(f"Code documentation scan error: {e}")
    
    def _extract_flask_routes(self, file_path, api_endpoints):
        """Safely extract Flask routes from Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find route decorators and their functions safely
            route_pattern = r'@\w+\.route\([\'\"](.*?)[\'\"].*?\)\s*(?:@.*?\s*)*def\s+(\w+)\s*\([^)]*\):\s*(?:\"\"\"(.*?)\"\"\")?'
            routes = re.findall(route_pattern, content, re.DOTALL)
            
            for route_path, function_name, docstring in routes:
                if len(api_endpoints) >= 50:  # Limit endpoints
                    break
                    
                endpoint_info = {
                    'function': function_name,
                    'file': os.path.basename(file_path),
                    'description': docstring.strip() if docstring else f"{function_name} endpoint",
                    'discovered': datetime.now().isoformat()
                }
                api_endpoints[route_path] = endpoint_info
                
        except Exception as e:
            print(f"Route extraction error for {file_path}: {e}")
    
    def _detect_application_features(self):
        """Safely detect available features"""
        try:
            features = {
                'user_management': os.path.exists('models/database.py') or os.path.exists('views/admin_routes.py'),
                'authentication': os.path.exists('views/auth_routes.py'),
                'league_management': os.path.exists('models/league.py'),
                'game_scheduling': os.path.exists('models/game.py'),
                'location_management': os.path.exists('models/league.py'),  # Locations usually in league.py
                'reporting': os.path.exists('views/report_routes.py') or 'report' in str(self.knowledge_base),
                'chatbot': True,  # Susan herself!
                'api_endpoints': len(self.knowledge_base.get('api_endpoints', {})) > 0,
                'database_available': os.path.exists('sports_scheduler.db')
            }
            
            # Safe database table detection
            if features['database_available']:
                features.update(self._safe_detect_database_tables())
            
            self.knowledge_base['application_features']['available_features'] = features
            self.knowledge_base['application_features']['feature_detection_date'] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Feature detection error: {e}")
    
    def _safe_detect_database_tables(self):
        """Safely detect database tables without breaking"""
        table_features = {}
        
        try:
            db_path = 'sports_scheduler.db'
            if not os.path.exists(db_path):
                return table_features
                
            conn = sqlite3.connect(db_path, timeout=5.0)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Map tables to features
                table_features['database_users'] = 'users' in tables
                table_features['database_leagues'] = 'leagues' in tables
                table_features['database_games'] = 'games' in tables
                table_features['database_locations'] = 'locations' in tables
                table_features['database_assignments'] = 'game_assignments' in tables
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Database table detection error: {e}")
            
        return table_features
    
    def _get_default_troubleshooting(self):
        """Get default troubleshooting knowledge"""
        return {
            'login_issues': {
                'symptoms': ['Cannot log in', 'Invalid credentials', 'Password not working'],
                'solutions': [
                    'Verify you\'re using your email address (not username)',
                    'Check if caps lock is enabled',
                    'Try clearing your browser cache',
                    'Contact your administrator for password reset',
                    'Ensure you\'re using the correct URL'
                ]
            },
            'page_not_loading': {
                'symptoms': ['Slow loading', 'Page not responding', 'Timeouts'],
                'solutions': [
                    'Refresh the page (Ctrl+F5 or Cmd+Shift+R)',
                    'Check your internet connection',
                    'Try a different browser',
                    'Clear browser cache and cookies',
                    'Contact system administrator if issues persist'
                ]
            },
            'assignment_problems': {
                'symptoms': ['Cannot assign officials', 'Assignment conflicts', 'Officials not showing up'],
                'solutions': [
                    'Ensure the game status is "Released"',
                    'Check official availability for that date/time',
                    'Verify no 2-hour buffer conflicts exist',
                    'Confirm officials are members of the league',
                    'Check if officials have proper rankings set'
                ]
            }
        }
    
    def add_user_feedback(self, feedback_type, content, user_role=None):
        """Safely add user feedback"""
        try:
            if 'user_feedback' not in self.knowledge_base:
                self.knowledge_base['user_feedback'] = []
            
            feedback_entry = {
                'type': feedback_type,
                'content': content[:500],  # Limit content length
                'user_role': user_role,
                'timestamp': datetime.now().isoformat()
            }
            
            self.knowledge_base['user_feedback'].append(feedback_entry)
            
            # Keep only recent 50 feedback entries (reduced from 100)
            self.knowledge_base['user_feedback'] = self.knowledge_base['user_feedback'][-50:]
            
            self.save_knowledge_base()
            return True
            
        except Exception as e:
            print(f"Feedback storage error: {e}")
            return False
    
    def update_troubleshooting_guide(self, issue, solution, user_role=None):
        """Safely add new troubleshooting information"""
        try:
            issue_key = re.sub(r'[^\w\s]', '', issue.lower()).replace(' ', '_')[:50]  # Limit key length
            
            self.knowledge_base['troubleshooting'][issue_key] = {
                'issue': issue[:200],  # Limit length
                'solution': solution[:500],  # Limit length
                'user_role': user_role,
                'added': datetime.now().isoformat(),
                'usage_count': 1
            }
            
            self.save_knowledge_base()
            return True
            
        except Exception as e:
            print(f"Troubleshooting update error: {e}")
            return False
    
    def get_contextual_knowledge(self, topic, user_role=None):
        """Safely get knowledge relevant to a specific topic"""
        try:
            relevant_knowledge = {}
            topic_lower = topic.lower()
            
            # Search through knowledge areas safely
            for category, content in self.knowledge_base.items():
                if isinstance(content, dict):
                    for key, value in content.items():
                        try:
                            if (topic_lower in key.lower() or 
                                (isinstance(value, dict) and topic_lower in str(value).lower())):
                                if category not in relevant_knowledge:
                                    relevant_knowledge[category] = {}
                                relevant_knowledge[category][key] = value
                        except Exception:
                            continue  # Skip problematic entries
            
            return relevant_knowledge
            
        except Exception as e:
            print(f"Contextual knowledge error: {e}")
            return {}
    
    def get_learning_summary(self):
        """Get a safe summary of what Susan has learned"""
        try:
            summary = {
                'knowledge_areas': len(self.knowledge_base),
                'total_guides': len(self.knowledge_base.get('workflow_guides', {})),
                'api_endpoints': len(self.knowledge_base.get('api_endpoints', {})),
                'faq_items': len(self.knowledge_base.get('faq', {})),
                'troubleshooting_items': len(self.knowledge_base.get('troubleshooting', {})),
                'changelog_versions': len(self.knowledge_base.get('changelog', [])),
                'last_updated': self.knowledge_base.get('last_updated', 'Never'),
                'available_features': list(self.knowledge_base.get('application_features', {}).get('available_features', {}).keys()),
                'safe_mode': self.knowledge_base.get('safe_mode', True)
            }
            
            return summary
            
        except Exception as e:
            print(f"Learning summary error: {e}")
            return {
                'error': str(e),
                'safe_mode': True,
                'knowledge_areas': 0
            }

# Safe initialization functions
def initialize_susan_knowledge():
    """Safely initialize Susan's knowledge from available documentation"""
    try:
        print("🚀 Initializing Susan's knowledge base safely...")
        knowledge_manager = SafeSusanKnowledgeManager()
        knowledge_manager.update_from_documentation()
        return knowledge_manager
    except Exception as e:
        print(f"⚠️ Susan initialization error: {e}")
        # Return minimal working manager
        return SafeSusanKnowledgeManager()

def get_susan_knowledge():
    """Safely get Susan's current knowledge base"""
    try:
        knowledge_manager = SafeSusanKnowledgeManager()
        return knowledge_manager.knowledge_base
    except Exception as e:
        print(f"Knowledge retrieval error: {e}")
        return {"error": str(e), "safe_mode": True}

def update_susan_knowledge():
    """Safely update Susan's knowledge from current documentation"""
    try:
        knowledge_manager = SafeSusanKnowledgeManager()
        knowledge_manager.update_from_documentation()
        return knowledge_manager.get_learning_summary()
    except Exception as e:
        print(f"Knowledge update error: {e}")
        return {"error": str(e), "safe_mode": True}

# Safe usage example
if __name__ == "__main__":
    try:
        # Safe initialization
        manager = initialize_susan_knowledge()
        
        # Show what Susan learned
        summary = manager.get_learning_summary()
        print("\n📚 Susan's Knowledge Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Test contextual knowledge safely
        game_knowledge = manager.get_contextual_knowledge("game", "administrator")
        print(f"\n🎮 Game-related knowledge: {len(game_knowledge)} categories found")
        
    except Exception as e:
        print(f"Safe Susan error: {e}")
        print("Susan is running in safe mode with minimal functionality.")