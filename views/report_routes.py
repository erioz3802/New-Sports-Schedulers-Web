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

@report_bp.route('/invoices')
@login_required
@reports_access_required
def invoices():
    """Invoice management page"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.dashboard'))
    
    from models.reports import Invoice
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('reports/invoices.html', invoices=invoices)

@report_bp.route('/create_invoice', methods=['GET', 'POST'])
@login_required
@reports_access_required
def create_invoice():
    """Create new invoice"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.dashboard'))
    
    from models.reports import Invoice, InvoiceItem
    from models.database import db
    
    if request.method == 'POST':
        try:
            league_id = request.form.get('league_id', type=int)
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            # Create invoice with demo data
            invoice = Invoice(
                league_id=league_id,
                billing_recipient=f"League {league_id} Billing",
                invoice_date=date.today(),
                period_start=start_date,
                period_end=end_date,
                created_by=current_user.id
            )
            
            db.session.add(invoice)
            db.session.flush()
            
            # Add demo invoice item
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"Games from {start_date} to {end_date}",
                quantity=5,
                unit_price=75.00
            )
            db.session.add(item)
            
            invoice.calculate_totals()
            db.session.commit()
            
            flash(f'Invoice {invoice.invoice_number} created!', 'success')
            return redirect(url_for('report.view_invoice', invoice_id=invoice.id))
            
        except Exception as e:
            flash(f'Error creating invoice: {e}', 'error')
    
    # Get leagues for form
    League = get_league_model()
    leagues = League.query.filter_by(is_active=True).all() if League else []
    return render_template('reports/create_invoice.html', leagues=leagues)

@report_bp.route('/invoice/<int:invoice_id>')
@login_required
@reports_access_required
def view_invoice(invoice_id):
    """View invoice details"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.dashboard'))
    
    from models.reports import Invoice
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('reports/view_invoice.html', invoice=invoice)

@report_bp.route('/paysheets')
@login_required
@reports_access_required
def paysheets():
    """Paysheet management page"""
    from models.reports import Paysheet
    
    if current_user.role == 'official':
        paysheets = Paysheet.query.filter_by(
            official_id=current_user.id
        ).order_by(Paysheet.created_at.desc()).all()
    else:
        paysheets = Paysheet.query.order_by(Paysheet.created_at.desc()).all()
    
    return render_template('reports/paysheets.html', paysheets=paysheets)

@report_bp.route('/create_paysheet', methods=['GET', 'POST'])
@login_required
@reports_access_required
def create_paysheet():
    """Create new paysheet"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.dashboard'))
    
    from models.reports import Paysheet, GamePayment
    from models.database import User, db
    
    if request.method == 'POST':
        try:
            official_id = request.form.get('official_id', type=int)
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            # Create paysheet
            paysheet = Paysheet(
                official_id=official_id,
                paysheet_date=date.today(),
                period_start=start_date,
                period_end=end_date,
                league_filter='ALL',
                level_filter='ALL',
                created_by=current_user.id
            )
            
            db.session.add(paysheet)
            db.session.flush()
            
            # Add demo game payment
            payment = GamePayment(
                paysheet_id=paysheet.id,
                game_date=start_date + timedelta(days=7),
                game_description="Demo Game - Team A vs Team B",
                league_name="Demo League",
                level="High School",
                position="Referee",
                amount=75.00
            )
            db.session.add(payment)
            
            paysheet.calculate_totals()
            db.session.commit()
            
            flash(f'Paysheet {paysheet.paysheet_number} created!', 'success')
            return redirect(url_for('report.view_paysheet', paysheet_id=paysheet.id))
            
        except Exception as e:
            flash(f'Error creating paysheet: {e}', 'error')
    
    # Get officials for form
    officials = User.query.filter_by(is_active=True).all()
    return render_template('reports/create_paysheet.html', officials=officials)

@report_bp.route('/paysheet/<int:paysheet_id>')
@login_required
@reports_access_required
def view_paysheet(paysheet_id):
    """View paysheet details"""
    from models.reports import Paysheet
    paysheet = Paysheet.query.get_or_404(paysheet_id)
    
    # Check access permissions
    if current_user.role == 'official' and paysheet.official_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('report.paysheets'))
    
    return render_template('reports/view_paysheet.html', paysheet=paysheet)

@report_bp.route('/paysheet/<int:paysheet_id>/add_adjustment', methods=['POST'])
@login_required
@reports_access_required
def add_paysheet_adjustment(paysheet_id):
    """Add an adjustment (addition or deduction) to a paysheet"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.paysheets'))
    
    from models.reports import Paysheet, PaysheetAdjustment
    from models.database import db
    
    paysheet = Paysheet.query.get_or_404(paysheet_id)
    
    try:
        adjustment = PaysheetAdjustment(
            paysheet_id=paysheet_id,
            adjustment_type=request.form.get('adjustment_type'),
            description=request.form.get('description'),
            amount=float(request.form.get('amount', 0)),
            category=request.form.get('category'),
            created_by=current_user.id
        )
        
        db.session.add(adjustment)
        paysheet.calculate_totals()
        db.session.commit()
        
        flash('Adjustment added successfully!', 'success')
        
    except ValueError as e:
        flash(f'Invalid amount: {e}', 'error')
    except Exception as e:
        flash(f'Error adding adjustment: {e}', 'error')
    
    return redirect(url_for('report.view_paysheet', paysheet_id=paysheet_id))

@report_bp.route('/paysheet/<int:paysheet_id>/delete_adjustment/<int:adjustment_id>', methods=['POST'])
@login_required
@reports_access_required  
def delete_paysheet_adjustment(paysheet_id, adjustment_id):
    """Delete an adjustment from a paysheet"""
    if current_user.role not in ['administrator', 'superadmin']:
        flash('Admin access required.', 'error')
        return redirect(url_for('report.paysheets'))
    
    from models.reports import Paysheet, PaysheetAdjustment
    from models.database import db
    
    paysheet = Paysheet.query.get_or_404(paysheet_id)
    adjustment = PaysheetAdjustment.query.get_or_404(adjustment_id)
    
    # Verify the adjustment belongs to this paysheet
    if adjustment.paysheet_id != paysheet_id:
        flash('Invalid adjustment.', 'error')
        return redirect(url_for('report.view_paysheet', paysheet_id=paysheet_id))
    
    try:
        db.session.delete(adjustment)
        paysheet.calculate_totals()
        db.session.commit()
        
        flash('Adjustment deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting adjustment: {e}', 'error')
    
    return redirect(url_for('report.view_paysheet', paysheet_id=paysheet_id))