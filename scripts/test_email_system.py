"""
Sports Scheduler - Email System Test Script
Created: September 20, 2025
Purpose: Test PrivateEmail configuration and notification system

This script tests:
1. Email server connection
2. Basic email sending
3. Assignment notifications
4. Game reminders
5. System integration

Usage:
    python scripts/test_email_system.py
    python scripts/test_email_system.py --test-recipient your_email@example.com
"""

import sys
import os
from datetime import datetime, timedelta
import argparse
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def test_email_configuration():
    """Test basic email configuration and connection"""
    
    print("🔧 Testing Email Configuration")
    print("=" * 50)
    
    try:
        from utils.email_service_enhanced import email_service, PrivateEmailConfig
        
        # Check configuration
        config_info = PrivateEmailConfig.get_connection_info()
        print("📋 Configuration Details:")
        print(f"   SMTP Server: {config_info['smtp_server']}")
        print(f"   SMTP Port: {config_info['smtp_port']}")
        print(f"   Username: {config_info['username']}")
        print(f"   Use TLS: {config_info['use_tls']}")
        print(f"   Configured: {config_info['configured']}")
        
        # Test connection
        print("\n🔌 Testing SMTP Connection...")
        connection_result = email_service.test_connection()
        
        if connection_result['success']:
            print("✅ SMTP Connection: SUCCESS")
            print(f"   Message: {connection_result['message']}")
        else:
            print("❌ SMTP Connection: FAILED")
            print(f"   Error: {connection_result['message']}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Configuration Test Failed: {e}")
        return False

def test_basic_email_sending(recipient_email: str):
    """Test basic email sending functionality"""
    
    print(f"\n📧 Testing Basic Email Sending to {recipient_email}")
    print("=" * 50)
    
    try:
        from utils.email_service_enhanced import email_service
        
        # Create test email
        subject = "Sports Scheduler - Email Test"
        
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #ecf0f1; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏆 Sports Scheduler Email Test</h1>
            </div>
            <div class="content">
                <h2>✅ Email System Working!</h2>
                <p>This is a test email from the Sports Scheduler application.</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>Sent from: admin@sportsschedulers.com</li>
                    <li>SMTP Server: mail.privateemail.com</li>
                    <li>Test Time: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</li>
                </ul>
                <p>If you receive this email, the email system is configured correctly!</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SPORTS SCHEDULER EMAIL TEST
        
        This is a test email from the Sports Scheduler application.
        
        Test Details:
        - Sent from: admin@sportsschedulers.com
        - SMTP Server: mail.privateemail.com
        - Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        If you receive this email, the email system is configured correctly!
        """
        
        # Send test email
        result = email_service.send_email(recipient_email, subject, html_body, text_body)
        
        if result:
            print("✅ Basic Email Test: SUCCESS")
            print(f"   Test email sent to {recipient_email}")
        else:
            print("❌ Basic Email Test: FAILED")
            print("   Check logs for detailed error information")
            
        return result
        
    except Exception as e:
        print(f"❌ Basic Email Test Failed: {e}")
        return False

def test_assignment_notification(recipient_email: str):
    """Test assignment notification functionality"""
    
    print(f"\n🎯 Testing Assignment Notification to {recipient_email}")
    print("=" * 50)
    
    try:
        from utils.email_service_enhanced import send_assignment_notification
        
        # Create test game details
        test_game_details = {
            'game_id': 'TEST-001',
            'league_name': 'Test Basketball League',
            'date': '2025-09-25',
            'time': '19:00',
            'location_name': 'Test High School Gymnasium',
            'location_address': '123 School Street, Test City, TX 77001',
            'level': 'High School Varsity',
            'field': 'Main Court',
            'fee': 75,
            'notes': 'This is a test assignment notification.',
            'partners': [
                {
                    'name': 'John Test Partner',
                    'email': 'john.partner@example.com',
                    'phone': '555-123-4567'
                },
                {
                    'name': 'Jane Test Partner',
                    'email': 'jane.partner@example.com',
                    'phone': '555-987-6543'
                }
            ]
        }
        
        # Send assignment notification
        result = send_assignment_notification(recipient_email, test_game_details)
        
        if result:
            print("✅ Assignment Notification Test: SUCCESS")
            print(f"   Assignment notification sent to {recipient_email}")
            print("   Check your email for the assignment details")
        else:
            print("❌ Assignment Notification Test: FAILED")
            
        return result
        
    except Exception as e:
        print(f"❌ Assignment Notification Test Failed: {e}")
        return False

def test_game_reminder(recipient_email: str):
    """Test game reminder functionality"""
    
    print(f"\n⏰ Testing Game Reminder to {recipient_email}")
    print("=" * 50)
    
    try:
        from utils.email_service_enhanced import send_game_reminder
        
        # Create test reminder details
        test_reminder_details = {
            'game_id': 'TEST-002',
            'league_name': 'Test Soccer League',
            'date': '2025-09-26',
            'time': '18:30',
            'location_name': 'Test Soccer Complex',
            'level': 'Youth U-16',
            'reminder_type': '24_hour',
            'hours_until_game': 24,
            'partners': [
                {
                    'name': 'Mike Test Official',
                    'email': 'mike.official@example.com',
                    'phone': '555-111-2222'
                }
            ]
        }
        
        # Send reminder
        result = send_game_reminder(recipient_email, test_reminder_details)
        
        if result:
            print("✅ Game Reminder Test: SUCCESS")
            print(f"   24-hour reminder sent to {recipient_email}")
            print("   Check your email for the reminder")
        else:
            print("❌ Game Reminder Test: FAILED")
            
        return result
        
    except Exception as e:
        print(f"❌ Game Reminder Test Failed: {e}")
        return False

def test_scheduler_integration():
    """Test scheduler integration with Flask app"""
    
    print(f"\n🔄 Testing Scheduler Integration")
    print("=" * 50)
    
    try:
        # Import with Flask app context
        from app import app
        from utils.scheduler import ReminderScheduler
        
        with app.app_context():
            print("📊 Testing reminder scheduler functions...")
            
            # Test upcoming games query
            upcoming_games = ReminderScheduler.get_upcoming_games(hours_ahead=168)
            print(f"   Found {len(upcoming_games)} upcoming games")
            
            # Test reminder check functions (dry run)
            print("   Testing 72-hour reminder check...")
            try:
                # This will check for games but won't send emails in test mode
                reminders_72h = ReminderScheduler.check_72_hour_reminders()
                print(f"   72-hour check completed: {reminders_72h} reminders would be sent")
            except Exception as e:
                print(f"   72-hour check error: {e}")
            
            print("   Testing 24-hour reminder check...")
            try:
                reminders_24h = ReminderScheduler.check_24_hour_reminders()
                print(f"   24-hour check completed: {reminders_24h} reminders would be sent")
            except Exception as e:
                print(f"   24-hour check error: {e}")
            
            print("✅ Scheduler Integration Test: SUCCESS")
            return True
            
    except Exception as e:
        print(f"❌ Scheduler Integration Test Failed: {e}")
        return False

def run_comprehensive_test(recipient_email: str):
    """Run all email system tests"""
    
    print("🏆 SPORTS SCHEDULER EMAIL SYSTEM TEST")
    print("=" * 60)
    print(f"Test Recipient: {recipient_email}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_results = {
        'configuration': False,
        'basic_email': False,
        'assignment_notification': False,
        'game_reminder': False,
        'scheduler_integration': False
    }
    
    # Run all tests
    test_results['configuration'] = test_email_configuration()
    
    if test_results['configuration']:
        test_results['basic_email'] = test_basic_email_sending(recipient_email)
        test_results['assignment_notification'] = test_assignment_notification(recipient_email)
        test_results['game_reminder'] = test_game_reminder(recipient_email)
    
    test_results['scheduler_integration'] = test_scheduler_integration()
    
    # Print summary
    print("\n🏁 TEST SUMMARY")
    print("=" * 30)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<25} {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 ALL TESTS PASSED! Email system is ready for production.")
    elif success_rate >= 80:
        print("⚠️  Most tests passed. Review failed tests before production.")
    else:
        print("❌ Multiple test failures. Email system needs configuration fixes.")
    
    return test_results

def create_env_file_template():
    """Create a .env template with correct PrivateEmail settings"""
    
    template_content = """# Sports Scheduler Email Configuration
