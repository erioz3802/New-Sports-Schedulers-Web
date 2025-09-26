# utils/data_helpers.py - Data Access Helper Functions
from sqlalchemy import and_, or_
from models.database import User, db
from models.league import League, Location
from models.game import Game, GameAssignment

def get_admin_leagues(admin_id):
    """Get leagues accessible to admin - UPDATED for Phase 3 league assignments"""
    from models.database import User
    from models.league import League, LeagueMembership
    
    admin = User.query.get(admin_id)
    
    if not admin:
        return []
    
    if admin.role == 'superadmin':
        # Superadmin can access ALL leagues
        leagues = League.query.filter_by(is_active=True).all()
    else:
        # Regular admin can only access:
        # 1. Leagues they created
        # 2. Leagues assigned to them by superadmin
        
        # Get leagues created by this admin
        created_leagues = League.query.filter_by(
            created_by=admin_id, 
            is_active=True
        ).all() if hasattr(League, 'created_by') else []
        
        # Get leagues assigned to this admin
        assigned_memberships = LeagueMembership.query.filter_by(
            user_id=admin_id, 
            is_active=True
        ).filter(LeagueMembership.assigned_by.isnot(None)).all()
        
        assigned_leagues = []
        for membership in assigned_memberships:
            if membership.league and membership.league.is_active:
                assigned_leagues.append(membership.league)
        
        # Combine and deduplicate using set comprehension
        league_ids = set()
        combined_leagues = []
        
        # Add created leagues
        for league in created_leagues:
            if league.id not in league_ids:
                league_ids.add(league.id)
                combined_leagues.append(league)
        
        # Add assigned leagues
        for league in assigned_leagues:
            if league.id not in league_ids:
                league_ids.add(league.id)
                combined_leagues.append(league)
        
        leagues = combined_leagues
    
    # Convert to the expected format
    league_list = []
    for league in leagues:
        league_data = {
            'id': league.id,
            'name': league.name,
            'level': league.level,
            'fee_per_official': float(league.game_fee) if league.game_fee else 0.0,
            'created_by_me': hasattr(league, 'created_by') and league.created_by == admin_id,
            'is_active': league.is_active,
            'location_count': len(league.locations) if hasattr(league, 'locations') else 0,
            'game_count': league.games_count if hasattr(league, 'games_count') else 0
        }
        
        # Add assignment info if this is an assigned league
        if admin.role != 'superadmin' and not league_data.get('created_by_me', False):
            membership = LeagueMembership.query.filter_by(
                user_id=admin_id, 
                league_id=league.id, 
                is_active=True
            ).filter(LeagueMembership.assigned_by.isnot(None)).first()
            
            if membership:
                league_data['permission_level'] = membership.permission_level or 'admin'
                league_data['assigned_by'] = membership.assigned_by
                league_data['assigned_at'] = membership.assigned_at
        
        league_list.append(league_data)
    
    return league_list


def get_admin_permission_for_league(admin_id, league_id):
    """Get admin's permission level for a specific league"""
    from models.database import User
    from models.league import League, LeagueMembership
    
    admin = User.query.get(admin_id)
    league = League.query.get(league_id)
    
    if not admin or not league:
        return None
    
    # Superadmin has full permissions
    if admin.role == 'superadmin':
        return 'superadmin'
    
    # Check if admin created the league (if League has created_by field)
    if hasattr(league, 'created_by') and league.created_by == admin_id:
        return 'owner'
    
    # Check if admin was assigned to the league
    membership = LeagueMembership.query.filter_by(
        user_id=admin_id,
        league_id=league_id,
        is_active=True
    ).filter(LeagueMembership.assigned_by.isnot(None)).first()
    
    if membership:
        return membership.permission_level or 'admin'
    
    return None


def admin_has_league_access(admin_id, league_id, required_permission='viewer'):
    """Check if admin has access to league with required permission level"""
    permission = get_admin_permission_for_league(admin_id, league_id)
    
    if not permission:
        return False
    
    # Permission hierarchy
    permission_levels = {
        'viewer': 1,
        'assigner': 2, 
        'admin': 3,
        'owner': 4,
        'superadmin': 5
    }
    
    user_level = permission_levels.get(permission, 0)
    required_level = permission_levels.get(required_permission, 0)
    
    return user_level >= required_level


