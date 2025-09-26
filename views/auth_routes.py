# views/auth_routes.py - Complete Authentication routes
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

class SimpleForm:
    def __init__(self):
        self.email = None
        self.password = None
        self.remember_me = None
        self.errors = {}
        
    def validate_on_submit(self):
        if request.method == 'POST':
            self.email = request.form.get('email', '').strip()
            self.password = request.form.get('password', '')
            self.remember_me = 'remember_me' in request.form
            
            if not self.email:
                self.errors['email'] = ['Email is required']
            if not self.password:
                self.errors['password'] = ['Password is required']
                
            return len(self.errors) == 0
        return False
    
    def hidden_tag(self):
        return ''

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SimpleForm()
    
    if form.validate_on_submit():
        from models.database import User, db
        
        user = User.query.filter_by(email=form.email.lower()).first()
        
        if user and user.check_password(form.password):
            if not user.is_active:
                flash('Account deactivated. Contact administrator.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me)
            
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    flash(f'Goodbye, {current_user.first_name}!', 'info')
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        from models.database import db
        
        # Update basic info
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if new_password:
            if not current_password:
                flash('Current password required to change password.', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            current_user.set_password(new_password)
            flash('Password updated successfully.', 'success')
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)