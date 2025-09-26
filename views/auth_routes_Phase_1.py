# views/auth_routes.py - Authentication routes
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
        return '<input type="hidden" name="csrf_token" value="dummy">'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SimpleForm()
    
    if form.validate_on_submit():
        from models.user import User
        
        user = User.query.filter_by(email=form.email.lower()).first()
        
        if user and user.check_password(form.password):
            if not user.is_active:
                flash('Account deactivated. Contact administrator.', 'error')
                return render_template('auth/login.html', form=form)
            
            user.last_login = datetime.utcnow()
            login_user(user, remember=form.remember_me)
            
            flash(f'Welcome back, {user.first_name}!', 'success')
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