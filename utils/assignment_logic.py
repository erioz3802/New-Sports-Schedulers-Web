# utils/assignment_logic.py - Auto-Assignment Algorithms
from datetime import datetime, timedelta
from models.database import db, User
from models.league import League
from models.game import Game, GameAssignment
from models.availability import OfficialRanking, OfficialAvailability, get_assignment_conflicts
import random

class AssignmentEngine:
    """Core engine for automatic official assignment"""
    
    def __init__(self, game):
        self.game = game
        self.league = game.league
        self.conflicts = []
        self.assignments_made = []
    
    def auto_assign_officials(self, num_officials=2, preferred_positions=None):
        """
        Automatically assign officials to a game based on ranking and availability
        
        Args:
            num_officials (int): Number of officials to assign
            preferred_positions (list): List of positions needed (optional)
            
        Returns:
            dict: Results of assignment process
        """
        results = {
            'success': False,
            'assignments_made': [],
            'conflicts': [],
            'message': ''
        }
        
        try:
            # Get available officials for this league
            available_officials = self._get_available_officials()
            
            if len(available_officials) < num_officials:
                results['message'] = f'Not enough available officials. Need {num_officials}, found {len(available_officials)}'
                results['conflicts'] = ['Insufficient officials available']
                return results
            
            # Sort officials by ranking and other criteria
            ranked_officials = self._rank_officials_for_assignment(available_officials)
            
            # Assign officials
            assigned_count = 0
            for official_data in ranked_officials:
                if assigned_count >= num_officials:
                    break
                
                official = official_data['user']
                
                # Double-check availability and conflicts
                conflicts = self._check_assignment_conflicts(official)
                if conflicts:
                    results['conflicts'].extend(conflicts)
                    continue
                
                # Create assignment
                position = None
                if preferred_positions and assigned_count < len(preferred_positions):
                    position = preferred_positions[assigned_count]
                
                assignment = self._create_assignment(official, position)
                if assignment:
                    results['assignments_made'].append({
                        'official': official.full_name,
                        'position': position,
                        'ranking': official_data['ranking']
                    })
                    assigned_count += 1
            
            if assigned_count > 0:
                results['success'] = True
                results['message'] = f'Successfully assigned {assigned_count} officials'
            else:
                results['message'] = 'No officials could be assigned due to conflicts'
            
        except Exception as e:
            results['message'] = f'Error during auto-assignment: {str(e)}'
            results['conflicts'].append(str(e))
        
        return results
    
    def _get_available_officials(self):
        """Get list of officials available for assignment in this league"""
        # Get all active officials
        officials = User.query.filter(
            User.role.in_(['official', 'assigner', 'administrator', 'superadmin']),
            User.is_active == True
        ).all()
        
        available_officials = []
        
        for official in officials:
            # Check if already assigned to this game
            if self._is_already_assigned(official):
                continue
            
            # Check basic availability
            game_datetime = datetime.combine(self.game.date, self.game.time)
            if OfficialAvailability.is_user_available(
                official.id, 
                self.game.date, 
                self.game.time
            ):
                # Check for time conflicts with other assignments
                assignment_conflicts = get_assignment_conflicts(
                    official.id, 
                    game_datetime, 
                    self.game.estimated_duration
                )
                
                if not assignment_conflicts:
                    available_officials.append(official)
        
        return available_officials
    
    def _rank_officials_for_assignment(self, officials):
        """Rank officials based on various criteria"""
        ranked_data = []
        
        for official in officials:
            # Get ranking in this league
            ranking = OfficialRanking.get_user_ranking(official.id, self.league.id)
            
            # Get experience data
            ranking_record = OfficialRanking.query.filter_by(
                user_id=official.id,
                league_id=self.league.id,
                is_active=True
            ).first()
            
            games_worked = ranking_record.games_worked if ranking_record else 0
            last_assignment = ranking_record.last_assignment_date if ranking_record else None
            
            # Calculate days since last assignment (for balancing workload)
            days_since_last = 0
            if last_assignment:
                days_since_last = (self.game.date - last_assignment).days
            else:
                days_since_last = 365  # New officials get priority
            
            # Calculate composite score
            score = self._calculate_assignment_score(
                ranking, games_worked, days_since_last
            )
            
            ranked_data.append({
                'user': official,
                'ranking': ranking,
                'games_worked': games_worked,
                'days_since_last': days_since_last,
                'score': score
            })
        
        # Sort by score (higher is better)
        ranked_data.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_data
    
    def _calculate_assignment_score(self, ranking, games_worked, days_since_last):
        """Calculate assignment priority score"""
        # Base score from ranking (1-5 scale)
        score = ranking * 20
        
        # Bonus for experience, but diminishing returns
        experience_bonus = min(games_worked * 2, 40)
        score += experience_bonus
        
        # Bonus for time since last assignment (load balancing)
        time_bonus = min(days_since_last * 0.5, 30)
        score += time_bonus
        
        # Add small random factor to break ties
        score += random.uniform(-2, 2)
        
        return score
    
    def _check_assignment_conflicts(self, official):
        """Check for any conflicts that would prevent assignment"""
        game_datetime = datetime.combine(self.game.date, self.game.time)
        
        # Check assignment conflicts
        conflicts = get_assignment_conflicts(
            official.id,
            game_datetime,
            self.game.estimated_duration
        )
        
        conflict_messages = []
        for conflict in conflicts:
            conflict_messages.append(conflict['message'])
        
        return conflict_messages
    
    def _is_already_assigned(self, official):
        """Check if official is already assigned to this game"""
        existing = GameAssignment.query.filter_by(
            game_id=self.game.id,
            user_id=official.id,
            is_active=True
        ).first()
        
        return existing is not None
    
    def _create_assignment(self, official, position=None):
        """Create the actual assignment record"""
        try:
            assignment = GameAssignment(
                game_id=self.game.id,
                user_id=official.id,
                position=position,
                assignment_type='auto',
                status='assigned'
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            return assignment
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating assignment: {e}")
            return None


class WorkloadBalancer:
    """Utility class for balancing official workloads"""
    
    @staticmethod
    def get_official_workload(user_id, league_id, days_back=30):
        """Get official's recent workload"""
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        
        assignments = GameAssignment.query.filter(
            GameAssignment.user_id == user_id,
            GameAssignment.is_active == True
        ).join(Game).filter(
            Game.league_id == league_id,
            Game.date >= cutoff_date,
            Game.status.in_(['completed', 'released'])
        ).count()
        
        return assignments
    
    @staticmethod
    def get_league_workload_distribution(league_id, days_back=30):
        """Get workload distribution across all officials in a league"""
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        
        # Get all officials with assignments in this league
        officials_workload = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            db.func.count(GameAssignment.id).label('assignment_count')
        ).join(GameAssignment).join(Game).filter(
            Game.league_id == league_id,
            Game.date >= cutoff_date,
            Game.status.in_(['completed', 'released']),
            GameAssignment.is_active == True
        ).group_by(User.id).all()
        
        return [
            {
                'user_id': official.id,
                'name': f"{official.first_name} {official.last_name}",
                'assignments': official.assignment_count
            }
            for official in officials_workload
        ]


