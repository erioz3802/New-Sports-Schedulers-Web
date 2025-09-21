"""
Sports Scheduler - Enhanced Email Service with PrivateEmail Configuration
Created: September 20, 2025
Updated for: admin@sportsschedulers.com via mail.privateemail.com
Filename: utils/email_service_enhanced.py (to avoid conflict with existing email_service.py)

This module handles all email notifications including:
- Assignment notifications
- Game reminders (72-hour and 24-hour)
- Game change notifications
- Cancellation notifications

Email Server Configuration:
- SMTP Server: mail.privateemail.com
- SMTP Port: 587 (TLS)
- From Address: admin@sportsschedulers.com

INTEGRATION NOTE: This file should be saved as utils/email_service_enhanced.py
to avoid conflicts with the existing utils/email_service.py file.
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
from flask import current_app

class PrivateEmailConfig:
    """
    Email configuration for Sports Schedulers PrivateEmail account
    """
    
    # PrivateEmail Server Configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'mail.privateemail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_USE_SSL = os.environ.get('SMTP_USE_SSL', 'False').lower() == 'true'
    
    # IMAP/POP Configuration (for future features)
    IMAP_SERVER = os.environ.get('IMAP_SERVER', 'mail.privateemail.com')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', 993))
    POP_SERVER = os.environ.get('POP_SERVER', 'mail.privateemail.com')
    POP_PORT = int(os.environ.get('POP_PORT', 995))
    
    # Account Credentials
    USERNAME = os.environ.get('SMTP_USERNAME', 'admin@sportsschedulers.com')
    PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # Email Headers
    DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Sports Scheduler <admin@sportsschedulers.com>')
    REPLY_TO = os.environ.get('MAIL_REPLY_TO', 'admin@sportsschedulers.com')
    
    # Rate Limiting
    MAX_EMAILS_PER_HOUR = int(os.environ.get('MAX_EMAILS_PER_HOUR', 100))
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if email is properly configured"""
        return bool(cls.USERNAME and cls.PASSWORD)
    
    @classmethod
    def get_connection_info(cls) -> Dict:
        """Get connection information for debugging"""
        return {
            'smtp_server': cls.SMTP_SERVER,
            'smtp_port': cls.SMTP_PORT,
            'username': cls.USERNAME,
            'use_tls': cls.SMTP_USE_TLS,
            'use_ssl': cls.SMTP_USE_SSL,
            'configured': cls.is_configured()
        }

