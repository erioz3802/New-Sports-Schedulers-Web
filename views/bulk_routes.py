# views/bulk_routes.py - Enhanced Bulk Operations System
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime, date
from utils.bulk_template_generator import (
    generate_games_only_template, 
    generate_games_with_assignments_template
)
from utils.bulk_processor import process_games_upload, validate_upload_file
from utils.decorators import admin_required

bulk_bp = Blueprint('bulk', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bulk_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Main bulk operations dashboard"""
    return render_template('bulk/dashboard.html', 
                         title='Bulk Operations Dashboard')

@bulk_bp.route('/games/templates')
@login_required
@admin_required
def game_templates():
    """Template download page for games"""
    # Get counts for display
    from models.league import League
    from models.database import User
    from sqlalchemy import and_
    
    # Count admin's accessible leagues
    if current_user.role == 'superadmin':
        league_count = League.query.count()
        official_count = User.query.filter(User.role.in_(['official', 'assigner', 'administrator'])).count()
    else:
        # For regular admins, count their leagues and accessible officials
        league_count = League.query.filter_by(created_by=current_user.id).count()
        official_count = User.query.filter(
            and_(
                User.role.in_(['official', 'assigner']),
                User.id != current_user.id
            )
        ).count()
    
    from models.league import Location
    location_count = Location.query.count()
    
    return render_template('bulk/game_templates.html',
                         title='Download Game Templates',
                         league_count=league_count,
                         location_count=location_count,
                         official_count=official_count)

@bulk_bp.route('/games/template/download')
@login_required
@admin_required
def download_game_template():
    """Generate and download dynamic game template"""
    template_type = request.args.get('type', 'games_only')
    
    try:
        if template_type == 'games_only':
            file_path, filename = generate_games_only_template(current_user.id)
        elif template_type == 'with_assignments':
            file_path, filename = generate_games_with_assignments_template(current_user.id)
        else:
            flash('Invalid template type requested.', 'error')
            return redirect(url_for('bulk.game_templates'))
        
        # Send file and cleanup
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Clean up temp file after sending
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(file_path)
            except:
                pass
        
        flash(f'Template downloaded successfully: {filename}', 'success')
        return response
        
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('bulk.game_templates'))

# Replace the upload_games function with this enhanced debug version:

@bulk_bp.route('/games/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_games():
    """Upload and process games bulk file - ENHANCED DEBUG VERSION"""
    
    # Debug GET requests
    if request.method == 'GET':
        print("DEBUG: GET request to upload_games")
        try:
            return render_template('bulk/upload_games.html', title='Upload Games')
        except Exception as e:
            return f"<h1>Template Error in upload_games.html</h1><pre>{str(e)}</pre>"
    
    print("DEBUG: POST request started")
    
    # Check file upload with debugging
    try:
        if 'file' not in request.files:
            print("DEBUG: No file in request")
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        print(f"DEBUG: File received: {file.filename}")
        
        if file.filename == '':
            print("DEBUG: Empty filename")
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            print(f"DEBUG: File type not allowed: {file.filename}")
            flash('Please upload an Excel file (.xlsx or .xls).', 'error')
            return redirect(request.url)
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        print(f"DEBUG: File size: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            print("DEBUG: File too large")
            flash('File too large. Maximum size is 16MB.', 'error')
            return redirect(request.url)
        
    except Exception as e:
        return f"<h1>Error in File Validation</h1><pre>{str(e)}</pre>"
    
    # File processing with enhanced debugging
    temp_fd = None
    file_path = None
    temp_dir = None
    
    try:
        print("DEBUG: Starting file processing")
        
        # Create secure temporary file
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        print(f"DEBUG: Created temp directory: {temp_dir}")
        
        temp_fd, file_path = tempfile.mkstemp(
            suffix=os.path.splitext(filename)[1],
            dir=temp_dir
        )
        print(f"DEBUG: Created temp file: {file_path}")
        
        # Save uploaded file to temporary location
        with os.fdopen(temp_fd, 'wb') as temp_file:
            file.stream.seek(0)
            temp_file.write(file.stream.read())
            temp_fd = None
        print("DEBUG: File saved to temp location")
        
        # Validate file structure
        print("DEBUG: Starting file validation")
        validation_result = validate_upload_file(file_path)
        print(f"DEBUG: Validation result: {validation_result}")
        
        if not validation_result['valid']:
            error_msg = f'File validation failed: {validation_result["error"]}'
            print(f"DEBUG: Validation failed: {error_msg}")
            flash(error_msg, 'error')
            return redirect(request.url)
        
        # Process the file
        print("DEBUG: Starting file processing")
        process_mode = request.form.get('process_mode', 'validate_only')
        print(f"DEBUG: Process mode: {process_mode}")
        
        results = process_games_upload(file_path, current_user.id, process_mode)
        print(f"DEBUG: Processing complete. Results: {results}")
        
        # Return results as plain text (bypass template issues)
        debug_output = f"""
UPLOAD PROCESSING RESULTS
========================
Success Count: {results['success_count']}
Error Count: {results['error_count']}
Warning Count: {results['warning_count']}
Process Mode: {results['process_mode']}

ERRORS ({len(results['errors'])}):
{chr(10).join(f"  • {error}" for error in results['errors']) if results['errors'] else '  None'}

WARNINGS ({len(results['warnings'])}):
{chr(10).join(f"  • {warning}" for warning in results['warnings']) if results['warnings'] else '  None'}

PREVIEW DATA:
{len(results['preview_data'])} items found

FIRST FEW PREVIEW ITEMS:
{chr(10).join(f"  Row {item['row']}: {item['league_name']} - {item['home_team']} vs {item['away_team']}" for item in results['preview_data'][:5])}
        """
        
        return f"<pre>{debug_output}</pre><br><a href='/bulk/games/upload'>← Back to Upload</a>"
        
    except Exception as e:
        # Full error details
        import traceback
        error_details = f"""
PROCESSING ERROR DETAILS
========================
Error Type: {type(e).__name__}
Error Message: {str(e)}
File Path: {file_path}
Temp Dir: {temp_dir}

FULL TRACEBACK:
{traceback.format_exc()}
        """
        print(f"DEBUG: Exception occurred: {str(e)}")
        return f"<pre>{error_details}</pre><br><a href='/bulk/games/upload'>← Back to Upload</a>"
        
    finally:
        # Cleanup with debugging
        print("DEBUG: Starting cleanup")
        
        if temp_fd is not None:
            try:
                os.close(temp_fd)
                print("DEBUG: Closed file descriptor")
            except Exception as e:
                print(f"DEBUG: Error closing fd: {e}")
        
        if file_path and os.path.exists(file_path):
            for attempt in range(3):
                try:
                    os.unlink(file_path)
                    print(f"DEBUG: Deleted temp file on attempt {attempt + 1}")
                    break
                except PermissionError as e:
                    print(f"DEBUG: Permission error on attempt {attempt + 1}: {e}")
                    if attempt < 2:
                        import time
                        time.sleep(0.1)
                except Exception as e:
                    print(f"DEBUG: Other error deleting file: {e}")
                    break
        
        if temp_dir and os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
                print("DEBUG: Removed temp directory")
            except Exception as e:
                print(f"DEBUG: Error removing temp dir: {e}")
        
        print("DEBUG: Cleanup complete")
@bulk_bp.route('/games/preview', methods=['POST'])
@login_required
@admin_required
def preview_games_upload():
    """Preview games upload without saving to database"""
    # Similar to upload_games but with process_mode='preview'
    return upload_games()

@bulk_bp.route('/export/games')
@login_required
@admin_required
def export_games():
    """Export existing games to Excel template format"""
    try:
        from utils.bulk_exporter import export_admin_games
        
        # Get filters from request
        league_id = request.args.get('league_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        include_assignments = request.args.get('include_assignments', 'false') == 'true'
        
        # Generate export file
        file_path, filename = export_admin_games(
            admin_id=current_user.id,
            league_id=league_id,
            date_from=date_from,
            date_to=date_to,
            include_assignments=include_assignments
        )
        
        # Send file
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Cleanup
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(file_path)
            except:
                pass
        
        return response
        
    except Exception as e:
        flash(f'Error exporting games: {str(e)}', 'error')
        return redirect(url_for('bulk.dashboard'))

@bulk_bp.route('/help')
@login_required
@admin_required
def help_page():
    """Bulk operations help and documentation"""
    return render_template('bulk/help.html', 
                         title='Bulk Operations Help')

# API endpoints for dynamic data
@bulk_bp.route('/api/leagues')
@login_required
@admin_required
def api_admin_leagues():
    """Get admin's accessible leagues for AJAX calls"""
    from utils.data_helpers import get_admin_leagues
    leagues = get_admin_leagues(current_user.id)
    return jsonify(leagues)

@bulk_bp.route('/api/locations')
@login_required
@admin_required
def api_all_locations():
    """Get all locations for AJAX calls"""
    from utils.data_helpers import get_all_locations
    locations = get_all_locations()
    return jsonify(locations)

@bulk_bp.route('/api/officials')
@login_required
@admin_required
def api_available_officials():
    """Get admin's available officials for AJAX calls"""
    from utils.data_helpers import get_available_officials
    officials = get_available_officials(current_user.id)
    return jsonify(officials)