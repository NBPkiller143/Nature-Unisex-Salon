#!/usr/bin/env python
"""
Standalone idempotent database initialization and migration script for Nature Unisex Salon.
Executes schema creations, upgrades, and initial seed data in a controlled single process
before multi-worker Gunicorn processes start.
Usage:
    python init_db.py
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure workspace root is in path
basedir = Path(__file__).resolve().parent
sys.path.insert(0, str(basedir))
load_dotenv(basedir / '.env')

from app import app, init_db

if __name__ == '__main__':
    print("[*] Nature Unisex Salon: Starting database verification and migration...")
    try:
        init_db(app)
        print("[SUCCESS] Database initialization completed safely.")
    except Exception as e:
        print(f"[FATAL] Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