def suggest_officials_for_game(game, num_officials=2):
    """
    Main function to suggest officials for a game
    
    Args:
        game: Game object
        num_officials: Number of officials needed
        
    Returns:
        dict: Suggested officials with ranking information
    """
    engine = AssignmentEngine(game)
    
    # Get available officials
    available_officials = engine._get_available_officials()
    
    if not available_officials:
        return {
            'success': False,
            'message': 'No available officials found',
            'suggestions': []
        }
    
    # Rank officials
    ranked_officials = engine._rank_officials_for_assignment(available_officials)
    
    # Return top suggestions
    suggestions = []
    for i, official_data in enumerate(ranked_officials[:num_officials * 2]):  # Show more options
        suggestions.append({
            'user_id': official_data['user'].id,
            'name': official_data['user'].full_name,
            'email': official_data['user'].email,
            'ranking': official_data['ranking'],
            'games_worked': official_data['games_worked'],
            'days_since_last': official_data['days_since_last'],
            'score': round(official_data['score'], 2),
            'recommended': i < num_officials
        })
    
    return {
        'success': True,
        'message': f'Found {len(suggestions)} potential officials',
        'suggestions': suggestions
    }


def auto_assign_game(game_id, num_officials=2, positions=None):
    """
    Main function to auto-assign officials to a game
    
    Args:
        game_id: ID of the game
        num_officials: Number of officials to assign
        positions: List of positions if specific roles needed
        
    Returns:
        dict: Results of the assignment process
    """
    game = Game.query.get(game_id)
    if not game:
        return {
            'success': False,
            'message': 'Game not found',
            'assignments_made': [],
            'conflicts': []
        }
    
    if game.status not in ['draft', 'ready']:
        return {
            'success': False,
            'message': 'Can only auto-assign officials to draft or ready games',
            'assignments_made': [],
            'conflicts': []
        }
    
    engine = AssignmentEngine(game)
    return engine.auto_assign_officials(num_officials, positions)