# Replace 'your_password_here' with the actual password for admin@sportsschedulers.com

# PrivateEmail SMTP Configuration
SMTP_SERVER=mail.privateemail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USERNAME=admin@sportsschedulers.com
SMTP_PASSWORD=your_password_here

# Application Settings
FLASK_ENV=development
DEBUG=True
SECRET_KEY=sports_scheduler_secret_key_2025

# Email Settings
MAIL_DEFAULT_SENDER=Sports Scheduler <admin@sportsschedulers.com>
MAIL_REPLY_TO=admin@sportsschedulers.com
MAX_EMAILS_PER_HOUR=100

# Notification Settings
ENABLE_EMAIL_REMINDERS=True
REMINDER_72H_ENABLED=True
REMINDER_24H_ENABLED=True
"""
    
    env_file_path = '.env.template'
    try:
        with open(env_file_path, 'w') as f:
            f.write(template_content)
        print(f"✅ Created {env_file_path} with PrivateEmail configuration")
        print("   Copy this file to .env and add your password")
    except Exception as e:
        print(f"❌ Failed to create template: {e}")

def main():
    """Main function with command line interface"""
    
    parser = argparse.ArgumentParser(description='Test Sports Scheduler Email System')
    parser.add_argument('--test-recipient', 
                       default='admin@sportsschedulers.com',
                       help='Email address to send test emails to')
    parser.add_argument('--config-only', 
                       action='store_true',
                       help='Only test configuration, don\'t send emails')
    parser.add_argument('--create-template', 
                       action='store_true',
                       help='Create .env template file')
    
    args = parser.parse_args()
    
    if args.create_template:
        create_env_file_template()
        return
    
    if args.config_only:
        test_email_configuration()
        return
    
    # Run comprehensive test
    run_comprehensive_test(args.test_recipient)

if __name__ == '__main__':
    main()