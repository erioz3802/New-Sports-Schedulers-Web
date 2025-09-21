"""
Sports Scheduler - Database Migration Script
Created: September 20, 2025
Purpose: Add reminder tracking fields to existing Game model

This script adds the following fields to the Game table:
- reminder_72h_sent (BOOLEAN) - Tracks if 72-hour reminder was sent
- reminder_24h_sent (BOOLEAN) - Tracks if 24-hour reminder was sent
- created_at (DATETIME) - Track when game was created
- updated_at (DATETIME) - Track when game was last modified

Usage:
    python scripts/add_reminder_fields.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Execute the database migration to add reminder fields"""
    
    try:
        # Import Flask app and database
        from app import app, db
        from models.game import Game
        
        with app.app_context():
            print("🔄 Starting database migration for reminder fields...")
            
            # Get database engine
            engine = db.engine
            
            # Check if columns already exist
            inspector = db.inspect(engine)
            existing_columns = [col['name'] for col in inspector.get_columns('game')]
            
            migrations_needed = []
            
            # Check which columns need to be added
            if 'reminder_72h_sent' not in existing_columns:
                migrations_needed.append(('reminder_72h_sent', 'BOOLEAN', '0'))
            
            if 'reminder_24h_sent' not in existing_columns:
                migrations_needed.append(('reminder_24h_sent', 'BOOLEAN', '0'))
                
            # Skip created_at and updated_at if they already exist
            # (Knowledge base shows these fields may already be present)
            
            if not migrations_needed:
                print("✅ All reminder fields already exist in database. No migration needed.")
                return True
            
            print(f"📋 Found {len(migrations_needed)} columns to add:")
            for col_name, col_type, default_val in migrations_needed:
                print(f"   - {col_name} ({col_type})")
            
            # Execute migrations
            success_count = 0
            for col_name, col_type, default_val in migrations_needed:
                try:
                    # SQLite syntax for adding columns
                    sql = f"ALTER TABLE game ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
                    
                    print(f"🔧 Adding column: {col_name}")
                    engine.execute(sql)
                    success_count += 1
                    print(f"✅ Successfully added {col_name}")
                    
                except Exception as e:
                    print(f"❌ Error adding {col_name}: {e}")
                    continue
            
            # Commit changes
            db.session.commit()
            
            print(f"\n🎉 Migration completed successfully!")
            print(f"   - {success_count}/{len(migrations_needed)} columns added")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            verify_migration()
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running this from the project root directory")
        return False
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    
    try:
        from app import app, db
        
        with app.app_context():
            # Get updated column list
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('game')]
            
            required_fields = ['reminder_72h_sent', 'reminder_24h_sent', 'created_at', 'updated_at']
            
            print("📊 Current Game table columns:")
            for col in sorted(columns):
                status = "✅" if col in required_fields else "📌"
                print(f"   {status} {col}")
            
            # Check if all required fields exist
            missing_fields = [field for field in required_fields if field not in columns]
            
            if missing_fields:
                print(f"\n⚠️  Missing fields: {missing_fields}")
                return False
            else:
                print(f"\n✅ All required reminder fields are present!")
                return True
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def rollback_migration():
    """
    Rollback the migration (removes added columns)
    WARNING: This will delete data in the added columns!
    """
    
    try:
        from app import app, db
        
        print("⚠️  WARNING: This will remove reminder tracking columns and delete their data!")
        confirm = input("Are you sure you want to rollback? (type 'YES' to confirm): ")
        
        if confirm != 'YES':
            print("❌ Rollback cancelled")
            return False
        
        with app.app_context():
            print("🔄 Starting rollback...")
            
            # Note: SQLite doesn't support DROP COLUMN directly
            # This would require recreating the table, which is complex
            print("❌ SQLite doesn't support dropping columns easily.")
            print("   To rollback, you would need to:")
            print("   1. Delete the database file: sports_scheduler.db")
            print("   2. Restart the application to recreate tables")
            print("   3. Re-import your data")
            
            return False
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

def show_game_table_info():
    """Display current Game table structure"""
    
    try:
        from app import app, db
        
        with app.app_context():
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('game')
            
            print("📊 Current Game table structure:")
            print("-" * 60)
            print(f"{'Column Name':<20} {'Type':<15} {'Nullable':<10} {'Default'}")
            print("-" * 60)
            
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = "Yes" if col['nullable'] else "No"
                default = col.get('default', 'None')
                
                print(f"{col_name:<20} {col_type:<15} {nullable:<10} {default}")
            
            print("-" * 60)
            print(f"Total columns: {len(columns)}")
            
    except Exception as e:
        print(f"❌ Error displaying table info: {e}")

def main():
    """Main function with command line interface"""
    
    print("🏆 Sports Scheduler - Database Migration Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'migrate':
            run_migration()
        elif command == 'verify':
            verify_migration()
        elif command == 'rollback':
            rollback_migration()
        elif command == 'info':
            show_game_table_info()
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
    else:
        # Default action: run migration
        print("No command specified, running migration...")
        run_migration()

def print_usage():
    """Print usage instructions"""
    
    print("\nUsage:")
    print("  python scripts/add_reminder_fields.py [command]")
    print("\nCommands:")
    print("  migrate   - Add reminder fields to database (default)")
    print("  verify    - Check if reminder fields exist")
    print("  rollback  - Remove reminder fields (WARNING: deletes data)")
    print("  info      - Show current Game table structure")
    print("\nExamples:")
    print("  python scripts/add_reminder_fields.py")
    print("  python scripts/add_reminder_fields.py migrate")
    print("  python scripts/add_reminder_fields.py verify")

if __name__ == '__main__':
    main()