def validate_assignment(game_id, user_id):
    """
    Validate if a user can be assigned to a game
    
    Args:
        game_id: ID of the game
        user_id: ID of the user
        
    Returns:
        dict: Validation results
    """
    game = Game.query.get(game_id)
    user = User.query.get(user_id)
    
    if not game or not user:
        return {
            'valid': False,
            'reason': 'Game or user not found'
        }
    
    # Check if already assigned
    existing = GameAssignment.query.filter_by(
        game_id=game_id,
        user_id=user_id,
        is_active=True
    ).first()
    
    if existing:
        return {
            'valid': False,
            'reason': 'Official already assigned to this game'
        }
    
    # Check conflicts
    game_datetime = datetime.combine(game.date, game.time)
    conflicts = get_assignment_conflicts(user_id, game_datetime, game.estimated_duration)
    
    if conflicts:
        return {
            'valid': False,
            'reason': 'Assignment conflicts detected',
            'conflicts': [conflict['message'] for conflict in conflicts]
        }
    
    return {
        'valid': True,
        'reason': 'Assignment is valid'
    }

# Update your existing utils/assignment_logic.py file
# Find the functions that are failing and replace them with these safe versions

def auto_assign_game_officials(game_id, num_officials=2):
    """
    Wrapper function for the routes - SAFE VERSION that handles missing tables
    
    Returns: (success, message, assigned_officials_list)
    """
    try:
        from models.game import Game, GameAssignment
        from models.database import db, User
        
        game = Game.query.get(game_id)
        if not game:
            return False, "Game not found", []
        
        # Get available officials - SAFE VERSION without availability checking
        available_officials = get_simple_available_officials_safe(game)
        
        if len(available_officials) < num_officials:
            return False, f"Only {len(available_officials)} officials available, but {num_officials} requested", []
        
        # Simple ranking - SAFE VERSION
        ranked_officials = simple_rank_officials_safe(game, available_officials)
        
        # Assign officials
        assigned_officials = []
        assigned_count = 0
        
        for official_data in ranked_officials:
            if assigned_count >= num_officials:
                break
                
            official = official_data['official']
            
            # Check for basic conflicts using existing game.check_conflicts method
            conflicts = game.check_conflicts(user_id=official.id)
            if conflicts:
                continue
                
            # Create assignment
            assignment = GameAssignment(
                game_id=game_id,
                user_id=official.id,
                assignment_type='auto',
                status='assigned',
                assigned_at=datetime.utcnow(),
                position=f"Official {assigned_count + 1}"
            )
            
            db.session.add(assignment)
            assigned_officials.append(official.full_name)
            assigned_count += 1
        
        if assigned_count > 0:
            db.session.commit()
            return True, f"Successfully assigned {assigned_count} officials", assigned_officials
        else:
            return False, "No officials could be assigned due to conflicts", []
            
    except Exception as e:
        db.session.rollback()
        return False, f"Error during auto-assignment: {str(e)}", []

def get_simple_available_officials_safe(game):
    """Get officials who are available (SAFE version without availability tables)"""
    from models.database import User
    from models.game import GameAssignment
    
    # Get all potential officials
    officials = User.query.filter(
        User.role.in_(['official', 'assigner', 'administrator', 'superadmin']),
        User.is_active == True
    ).all()
    
    available_officials = []
    
    for official in officials:
        # Skip if already assigned to this game
        existing_assignment = GameAssignment.query.filter_by(
            game_id=game.id,
            user_id=official.id,
            is_active=True
        ).first()
        
        if existing_assignment:
            continue
            
        # Check for time conflicts using game's built-in method
        conflicts = game.check_conflicts(user_id=official.id)
        if not conflicts:
            available_officials.append(official)
    
    return available_officials

def simple_rank_officials_safe(game, officials):
    """Simple ranking SAFE VERSION that handles missing ranking tables"""
    ranked_officials = []
    
    for official in officials:
        score = calculate_simple_score_safe(official, game)
        
        ranked_officials.append({
            'official': official,
            'score': score
        })
    
    # Sort by score (highest first)
    ranked_officials.sort(key=lambda x: x['score'], reverse=True)
    
    return ranked_officials

