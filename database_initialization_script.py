#!/usr/bin/env python3
"""
Database Initialization Script for Sports Scheduler Phase 4
Creates all tables and populates with demo data including rankings

Run this script to ensure all Phase 4 tables exist:
python initialize_database.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.database import User
from models.league import League, Location
from models.game import Game, GameAssignment
from models.availability import OfficialRanking, OfficialAvailability
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

def create_all_tables():
    """Create all database tables"""
    print("Creating all database tables...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ All tables created successfully!")
            return True
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False

def populate_demo_rankings():
    """Create demo ranking data for testing"""
    print("Creating demo ranking data...")
    
    with app.app_context():
        try:
            # Get users and leagues
            users = User.query.filter(User.role.in_(['official', 'assigner', 'administrator'])).all()
            leagues = League.query.all()
            
            if not users or not leagues:
                print("❌ No users or leagues found. Create basic data first.")
                return False
            
            rankings_created = 0
            
            # Create rankings for each user in each league
            for league in leagues:
                for i, user in enumerate(users):
                    # Skip if ranking already exists
                    existing = OfficialRanking.query.filter_by(
                        user_id=user.id,
                        league_id=league.id
                    ).first()
                    
                    if not existing:
                        # Assign varied rankings (distribute 2-5, with more 3s and 4s)
                        if i % 5 == 0:
                            ranking_value = 5  # Expert
                        elif i % 4 == 0:
                            ranking_value = 2  # Developing  
                        elif i % 3 == 0:
                            ranking_value = 4  # Proficient
                        else:
                            ranking_value = 3  # Competent
                        
                        ranking = OfficialRanking(
                            user_id=user.id,
                            league_id=league.id,
                            ranking=ranking_value
                        )
                        db.session.add(ranking)
                        rankings_created += 1
            
            db.session.commit()
            print(f"✅ Created {rankings_created} demo rankings!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo rankings: {e}")
            return False

def populate_demo_availability():
    """Create demo availability data"""
    print("Creating demo availability data...")
    
    with app.app_context():
        try:
            users = User.query.filter(User.role.in_(['official', 'assigner', 'administrator'])).all()
            
            if not users:
                print("❌ No users found for availability data.")
                return False
            
            availability_created = 0
            
            # Create some blocked availability for testing
            for i, user in enumerate(users):
                # Block some weekends for variety
                if i % 3 == 0:  # Every 3rd user has weekend blocks
                    for week_offset in range(4):  # Next 4 weekends
                        weekend_date = date.today() + timedelta(days=(5 - date.today().weekday()) + (week_offset * 7))
                        
                        availability = OfficialAvailability(
                            user_id=user.id,
                            availability_type='unavailable_all_day',
                            start_date=weekend_date,
                            end_date=weekend_date,
                            reason="Weekend family time"
                        )
                        db.session.add(availability)
                        availability_created += 1
                
                # Block some specific time periods
                if i % 4 == 0:  # Every 4th user has specific time blocks
                    block_date = date.today() + timedelta(days=10)
                    availability = OfficialAvailability(
                        user_id=user.id,
                        availability_type='unavailable_hours',
                        start_date=block_date,
                        end_date=block_date,
                        start_time=time(9, 0),
                        end_time=time(12, 0),
                        reason="Morning appointment"
                    )
                    db.session.add(availability)
                    availability_created += 1
            
            db.session.commit()
            print(f"✅ Created {availability_created} demo availability records!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo availability: {e}")
            return False

def verify_game_assignments():
    """Verify and create additional game assignments if needed"""
    print("Verifying game assignments...")
    
    with app.app_context():
        try:
            # Check existing assignments
            assignments = GameAssignment.query.count()
            print(f"Current assignments: {assignments}")
            
            if assignments < 5:  # Create more if we don't have enough
                games = Game.query.limit(3).all()
                users = User.query.filter(User.role.in_(['official', 'assigner', 'administrator'])).limit(5).all()
                
                if games and users:
                    created = 0
                    for game in games:
                        for i, user in enumerate(users[:2]):  # 2 officials per game
                            existing = GameAssignment.query.filter_by(
                                game_id=game.id,
                                user_id=user.id
                            ).first()
                            
                            if not existing:
                                assignment = GameAssignment(
                                    game_id=game.id,
                                    user_id=user.id,
                                    position=f"Official {i+1}",
                                    assignment_type='manual',
                                    status='assigned'
                                )
                                db.session.add(assignment)
                                created += 1
                    
                    db.session.commit()
                    print(f"✅ Created {created} additional assignments!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error verifying assignments: {e}")
            return False

def check_database_integrity():
    """Check that all required tables exist"""
    print("Checking database integrity...")
    
    with app.app_context():
        try:
            # Test each model
            models_to_test = [
                ('User', User),
                ('League', League),
                ('Location', Location),
                ('Game', Game),
                ('GameAssignment', GameAssignment),
                ('OfficialRanking', OfficialRanking),
                ('OfficialAvailability', OfficialAvailability)
            ]
            
            for model_name, model_class in models_to_test:
                try:
                    count = model_class.query.count()
                    print(f"✅ {model_name}: {count} records")
                except Exception as e:
                    print(f"❌ {model_name}: Error - {e}")
                    return False
            
            print("✅ Database integrity check passed!")
            return True
            
        except Exception as e:
            print(f"❌ Database integrity check failed: {e}")
            return False

def main():
    """Main initialization function"""
    print("🚀 Sports Scheduler Phase 4 Database Initialization")
    print("=" * 60)
    
    # Step 1: Create tables
    if not create_all_tables():
        print("❌ Failed to create tables. Exiting.")
        return False
    
    # Step 2: Check integrity
    if not check_database_integrity():
        print("❌ Database integrity check failed. Exiting.")
        return False
    
    # Step 3: Create demo rankings
    if not populate_demo_rankings():
        print("⚠️ Warning: Could not create demo rankings")
    
    # Step 4: Create demo availability
    if not populate_demo_availability():
        print("⚠️ Warning: Could not create demo availability")
    
    # Step 5: Verify assignments
    if not verify_game_assignments():
        print("⚠️ Warning: Could not verify game assignments")
    
    print("\n" + "=" * 60)
    print("🎉 Phase 4 Database Initialization Complete!")
    print("\nNext Steps:")
    print("1. Start the application: python app.py")
    print("2. Login as admin: admin@sportsscheduler.com / admin123")
    print("3. Navigate to Game Management > Official Assignments")
    print("4. Test the new assignment response workflow")
    print("5. Check Admin > Manage Rankings")
    print("\n✅ Ready to continue Phase 4 implementation!")
    
    return True

if __name__ == "__main__":
    main()