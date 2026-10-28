#!/usr/bin/env python
"""
Migration Utility: SQLite to PostgreSQL for Nature Unisex Salon
Safely copies all existing records from local SQLite (instance/salon.db)
to a target PostgreSQL database (e.g. on Render) without data loss.

Preserves:
- Users & admin passwords
- Services catalog & rates
- Gallery portfolios
- Customer reviews & ratings
- Contact inquiries
- Website settings & branding
- Customer appointments & booking history

Usage:
    python migrate_sqlite_to_postgres.py --target-url "postgresql://user:pass@host/dbname"
    # Or uses TARGET_DATABASE_URL or DATABASE_URL from .env
"""
import sys
import os
import argparse
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

basedir = Path(__file__).resolve().parent
sys.path.insert(0, str(basedir))

from config import normalize_db_url
from models import User, Service, Gallery, Review, ContactEnquiry, WebsiteSetting, Appointment

MODELS = [
    User,
    WebsiteSetting,
    Service,
    Gallery,
    Review,
    ContactEnquiry,
    Appointment
]

def inspect_source_database(sqlite_path):
    """Inspect and report records in source SQLite database."""
    if not sqlite_path.exists():
        print(f"[ERROR] Source SQLite database not found at: {sqlite_path}")
        return False
    print(f"[*] Inspecting source database: {sqlite_path}")
    src_engine = create_engine(f"sqlite:///{sqlite_path}")
    SrcSession = sessionmaker(bind=src_engine)
    session = SrcSession()
    try:
        total = 0
        for model in MODELS:
            cnt = session.query(model).count()
            print(f"  - {model.__tablename__}: {cnt} records")
            total += cnt
        print(f"[OK] Total records available for migration: {total}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to read source SQLite: {e}")
        return False
    finally:
        session.close()

def run_migration(sqlite_path, pg_url, dry_run=False):
    if not sqlite_path.exists():
        print(f"[ERROR] Source SQLite database not found at: {sqlite_path}")
        return False

    pg_url = normalize_db_url(pg_url)
    if 'sqlite' in pg_url:
        print("[ERROR] Target URL must be a PostgreSQL connection string, not SQLite.")
        return False

    print(f"[*] Source SQLite: {sqlite_path}")
    print(f"[*] Target PostgreSQL: {pg_url.split('@')[-1] if '@' in pg_url else 'configured database'}")

    src_engine = create_engine(f"sqlite:///{sqlite_path}")
    try:
        dst_engine = create_engine(pg_url, pool_pre_ping=True)
    except Exception as e:
        if 'psycopg2' in str(e) or 'ModuleNotFoundError' in str(type(e).__name__):
            print("[NOTICE] PostgreSQL driver 'psycopg2' is not installed in the local Python environment.")
            print("         Run 'pip install psycopg2-binary' to enable direct database migration.")
            return False
        print(f"[FATAL] Failed to configure database engine: {e}")
        return False

    # Test destination connection
    try:
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("[OK] Successfully connected to PostgreSQL target.")
    except Exception as e:
        print(f"[FATAL] Could not connect to PostgreSQL target: {e}")
        return False

    # Create tables in target if not present using direct metadata binding
    from models import db
    db.metadata.create_all(bind=dst_engine)
    print("[OK] Target database tables verified/created.")

    SrcSession = sessionmaker(bind=src_engine)
    DstSession = sessionmaker(bind=dst_engine)

    src_session = SrcSession()
    dst_session = DstSession()

    try:
        total_migrated = 0
        for model in MODELS:
            table_name = model.__tablename__
            records = src_session.query(model).all()
            print(f"[*] Table '{table_name}': {len(records)} records in source SQLite.")

            if dry_run:
                continue

            migrated_table_count = 0
            for r in records:
                # Check if record with same ID already exists in target
                existing = dst_session.get(model, r.id)
                if not existing:
                    # Detach from source session and merge into destination
                    src_session.expunge(r)
                    dst_session.merge(r)
                    migrated_table_count += 1

            dst_session.commit()
            print(f"    -> Merged {migrated_table_count} new records into '{table_name}'.")
            total_migrated += migrated_table_count

            # Reset PostgreSQL serial sequences
            try:
                with dst_engine.connect() as conn:
                    seq_query = text(f"SELECT pg_get_serial_sequence('{table_name}', 'id');")
                    seq_result = conn.execute(seq_query).scalar()
                    if seq_result:
                        conn.execute(text(f"SELECT setval('{seq_result}', COALESCE((SELECT MAX(id) FROM {table_name}), 1));"))
                        conn.commit()
            except Exception as seq_err:
                # Some tables might not use sequences
                pass

        if dry_run:
            print("[DRY RUN] Verification finished. No changes written.")
        else:
            print(f"[SUCCESS] Migration complete! Total records transferred: {total_migrated}")
        return True

    except Exception as e:
        dst_session.rollback()
        print(f"[FATAL] Migration error: {e}", file=sys.stderr)
        return False
    finally:
        src_session.close()
        dst_session.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL.")
    parser.add_argument('--sqlite-path', default=str(basedir / 'instance' / 'salon.db'), help="Path to SQLite database file")
    parser.add_argument('--target-url', '--dest', dest='target_url', default=os.environ.get('TARGET_DATABASE_URL') or os.environ.get('DATABASE_URL'), help="PostgreSQL connection string")
    parser.add_argument('--dry-run', action='store_true', help="Inspect record counts without writing to target")

    parser.add_argument('--inspect', action='store_true', help="Inspect and count records in SQLite source database")
    args = parser.parse_args()

    if args.inspect:
        inspect_source_database(Path(args.sqlite_path))
        sys.exit(0)

    if not args.target_url:
        print("[ERROR] Please provide --target-url or set TARGET_DATABASE_URL/DATABASE_URL environment variable.")
        sys.exit(1)

    success = run_migration(Path(args.sqlite_path), args.target_url, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
