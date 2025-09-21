# views/report_routes.py - Reporting System Routes
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from functools import wraps
import io
import csv

# Avoid circular imports by importing models when needed
def get_models():
    """Get model classes when needed"""
    from models.database import User
    from models.reports import FinancialReport, GameReport
    return User, FinancialReport, GameReport

def get_league_model():
    """Get League model when available"""
    try:
        from models.league import League
        return League
    except ImportError:
        # Fallback if League model not available
        return None

report_bp = Blueprint('report', __name__)

def reports_access_required(f):
    """Decorator to require report access permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # All authenticated users can access some reports
        return f(*args, **kwargs)
    return decorated_function

@report_bp.route('/dashboard')
@login_required
@reports_access_required
def dashboard():
    """Reports dashboard with role-based content"""
    User, FinancialReport, GameReport = get_models()
    
    # Get date range (default to last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    dashboard_data = {}
    
    if current_user.role == 'official':
        # Official-specific reports
        earnings_data = FinancialReport.get_official_earnings(
            current_user.id, start_date, end_date
        )
        game_history = GameReport.get_official_game_history(current_user.id, 10)
        
        dashboard_data.update({
            'earnings_data': earnings_data,
            'recent_games': game_history
        })
    
    elif current_user.role in ['administrator', 'superadmin']:
        # Admin reports
        if current_user.is_superadmin:
            global_financials = FinancialReport.get_global_financials(start_date, end_date)
            dashboard_data['global_financials'] = global_financials
        
        # Get leagues if available
        League = get_league_model()
        if League:
            leagues = League.query.filter_by(is_active=True).all()
            league_stats = []
            
            for league in leagues[:5]:  # Limit to top 5 for dashboard
                stats = GameReport.get_league_statistics(league.id)
                financials = FinancialReport.get_league_financials(league.id, start_date, end_date)
                
                league_stats.append({
                    'league': league,
                    'stats': stats,
                    'financials': financials
                })
            
            dashboard_data['league_stats'] = league_stats
    
    elif current_user.role == 'assigner':
        # Assigner reports (similar to admin but limited scope)
        earnings_data = FinancialReport.get_official_earnings(
            current_user.id, start_date, end_date
        )
        dashboard_data['earnings_data'] = earnings_data
    
    return render_template('reports/dashboard.html', **dashboard_data)

@report_bp.route('/financial')
@login_required
@reports_access_required
def financial_reports():
    """Financial reports page"""
    User, FinancialReport, GameReport = get_models()
    League = get_league_model()
    
    # Get filters from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    league_id = request.args.get('league_id', type=int)
    
    # Default date range (last 90 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    report_data = {}
    
    if current_user.role == 'official':
        # Official earnings report
        earnings_data = FinancialReport.get_official_earnings(
            current_user.id, start_date, end_date, league_id
        )
        report_data['earnings_data'] = earnings_data
    
    elif current_user.role in ['administrator', 'superadmin']:
        if league_id:
            # League-specific financial report
            league_financials = FinancialReport.get_league_financials(
                league_id, start_date, end_date
            )
            if League:
                league = League.query.get(league_id)
                report_data.update({
                    'league_financials': league_financials,
                    'selected_league': league
                })
        elif current_user.is_superadmin:
            # Global financial report
            global_financials = FinancialReport.get_global_financials(start_date, end_date)
            report_data['global_financials'] = global_financials
    
    # Get leagues for filter dropdown
    leagues = []
    if League:
        leagues = League.query.filter_by(is_active=True).all()
    
    return render_template('reports/financial.html',
                         leagues=leagues,
                         start_date=start_date,
                         end_date=end_date,
                         league_id=league_id,
                         **report_data)

@report_bp.route('/games')
@login_required
@reports_access_required
def game_reports():
    """Game reports and statistics"""
    User, FinancialReport, GameReport = get_models()
    League = get_league_model()
    
    league_id = request.args.get('league_id', type=int)
    
    report_data = {}
    
    if current_user.role == 'official':
        # Official game history
        game_history = GameReport.get_official_game_history(current_user.id, 50)
        report_data['game_history'] = game_history
    
    elif current_user.role in ['administrator', 'superadmin', 'assigner']:
        if league_id:
            # League-specific game statistics
            league_stats = GameReport.get_league_statistics(league_id)
            workload_distribution = GameReport.get_workload_distribution(league_id)
            if League:
                league = League.query.get(league_id)
                report_data.update({
                    'league_stats': league_stats,
                    'workload_distribution': workload_distribution,
                    'selected_league': league
                })
        else:
            # Summary across all leagues
            if League:
                leagues = League.query.filter_by(is_active=True).all()
                league_summaries = []
                
                for league in leagues:
                    stats = GameReport.get_league_statistics(league.id)
                    league_summaries.append({
                        'league': league,
                        'stats': stats
                    })
                
                report_data['league_summaries'] = league_summaries
    
    # Get leagues for filter dropdown
    leagues = []
    if League:
        leagues = League.query.filter_by(is_active=True).all()
    
    return render_template('reports/games.html',
                         leagues=leagues,
                         league_id=league_id,
                         **report_data)

@report_bp.route('/export/earnings')
@login_required
@reports_access_required
def export_earnings():
    """Export earnings data to CSV"""
    if current_user.role != 'official':
        flash('Access denied.', 'error')
        return redirect(url_for('report.dashboard'))
    
    User, FinancialReport, GameReport = get_models()
    
    # Get date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get earnings data
    earnings_data = FinancialReport.get_official_earnings(
        current_user.id, start_date, end_date
    )
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Time', 'League', 'Game', 'Position', 'Fee'])
    
    # Write data
    for game in earnings_data['games_worked']:
        writer.writerow([
            game['date'].strftime('%Y-%m-%d'),
            game['time'].strftime('%H:%M'),
            game['league'],
            game['game_title'],
            game['position'] or '',
            f"${game['fee']:.2f}"
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['Summary'])
    writer.writerow(['Total Games', earnings_data['games_count']])
    writer.writerow(['Total Earnings', f"${earnings_data['total_earnings']:.2f}"])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=earnings_{current_user.id}_{date.today()}.csv'
    
    return response

@report_bp.route('/export/league/<int:league_id>/financials')
@login_required
@reports_access_required
def export_league_financials(league_id):
    """Export league financial data to CSV"""
    if not current_user.can_manage_users:
        flash('Access denied.', 'error')
        return redirect(url_for('report.dashboard'))
    
    User, FinancialReport, GameReport = get_models()
    League = get_league_model()
    
    if not League:
        flash('League management not available.', 'error')
        return redirect(url_for('report.dashboard'))
    
    league = League.query.get_or_404(league_id)
    
    # Get date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get financial data
    financials = FinancialReport.get_league_financials(league_id, start_date, end_date)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Game', 'Officials Count', 'Fee per Official', 'Total Cost', 'Billing Amount'])
    
    # Write data
    for game in financials['games_summary']:
        writer.writerow([
            game['date'].strftime('%Y-%m-%d'),
            game['game_title'],
            game['officials_count'],
            f"${game['fee_per_official']:.2f}",
            f"${game['total_cost']:.2f}",
            f"${game['billing_amount']:.2f}"
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['Summary'])
    writer.writerow(['Total Games', financials['games_count']])
    writer.writerow(['Total Fees Paid', f"${financials['total_fees_paid']:.2f}"])
    writer.writerow(['Total Billing', f"${financials['total_billing']:.2f}"])
    writer.writerow(['Profit Margin', f"${financials['profit_margin']:.2f}"])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={league.name}_financials_{date.today()}.csv'
    
    return response

# API endpoints for AJAX requests

@report_bp.route('/api/league/<int:league_id>/stats')
@login_required
@reports_access_required
def api_league_stats(league_id):
    """API endpoint for league statistics"""
    stats = GameReport.get_league_statistics(league_id)
    return jsonify(stats)

@report_bp.route('/api/workload/<int:league_id>')
@login_required
@reports_access_required
def api_workload_distribution(league_id):
    """API endpoint for workload distribution"""
    if not current_user.can_manage_users and current_user.role != 'assigner':
        return jsonify({'error': 'Access denied'}), 403
    
    days_back = request.args.get('days', 30, type=int)
    workload = GameReport.get_workload_distribution(league_id, days_back)
    return jsonify(workload)

@report_bp.route('/api/earnings')
@login_required
@reports_access_required
def api_earnings_summary():
    """API endpoint for earnings summary"""
    if current_user.role != 'official':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get last 6 months of data
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    earnings_data = FinancialReport.get_official_earnings(
        current_user.id, start_date, end_date
    )
    
    # Group by month
    monthly_earnings = {}
    for game in earnings_data['games_worked']:
        month_key = game['date'].strftime('%Y-%m')
        if month_key not in monthly_earnings:
            monthly_earnings[month_key] = {'games': 0, 'earnings': 0}
        monthly_earnings[month_key]['games'] += 1
        monthly_earnings[month_key]['earnings'] += game['fee']
    
    return jsonify({
        'monthly_earnings': monthly_earnings,
        'total_earnings': earnings_data['total_earnings'],
        'total_games': earnings_data['games_count']
    })
