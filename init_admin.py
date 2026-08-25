#!/usr/bin/env python
"""
CLI Utility to create or reset the administrator user for Nature Unisex Salon.
Usage:
    python init_admin.py
    python init_admin.py --username admin --password MySecurePassword123 --email admin@natureunisexsalon.com
"""
import argparse
import sys
from app import app
from models import db, User

def setup_admin(username, password, email):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(password)
            user.email = email
            user.is_admin = True
            db.session.commit()
            print(f"[OK] Successfully updated password for existing admin: '{username}'")
        else:
            new_user = User(
                username=username,
                email=email,
                is_admin=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            print(f"[OK] Successfully created new admin: '{username}' ({email})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create or reset Admin user.")
    parser.add_argument('--username', default='admin', help="Admin username")
    parser.add_argument('--password', default='Admin@Nature2026', help="Admin password")
    parser.add_argument('--email', default='admin@natureunisexsalon.com', help="Admin email")
    
    args = parser.parse_args()
    setup_admin(args.username, args.password, args.email)