def get_local_users_for_league(admin_id, league_id=None):
    """Get users in admin's local list, optionally filtered by league access"""
    from models.database import User
    
    # Check if local_user_list module exists (Phase 2 should have created it)
    try:
        from models.local_user_list import LocalUserList
        local_user_list_exists = True
    except ImportError:
        local_user_list_exists = False
    
    admin = User.query.get(admin_id)
    if not admin:
        return []
    
    if admin.role == 'superadmin':
        # Superadmin sees all active users
        users = User.query.filter_by(is_active=True).all()
    elif local_user_list_exists:
        # Get users in admin's local list
        local_users = LocalUserList.query.filter_by(
            admin_id=admin_id,
            is_active=True
        ).all()
        
        user_ids = [lu.user_id for lu in local_users]
        users = User.query.filter(
            User.id.in_(user_ids),
            User.is_active == True
        ).all()
    else:
        # Fallback: if Phase 2 not completed, show all users for now
        users = User.query.filter_by(is_active=True).all()
    
    # If league_id specified, filter users who have access to that league
    if league_id:
        filtered_users = []
        for user in users:
            if admin_has_league_access(user.id, league_id, 'viewer'):
                filtered_users.append(user)
        users = filtered_users
    
    # Convert to expected format
    user_list = []
    for user in users:
        user_data = {
            'id': user.id,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role,
            'phone': getattr(user, 'phone', ''),
            'is_active': user.is_active,
            'last_login': user.last_login,
            'created_at': user.created_at
        }
        user_list.append(user_data)
    
    return user_list

def get_all_locations():
    """Get all available locations"""
    locations = Location.query.all()
    
    return [
        {
            'id': location.id,
            'name': location.name,
            'address': location.address,
            'city': location.city,
            'state': location.state
        }
        for location in locations
    ]

def get_available_officials(admin_id):
    """Get officials available to admin for assignments"""
    admin = User.query.get(admin_id)
    
    if not admin:
        return []
    
    if admin.role == 'superadmin':
        # Superadmin can assign any official
        officials = User.query.filter(
            User.role.in_(['official', 'assigner', 'administrator'])
        ).all()
    else:
        # Regular admin can assign officials in their leagues
        # For now, get all officials except other admins
        officials = User.query.filter(
            and_(
                User.role.in_(['official', 'assigner']),
                User.id != admin_id
            )
        ).all()
    
    return [
        {
            'id': official.id,
            'first_name': official.first_name,
            'last_name': official.last_name,
            'email': official.email,
            'phone': official.phone,
            'role': official.role
        }
        for official in officials
    ]

def get_admin_games(admin_id, league_id=None, date_from=None, date_to=None):
    """Get games accessible to admin with optional filters"""
    admin = User.query.get(admin_id)
    
    if not admin:
        return []
    
    query = Game.query
    
    if admin.role == 'superadmin':
        # Superadmin can see all games
        pass
    else:
        # Regular admin can only see games in their leagues
        admin_league_ids = [league['id'] for league in get_admin_leagues(admin_id)]
        if not admin_league_ids:
            return []
        query = query.filter(Game.league_id.in_(admin_league_ids))
    
    # Apply filters
    if league_id:
        query = query.filter(Game.league_id == league_id)
    
    if date_from:
        query = query.filter(Game.date >= date_from)
    
    if date_to:
        query = query.filter(Game.date <= date_to)
    
    games = query.order_by(Game.date.desc(), Game.time.desc()).all()
    
    result = []
    for game in games:
        # Get assignments
        assignments = GameAssignment.query.filter_by(game_id=game.id).all()
        
        game_data = {
            'id': game.id,
            'league_name': game.league.name if game.league else 'Unknown',
            'date': game.date,
            'time': game.time,
            'location_name': game.location.name if game.location else 'Unknown',
            'field_name': game.field_name,
            'home_team': game.home_team,
            'away_team': game.away_team,
            'game_level': game.game_level,
            'status': game.status,
            'fee_per_official': game.fee_per_official,
            'notes': game.notes,
            'special_instructions': game.special_instructions,
            'assignments': []
        }
        
        # Add assignment details
        for assignment in assignments:
            if assignment.official:
                game_data['assignments'].append({
                    'official_name': f"{assignment.official.first_name} {assignment.official.last_name}",
                    'position': assignment.position,
                    'status': assignment.status
                })
        
        result.append(game_data)
    
    return result

def get_league_by_name(league_name, admin_id):
    """Get league by name if accessible to admin"""
    admin_leagues = get_admin_leagues(admin_id)
    
    for league in admin_leagues:
        if league['name'] == league_name:
            return League.query.get(league['id'])
    
    return None

def get_location_by_name(location_name):
    """Get location by name"""
    return Location.query.filter_by(name=location_name).first()

def get_official_by_name(first_name, last_name, admin_id):
    """Get official by name if accessible to admin"""
    available_officials = get_available_officials(admin_id)
    
    for official in available_officials:
        if official['first_name'] == first_name and official['last_name'] == last_name:
            return User.query.get(official['id'])
    
    return None

