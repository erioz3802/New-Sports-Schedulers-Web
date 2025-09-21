#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python -c "
from app import app, db
from models.database import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    print('Database tables created successfully')
    
    # Check if admin exists
    admin = User.query.filter_by(email='admin@sportsscheduler.com').first()
    if not admin:
        # Create admin user
        admin = User(
            email='admin@sportsscheduler.com',
            first_name='Admin',
            last_name='User',
            role='superadmin',
            password_hash=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
"

echo "Build completed successfully!"
