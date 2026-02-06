"""
Database Sync Script
Compares SQLAlchemy models against the actual database schema
and adds any missing columns/tables automatically.

Usage:
    python sync_db.py          # Dry run - shows what's missing
    python sync_db.py --apply  # Apply changes to the database
"""

import sys
from sqlalchemy import inspect, text
from app import app
from database import db
from models import User, Pandit, PujaMaterial, Testimonial, Bundle, Admin, Booking, Order, OrderItem, OTP

# Map SQLAlchemy types to PostgreSQL types
TYPE_MAP = {
    'VARCHAR': 'VARCHAR',
    'String': 'VARCHAR',
    'TEXT': 'TEXT',
    'Text': 'TEXT',
    'INTEGER': 'INTEGER',
    'Integer': 'INTEGER',
    'FLOAT': 'FLOAT',
    'Float': 'DOUBLE PRECISION',
    'BOOLEAN': 'BOOLEAN',
    'Boolean': 'BOOLEAN',
    'DATETIME': 'TIMESTAMP',
    'DateTime': 'TIMESTAMP WITHOUT TIME ZONE',
    'DATE': 'DATE',
    'Date': 'DATE',
}


def get_pg_type(column):
    """Convert SQLAlchemy column type to PostgreSQL type string."""
    col_type = type(column.type).__name__
    if col_type in ('String', 'VARCHAR'):
        length = getattr(column.type, 'length', None)
        if length:
            return f'VARCHAR({length})'
        return 'VARCHAR(255)'
    return TYPE_MAP.get(col_type, 'TEXT')


def get_default_clause(column):
    """Get DEFAULT clause for a column if applicable."""
    if column.default is not None:
        default_val = column.default.arg if hasattr(column.default, 'arg') else column.default
        if callable(default_val):
            return ''
        if isinstance(default_val, bool):
            return f" DEFAULT {'TRUE' if default_val else 'FALSE'}"
        if isinstance(default_val, (int, float)):
            return f' DEFAULT {default_val}'
        if isinstance(default_val, str):
            return f" DEFAULT '{default_val}'"
    if column.server_default is not None:
        return f' DEFAULT {column.server_default.arg}'
    return ''


def sync_database(apply=False):
    """Compare models to database and report/fix mismatches."""
    models = [User, Pandit, PujaMaterial, Testimonial, Bundle, Admin, Booking, Order, OrderItem, OTP]

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names(schema='public')

        changes = []

        for model in models:
            table_name = model.__tablename__

            # Check if table exists
            if table_name not in existing_tables:
                changes.append({
                    'type': 'missing_table',
                    'table': table_name,
                    'sql': None  # Will use db.create_all() for missing tables
                })
                print(f'  MISSING TABLE: {table_name}')
                continue

            # Get existing columns from database
            db_columns = {col['name']: col for col in inspector.get_columns(table_name, schema='public')}

            # Get model columns
            model_columns = {col.name: col for col in model.__table__.columns}

            print(f'\n[{table_name}]')

            # Find missing columns
            missing = set(model_columns.keys()) - set(db_columns.keys())
            if not missing:
                print('  OK - all columns in sync')

            for col_name in missing:
                col = model_columns[col_name]
                pg_type = get_pg_type(col)
                default = get_default_clause(col)
                nullable = '' if col.nullable else ' NOT NULL'

                # For adding columns, skip NOT NULL if no default (would fail on existing rows)
                if nullable and not default:
                    nullable = ''

                sql = f'ALTER TABLE public.{table_name} ADD COLUMN {col_name} {pg_type}{default}{nullable};'
                changes.append({
                    'type': 'missing_column',
                    'table': table_name,
                    'column': col_name,
                    'sql': sql
                })
                print(f'  MISSING COLUMN: {col_name} ({pg_type}{default})')

        if not changes:
            print('\nDatabase is fully in sync with models!')
            return

        print(f'\n--- Found {len(changes)} change(s) needed ---\n')

        if not apply:
            print('Run with --apply to execute these changes:')
            for c in changes:
                if c['sql']:
                    print(f'  {c["sql"]}')
                else:
                    print(f'  CREATE TABLE {c["table"]} (via db.create_all())')
            return

        # Apply changes
        print('Applying changes...\n')

        # First, create any missing tables
        missing_tables = [c for c in changes if c['type'] == 'missing_table']
        if missing_tables:
            print('Creating missing tables...')
            db.create_all()
            print('  Done.\n')

        # Then, add missing columns
        missing_columns = [c for c in changes if c['type'] == 'missing_column']
        for c in missing_columns:
            try:
                db.session.execute(text(c['sql']))
                db.session.commit()
                print(f'  ADDED: {c["table"]}.{c["column"]}')
            except Exception as e:
                db.session.rollback()
                error_msg = str(e)
                if 'already exists' in error_msg:
                    print(f'  SKIPPED (already exists): {c["table"]}.{c["column"]}')
                else:
                    print(f'  FAILED: {c["table"]}.{c["column"]} - {error_msg}')

        print('\nSync complete!')


if __name__ == '__main__':
    apply = '--apply' in sys.argv
    if apply:
        print('=== DATABASE SYNC (APPLYING CHANGES) ===\n')
    else:
        print('=== DATABASE SYNC (DRY RUN) ===\n')
    sync_database(apply=apply)