def calculate_simple_score_safe(official, game):
    """Calculate score SAFE VERSION - works without ranking tables"""
    score = 0
    
    # Base score by role
    role_scores = {
        'superadmin': 100,
        'administrator': 90,
        'assigner': 80,
        'official': 70
    }
    score += role_scores.get(official.role, 50)
    
    # Try to check if official has league ranking (SAFE)
    try:
        from models.availability import OfficialRanking
        
        ranking = OfficialRanking.query.filter_by(
            user_id=official.id,
            league_id=game.league_id
        ).first()
        
        if ranking:
            score += ranking.ranking * 15  # 15-75 points for ranking (1-5)
            if hasattr(ranking, 'games_worked'):
                score += min(ranking.games_worked / 5, 20)  # Up to 20 points
    except (ImportError, Exception):
        # SAFE: If ranking table doesn't exist, use default scoring
        pass
    
    # Workload balancing - officials with fewer recent assignments get higher scores
    try:
        from models.game import GameAssignment
        
        recent_assignments = GameAssignment.query.filter(
            GameAssignment.user_id == official.id,
            GameAssignment.is_active == True,
            GameAssignment.assigned_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        score -= recent_assignments * 10  # Reduce score for busy officials
    except Exception:
        # SAFE: If can't check recent assignments, skip this factor
        pass
    
    # Small random factor to break ties
    import random
    score += random.uniform(-2, 2)
    
    return max(score, 0)

def auto_assign_all_released_games():
    """
    SAFE VERSION of bulk auto-assignment
    
    Returns: (success_count, error_count, messages)
    """
    try:
        from models.game import Game, GameAssignment
        
        # Get all released games that need assignments
        released_games = Game.query.filter(Game.status == 'released').all()
        
        success_count = 0
        error_count = 0
        messages = []
        
        for game in released_games:
            # Check current assignments
            current_assignments = GameAssignment.query.filter_by(
                game_id=game.id,
                is_active=True
            ).count()
            
            # Assume 2 officials per game
            needed_officials = 2 - current_assignments
            
            if needed_officials > 0:
                success, message, assigned_officials = auto_assign_game_officials(game.id, needed_officials)
                
                if success:
                    success_count += 1
                    if assigned_officials:
                        messages.append(f"✅ {game.game_title}: {', '.join(assigned_officials)}")
                else:
                    error_count += 1
                    messages.append(f"❌ {game.game_title}: {message}")
        
        return success_count, error_count, messages
        
    except Exception as e:
        return 0, 1, [f"Error during bulk auto-assignment: {str(e)}"]

def get_assignment_preview(game_id):
    """
    SAFE VERSION of preview function
    
    Returns: dict with preview data
    """
    try:
        from models.game import Game
        
        game = Game.query.get(game_id)
        if not game:
            return {'error': 'Game not found'}
        
        available_officials = get_simple_available_officials_safe(game)
        ranked_officials = simple_rank_officials_safe(game, available_officials)
        
        preview = {
            'game_title': game.game_title,
            'available_count': len(available_officials),
            'top_candidates': []
        }
        
        # Show top 5 candidates
        for i, official_data in enumerate(ranked_officials[:5]):
            official = official_data['official']
            
            # Get ranking info if available (SAFE)
            league_ranking = "Not ranked"
            games_worked = 0
            try:
                from models.availability import OfficialRanking
                ranking = OfficialRanking.query.filter_by(
                    user_id=official.id,
                    league_id=game.league_id
                ).first()
                if ranking:
                    league_ranking = f"{ranking.ranking}/5"
                    games_worked = getattr(ranking, 'games_worked', 0)
            except (ImportError, Exception):
                # SAFE: Continue without ranking info
                pass
            
            # Recent assignments (SAFE)
            recent_assignments = 0
            try:
                from models.game import GameAssignment
                recent_assignments = GameAssignment.query.filter(
                    GameAssignment.user_id == official.id,
                    GameAssignment.is_active == True,
                    GameAssignment.assigned_at >= datetime.utcnow() - timedelta(days=30)
                ).count()
            except Exception:
                # SAFE: Continue without recent assignment info
                pass
            
            preview['top_candidates'].append({
                'rank': i + 1,
                'name': official.full_name,
                'score': round(official_data['score'], 1),
                'league_ranking': league_ranking,
                'experience': f"{games_worked} games",
                'recent_assignments': f"{recent_assignments} recent",
                'would_assign': i < 2  # Top 2 would be assigned
            })
        
        return preview
        
    except Exception as e:
        return {'error': str(e)}