class EmailService:
    """
    Email service for Sports Scheduler application
    Handles all outgoing email notifications
    """
    
    def __init__(self):
        self.config = PrivateEmailConfig()
        self.logger = logging.getLogger(__name__)
    
    def _create_smtp_connection(self):
        """
        Create and authenticate SMTP connection
        
        Returns:
            smtplib.SMTP: Authenticated SMTP connection
        """
        try:
            # Create SMTP connection
            if self.config.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            else:
                server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            
            # Enable debug output if in development
            if os.environ.get('FLASK_ENV') == 'development':
                server.set_debuglevel(1)
            
            # Start TLS if not using SSL
            if self.config.SMTP_USE_TLS and not self.config.SMTP_USE_SSL:
                server.starttls()
            
            # Authenticate
            server.login(self.config.USERNAME, self.config.PASSWORD)
            
            self.logger.info(f"Successfully connected to {self.config.SMTP_SERVER}")
            return server
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> bool:
        """
        Send email using PrivateEmail SMTP server
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (optional)
            
        Returns:
            bool: True if email sent successfully
        """
        
        if not self.config.is_configured():
            self.logger.warning("Email not configured - skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.DEFAULT_SENDER
            msg['To'] = to_email
            msg['Reply-To'] = self.config.REPLY_TO
            msg['Subject'] = subject
            
            # Add plain text version
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(
                    self.config.USERNAME,
                    [to_email],
                    msg.as_string()
                )
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def test_connection(self) -> Dict:
        """
        Test email server connection
        
        Returns:
            Dict: Connection test results
        """
        result = {
            'success': False,
            'message': '',
            'config': self.config.get_connection_info(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if not self.config.is_configured():
                result['message'] = 'Email credentials not configured'
                return result
            
            # Test connection
            with self._create_smtp_connection() as server:
                result['success'] = True
                result['message'] = 'Successfully connected to PrivateEmail server'
                
        except Exception as e:
            result['message'] = f'Connection failed: {str(e)}'
            
        return result

# Initialize email service
email_service = EmailService()

# =============================================================================
# EMAIL TEMPLATE FUNCTIONS
# =============================================================================

def send_assignment_notification(official_email: str, game_details: Dict) -> bool:
    """
    Send assignment notification to official
    
    Args:
        official_email: Official's email address
        game_details: Dictionary with game information
        
    Returns:
        bool: True if sent successfully
    """
    
    subject = f"Game Assignment - {game_details.get('league_name', 'Sports Game')}"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 30px; }}
            .game-details {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #2c3e50; }}
            .partners {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 Game Assignment Notification</h1>
                <p>You have been assigned to officiate a game</p>
            </div>
            
            <div class="game-details">
                <h2>Game Details</h2>
                <div class="detail-row">
                    <span class="label">League:</span> {game_details.get('league_name', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> {game_details.get('date', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> {game_details.get('time', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Location:</span> {game_details.get('location_name', 'TBD')}
                </div>
                {f'<div class="detail-row"><span class="label">Address:</span> {game_details.get("location_address", "")}</div>' if game_details.get('location_address') else ''}
                <div class="detail-row">
                    <span class="label">Level:</span> {game_details.get('level', 'Not specified')}
                </div>
                {f'<div class="detail-row"><span class="label">Field:</span> {game_details.get("field", "")}</div>' if game_details.get('field') else ''}
                {f'<div class="detail-row"><span class="label">Game Fee:</span> ${game_details.get("fee", 0)}</div>' if game_details.get('fee') else ''}
            </div>
            
            {_render_partners_section(game_details.get('partners', []))}
            
            {f'<div class="game-details"><h3>Notes</h3><p>{game_details.get("notes")}</p></div>' if game_details.get('notes') else ''}
            
            <div class="footer">
                <p>This assignment was sent from Sports Scheduler</p>
                <p>Please contact admin@sportsschedulers.com if you have any questions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    GAME ASSIGNMENT NOTIFICATION
    
    You have been assigned to officiate the following game:
    
    League: {game_details.get('league_name', 'TBD')}
    Date: {game_details.get('date', 'TBD')}
    Time: {game_details.get('time', 'TBD')}
    Location: {game_details.get('location_name', 'TBD')}
    Level: {game_details.get('level', 'Not specified')}
    
    {_render_partners_text(game_details.get('partners', []))}
    
    Questions? Contact admin@sportsschedulers.com
    """
    
    return email_service.send_email(official_email, subject, html_body, text_body)

def send_game_reminder(official_email: str, game_details: Dict) -> bool:
    """
    Send game reminder to official
    
    Args:
        official_email: Official's email address
        game_details: Dictionary with game information
        
    Returns:
        bool: True if sent successfully
    """
    
    reminder_type = game_details.get('reminder_type', '24_hour')
    hours = game_details.get('hours_until_game', 24)
    
    subject = f"Game Reminder - {hours}h - {game_details.get('league_name', 'Sports Game')}"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 30px; }}
            .reminder-notice {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }}
            .game-details {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #2c3e50; }}
            .partners {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏰ Game Reminder</h1>
                <p>Upcoming game in {hours} hours</p>
            </div>
            
            <div class="reminder-notice">
                <h2>🚨 Don't Forget!</h2>
                <p>You have a game scheduled for <strong>{game_details.get('date', 'TBD')} at {game_details.get('time', 'TBD')}</strong></p>
            </div>
            
            <div class="game-details">
                <h2>Game Details</h2>
                <div class="detail-row">
                    <span class="label">League:</span> {game_details.get('league_name', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> {game_details.get('date', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> {game_details.get('time', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Location:</span> {game_details.get('location_name', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Level:</span> {game_details.get('level', 'Not specified')}
                </div>
            </div>
            
            {_render_partners_section(game_details.get('partners', []))}
            
            <div class="footer">
                <p>This reminder was sent from Sports Scheduler</p>
                <p>Contact admin@sportsschedulers.com if you have any questions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    GAME REMINDER - {hours} HOURS
    
    Don't forget! You have a game in {hours} hours:
    
    League: {game_details.get('league_name', 'TBD')}
    Date: {game_details.get('date', 'TBD')}
    Time: {game_details.get('time', 'TBD')}
    Location: {game_details.get('location_name', 'TBD')}
    Level: {game_details.get('level', 'Not specified')}
    
    {_render_partners_text(game_details.get('partners', []))}
    
    Questions? Contact admin@sportsschedulers.com
    """
    
    return email_service.send_email(official_email, subject, html_body, text_body)

def send_game_change_notification(official_email: str, game_details: Dict) -> bool:
    """
    Send game change notification to official
    
    Args:
        official_email: Official's email address
        game_details: Dictionary with game information and changes
        
    Returns:
        bool: True if sent successfully
    """
    
    change_type = game_details.get('change_type', 'changed')
    subject = f"Game {change_type.title()} - {game_details.get('league_name', 'Sports Game')}"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background-color: #f39c12; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 30px; }}
            .change-notice {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .game-details {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #2c3e50; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Game Update</h1>
                <p>Changes to your assigned game</p>
            </div>
            
            <div class="change-notice">
                <h2>⚠️ Important Update</h2>
                <p>There have been changes to your assigned game. Please review the updated details below.</p>
            </div>
            
            <div class="game-details">
                <h2>Updated Game Details</h2>
                <div class="detail-row">
                    <span class="label">League:</span> {game_details.get('league_name', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> {game_details.get('date', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> {game_details.get('time', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Location:</span> {game_details.get('location_name', 'TBD')}
                </div>
            </div>
            
            <div class="footer">
                <p>This update was sent from Sports Scheduler</p>
                <p>Contact admin@sportsschedulers.com if you have any questions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return email_service.send_email(official_email, subject, html_body)

def send_cancellation_notification(official_email: str, game_details: Dict) -> bool:
    """
    Send game cancellation notification to official
    
    Args:
        official_email: Official's email address
        game_details: Dictionary with game information
        
    Returns:
        bool: True if sent successfully
    """
    
    subject = f"Game Cancelled - {game_details.get('league_name', 'Sports Game')}"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 30px; }}
            .cancel-notice {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }}
            .game-details {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #2c3e50; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>❌ Game Cancelled</h1>
                <p>Your assigned game has been cancelled</p>
            </div>
            
            <div class="cancel-notice">
                <h2>🚫 Cancellation Notice</h2>
                <p>The following game has been <strong>CANCELLED</strong>. You are no longer assigned to this game.</p>
            </div>
            
            <div class="game-details">
                <h2>Cancelled Game Details</h2>
                <div class="detail-row">
                    <span class="label">League:</span> {game_details.get('league_name', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> {game_details.get('date', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> {game_details.get('time', 'TBD')}
                </div>
                <div class="detail-row">
                    <span class="label">Location:</span> {game_details.get('location_name', 'TBD')}
                </div>
            </div>
            
            <div class="footer">
                <p>This cancellation notice was sent from Sports Scheduler</p>
                <p>Contact admin@sportsschedulers.com if you have any questions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return email_service.send_email(official_email, subject, html_body)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _render_partners_section(partners: List[Dict]) -> str:
    """Render partners section for HTML emails"""
    if not partners:
        return ""
    
    partners_html = '<div class="partners"><h3>Your Partners</h3>'
    for partner in partners:
        partners_html += f"""
        <div style="margin: 10px 0; padding: 10px; background-color: white; border-radius: 3px;">
            <strong>{partner.get('name', 'Unknown')}</strong><br>
            📧 {partner.get('email', 'No email')}<br>
            📞 {partner.get('phone', 'No phone')}
        </div>
        """
    partners_html += '</div>'
    return partners_html

def _render_partners_text(partners: List[Dict]) -> str:
    """Render partners section for text emails"""
    if not partners:
        return ""
    
    text = "Your Partners:\n"
    for partner in partners:
        text += f"- {partner.get('name', 'Unknown')} ({partner.get('email', 'No email')}) - {partner.get('phone', 'No phone')}\n"
    
    return text

# =============================================================================
# TESTING FUNCTIONS
# =============================================================================

def test_email_connection():
    """Test email server connection"""
    return email_service.test_connection()

def send_test_email(to_email: str) -> bool:
    """Send a test email to verify configuration"""
    
    test_details = {
        'league_name': 'Test League',
        'date': '2025-09-21',
        'time': '19:00',
        'location_name': 'Test Stadium',
        'level': 'Test Level',
        'partners': [{
            'name': 'Test Partner',
            'email': 'test@example.com',
            'phone': '555-1234'
        }]
    }
    
    return send_assignment_notification(to_email, test_details)