def check_official_availability(official_id, game_date, game_time):
    """Check if official is available for game (simplified version)"""
    # Check for existing assignments at same time
    existing_assignment = db.session.query(GameAssignment).join(Game).filter(
        and_(
            GameAssignment.official_id == official_id,
            Game.date == game_date,
            Game.time == game_time,
            GameAssignment.status.in_(['assigned', 'accepted'])
        )
    ).first()
    
    return existing_assignment is None

def get_game_conflicts(game_date, game_time, location_id, field_name=None):
    """Get existing games that conflict with proposed game"""
    query = Game.query.filter(
        and_(
            Game.date == game_date,
            Game.time == game_time,
            Game.location_id == location_id
        )
    )
    
    if field_name:
        query = query.filter(Game.field_name == field_name)
    
    return query.all()

def get_user_statistics(admin_id):
    """Get statistics for admin's accessible data"""
    admin = User.query.get(admin_id)
    
    if not admin:
        return {}
    
    stats = {
        'leagues_count': 0,
        'games_count': 0,
        'officials_count': 0,
        'recent_games_count': 0
    }
    
    # Count leagues
    admin_leagues = get_admin_leagues(admin_id)
    stats['leagues_count'] = len(admin_leagues)
    
    # Count games
    admin_games = get_admin_games(admin_id)
    stats['games_count'] = len(admin_games)
    
    # Count officials
    available_officials = get_available_officials(admin_id)
    stats['officials_count'] = len(available_officials)
    
    # Count recent games (last 30 days)
    from datetime import date, timedelta
    recent_date = date.today() - timedelta(days=30)
    recent_games = get_admin_games(admin_id, date_from=recent_date)
    stats['recent_games_count'] = len(recent_games)
    
    return stats

def validate_admin_access_to_league(admin_id, league_id):
    """Check if admin has access to specific league"""
    admin_leagues = get_admin_leagues(admin_id)
    return any(league['id'] == league_id for league in admin_leagues)

def validate_admin_access_to_official(admin_id, official_id):
    """Check if admin can assign specific official"""
    available_officials = get_available_officials(admin_id)
    return any(official['id'] == official_id for official in available_officials)

def get_bulk_operation_summary(admin_id):
    """Get summary data for bulk operations dashboard"""
    admin_leagues = get_admin_leagues(admin_id)
    all_locations = get_all_locations()
    available_officials = get_available_officials(admin_id)
    
    return {
        'leagues': {
            'count': len(admin_leagues),
            'names': [league['name'] for league in admin_leagues[:5]]  # Show first 5
        },
        'locations': {
            'count': len(all_locations),
            'names': [location['name'] for location in all_locations[:5]]  # Show first 5
        },
        'officials': {
            'count': len(available_officials),
            'names': [f"{official['first_name']} {official['last_name']}" 
                     for official in available_officials[:5]]  # Show first 5
        }
    }

def get_local_users(admin_id):
    """Get users in admin's local list"""
    from models.database import User
    from models.local_user_list import LocalUserList
    
    admin = User.query.get(admin_id)
    if not admin:
        return []
    
    if admin.role == 'superadmin':
        # Superadmin sees all users (master list)
        users = User.query.filter(User.is_active == True).all()
    else:
        # Admin sees only their local list
        local_list = LocalUserList.query.filter_by(
            admin_id=admin_id, 
            is_active=True
        ).all()
        users = [item.user for item in local_list if item.user and item.user.is_active]
    
    return [
        {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'is_active': user.is_active
        }
        for user in users
    ]

def get_master_user_list():
    """Get master user list (superadmin only)"""
    from models.database import User
    
    users = User.query.filter(User.is_active == True).all()
    
    return [
        {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at
        }
        for user in users
    ]

# UPDATE the existing get_available_officials function:
def get_available_officials(admin_id):
    """Get officials available to admin for assignments - UPDATED"""
    from models.database import User
    
    admin = User.query.get(admin_id)
    
    if not admin:
        return []
    
    if admin.role == 'superadmin':
        # Superadmin can assign any official
        officials = User.query.filter(
            User.role.in_(['official', 'assigner', 'administrator'])
        ).all()
    else:
        # Regular admin can only assign officials from their local list
        local_users = get_local_users(admin_id)
        official_ids = [user['id'] for user in local_users 
                       if user['role'] in ['official', 'assigner', 'administrator']]
        
        officials = User.query.filter(
            User.id.in_(official_ids)
        ).all() if official_ids else []
    
    return [
        {
            'id': official.id,
            'first_name': official.first_name,
            'last_name': official.last_name,
            'email': official.email,
            'phone': official.phone
        }
        for official in officials
    ]