#!/usr/bin/env python3
"""
Safe migration: adds page_texts column to documents table if it doesn't exist.
Run once against existing databases after upgrading to this version.
Usage:
    cd Alethian/backend
    python migrate_add_page_texts.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text, inspect
from app.db.session import engine

def run():
    with engine.connect() as conn:
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('documents')]
        if 'page_texts' not in cols:
            conn.execute(text("ALTER TABLE documents ADD COLUMN page_texts JSONB"))
            conn.commit()
            print("✅  Added page_texts column to documents table.")
        else:
            print("ℹ️   page_texts column already exists — nothing to do.")

if __name__ == '__main__':
    run()
