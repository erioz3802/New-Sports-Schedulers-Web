#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

echo "Build completed successfully!"